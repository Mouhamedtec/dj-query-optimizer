from django.db import connection
from django.conf import settings

from query_optimizer.models import QueryRecord

from functools import wraps
import time
import traceback
import logging

logger = logging.getLogger(__name__)

def track_queries(view_func=None, enabled=True, threshold=0.5, capture_stack=True, capture_params=True):
    """
    Universal decorator that tracks queries with additional request/response context.
    Works with:
    - Django function views
    - Django class views (when used with @method_decorator)
    - DRF APIViews and ViewSets
    """
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            # Skip if not enabled
            if not enabled:
                return func(*args, **kwargs)

            # Determine the request object and view name
            request = None
            view_name = ''
            
            # Case 1: DRF class-based view (first arg is 'self')
            if len(args) > 0 and hasattr(args[0], 'request'):
                self = args[0]
                request = self.request
                view_name = self.__class__.__name__
            # Case 2: Django class-based view (when using @method_decorator)
            elif len(args) > 0 and hasattr(args[0], 'request'):
                self = args[0]
                request = args[1]  # For Django class views, request is second arg
                view_name = self.__class__.__name__
            # Case 3: Regular function view (first arg is request)
            else:
                request = args[0]
                resolver_match = getattr(request, 'resolver_match', None)
                view_name = resolver_match.view_name if resolver_match else ''

            if not request:
                return func(*args, **kwargs)

            # Start tracking
            start_time = time.time()
            initial_queries = len(connection.queries)
            
            #Execute the view
            response = func(*args, **kwargs)
            
            # Get response status code
            status_code = getattr(response, 'status_code', 200)
            
            # Get request content type
            content_type = request.content_type if hasattr(request, 'content_type') else ''
            
            # Capture queries
            for query in connection.queries[initial_queries:]:
                try:
                    duration = float(query['time'])
                    is_slow = duration > threshold
                    
                    QueryRecord.objects.create(
                        query=query['sql'],
                        duration=duration,
                        is_slow=is_slow,
                        view_name=view_name,
                        url_path=request.path,
                        stack_trace='\n'.join(traceback.format_stack()[:-2]) if capture_stack else "",
                        query_params=dict(request.GET) if capture_params else {},
                        request_method=request.method,
                        request_content_type=content_type,
                        response_status_code=status_code,
                    )
                    
                    if is_slow:
                        logger.warning(
                            f"Slow query ({duration:.3f}s) in {view_name} - "
                            f"Status: {status_code}, Content-Type: {content_type}\n"
                            f"Query: {query['sql'][:100]}..."
                        )
                        
                except Exception as e:
                    logger.error(f"Failed to capture query: {str(e)}", exc_info=True)
                    continue

            return response

        return wrapped

    # Handle both @track_queries and @track_queries(threshold=0.7) cases
    if view_func:
        return decorator(view_func)
    return decorator