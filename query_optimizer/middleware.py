
from django.conf import settings
from django.db import connection
from query_optimizer.models import QueryRecord
import time
import traceback
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class QueryCaptureMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.config = getattr(settings, 'QUERY_OPTIMIZER_CONFIG', None)
        if not self.config:
            raise ValueError("QUERY_OPTIMIZER_CONFIG is not set in settings.py")

        self.watched_models = self.config.get('watched_models', [])
        self.excluded_paths = self.config.get('excluded_paths', []) + ['/admin/', '/static/', '/media/']
        self.slow_query_threshold = self.config.get('slow_query_threshold', 0.5)
        self.check_config()
    
    def check_config(self):
        if self.watched_models and not isinstance(self.watched_models, list):
            raise ValueError("watched_models must be a list")
        
        if self.excluded_paths and not isinstance(self.excluded_paths, list):
            raise ValueError("excluded_paths must be a list")
        
        if self.slow_query_threshold and not any([isinstance(self.slow_query_threshold, float), isinstance(self.slow_query_threshold, int)]):
            raise ValueError("slow_query_threshold must be a float or int")

    def should_capture(self, request):
        """Determine if we should capture queries for this request"""
        # Skip excluded paths
        path = urlparse(request.path).path
        return not any(path.startswith(excluded) for excluded in self.excluded_paths)
            
        # Check if it's an API request
        # if hasattr(request, 'accepted_renderer'):
        #     return True

    def get_view_name(self, request):
        """Extract view name from request"""
        resolver_match = getattr(request, 'resolver_match', None)
        if not resolver_match:
            return ''
            
        # For DRF views
        if hasattr(resolver_match, 'func') and hasattr(resolver_match.func, '__name__'):
            return resolver_match.func.__name__
            
        # For Django views
        return resolver_match.view_name if resolver_match.view_name else resolver_match.url_name

    def is_watched_model_query(self, query):
        """Check if query involves watched models"""
        if not self.watched_models:
            return True
            
        sql_lower = query['sql'].lower()
        return any(model.lower() in sql_lower for model in self.watched_models)

    def __call__(self, request):
        if not self.should_capture(request):
            return self.get_response(request)

        # Reset query tracking at the start of the request
        request._query_start_time = time.time()
        initial_query_count = len(connection.queries)
        
        response = self.get_response(request)
        
        # Process captured queries
        view_name = self.get_view_name(request)
        
        for query in connection.queries[initial_query_count:]:
            if not self.is_watched_model_query(query):
                continue
                
            try:
                duration = float(query['time'])
                is_slow = duration > self.slow_query_threshold
                
                QueryRecord.objects.create(
                    query=query['sql'],
                    duration=duration,
                    is_slow=is_slow,
                    view_name=view_name,
                    url_path=request.path,
                    stack_trace='\n'.join(traceback.format_stack()[:-2]),
                    query_params=dict(request.GET),
                    request_method=request.method,
                    request_content_type=request.content_type,
                    response_status_code=response.status_code if hasattr(response, 'status_code') else 200,
                )
                
                if is_slow:
                    logger.warning(
                        f"Slow query ({duration:.3f}s) in {view_name}: "
                        f"{query['sql'][:100]}..."
                    )
                    
            except Exception as e:
                logger.error(f"Failed to capture query: {str(e)}", exc_info=True)
                continue
                
        # Log request summary
        total_time = time.time() - request._query_start_time
        query_count = len(connection.queries) - initial_query_count
        logger.debug(
            f"Request {request.method} {request.path} - "
            f"{query_count} queries in {total_time:.3f}s"
        )
        
        return response