from django.conf import settings

def is_excluded_path(request_path):
    excluded_paths = getattr(settings,
    'QUERY_OPTIMIZER_EXCLUDED_PATHS',
        [
            '/admin/',
            '/static/',
            '/media/'
        ])
    return any(request_path.startswith(excluded) for excluded in excluded_paths)