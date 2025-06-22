[![Published on Django Packages](https://img.shields.io/badge/Published%20on-Django%20Packages-0c3c26)](https://djangopackages.org/packages/p/dj-query-optimizer/)

# Query Optimizer AI

A Django application that automatically captures, analyzes, and optimizes SQL queries using AI-powered suggestions. This tool helps developers identify slow queries and provides intelligent optimization recommendations.

## Features

- **Automatic Query Capture**: Middleware automatically captures SQL queries during request processing
- **AI-Powered Analysis**: Uses AI providers (Mistral, OpenAI, Anthropic) to analyze query performance
- **Smart Filtering**: Filter queries by date range, speed, analysis status, view name, and duration
- **Optimization Suggestions**: Get detailed recommendations for query optimization, index suggestions, and Django ORM improvements
- **Beautiful Dashboard**: Modern, responsive UI with dark mode support
- **Configurable Monitoring**: Set thresholds for slow queries and specify which models to watch
- **Pagination**: Efficient pagination with filter preservation


## Installation

### Prerequisites

- Python 3.8+
- Django 3.2+
- Database (SQLite, PostgreSQL, MySQL)

### 1. Install the App

clone the repository:

```bash
git clone <repository-url>
cd query-optimizer
pip install -r requirements.txt
```

### 2. Add to Django Settings

Add `query_optimizer` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... other apps
    'query_optimizer',
]
```

### 3. Configure AI Provider

Add the `QUERY_OPTIMIZER_CONFIG` to your Django settings:

```python
QUERY_OPTIMIZER_CONFIG = {
    "model": "mistral-large-latest",  # or "gpt-4", "claude-3-sonnet"
    "api_key": "your-api-key-here",
    "provider": "mistral",  # "mistral", "openai", or "anthropic"
    "watched_models": ['your_app_model'],  # Models to monitor
    "excluded_paths": ['/admin/', '/static/', '/media/'],  # Paths to exclude
    "slow_threshold": 0.5  # Seconds threshold for slow queries
}
```

### 4. Add Middleware

Add the query capture middleware to your `MIDDLEWARE`:

```python
MIDDLEWARE = [
    # ... other middleware
    'query_optimizer.middleware.QueryCaptureMiddleware',
]
```

### 5. Include URLs

Add the query optimizer URLs to your main `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... other URLs
    path('query-optimizer/', include('query_optimizer.urls')),
]
```

### 6. Run Migrations

```bash
python manage.py migrate
```

## Usage

### 1. Access the Dashboard

Navigate to `/query-optimizer/` to access the main dashboard.

### 2. View Captured Queries

The dashboard shows:
- Total queries captured
- Slow queries count
- Analyzed queries count
- Filterable query list

### 3. Filter Queries

Use the filter panel to:
- Filter by date range
- Filter by query speed (slow/fast)
- Filter by analysis status
- Filter by view name
- Filter by duration range
- Sort by various criteria

### 4. Analyze Queries

1. Click on a query to view details
2. Click "Analyze Query" to get AI-powered optimization suggestions
3. View the analysis results with:
   - Performance analysis
   - Optimization suggestions
   - Optimized query (if applicable)
   - Index suggestions
   - Django ORM improvements

### 5. View Analysis History

Navigate to the "Analysis History" tab to view all previous analyses.

## Decorators

Use the `@track_queries` decorator to manually track queries in specific views:

```python
from query_optimizer.decorators import track_queries

@track_queries
def my_view(request):
    # Your view logic here
    pass

# With custom settings
@track_queries(threshold=1.0, capture_stack=True)
def slow_view(request):
    # Your view logic here
    pass
```

## Troubleshooting

### Common Issues

1. **No queries being captured**
   - Check if middleware is properly configured
   - Verify excluded paths don't match your URLs
   - Check database permissions

2. **AI analysis failing**
   - Verify API key is correct
   - Check API provider configuration
   - Ensure model name is valid

3. **Performance impact**
   - Adjust `slow_threshold` to capture fewer queries
   - Use `watched_models` to limit monitoring
   - Consider excluding more paths


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting section

## Changelog

### v1.0.0
- Initial release
- Query capture middleware
- AI-powered analysis
- Web dashboard
- Filtering and pagination
- Support for multiple AI providers 