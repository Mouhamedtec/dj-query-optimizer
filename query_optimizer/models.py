from django.db import models
from django.urls import reverse

class QueryRecord(models.Model):
    query = models.TextField()  # The actual SQL query
    duration = models.FloatField()  # Execution time in seconds
    timestamp = models.DateTimeField(auto_now_add=True)
    is_slow = models.BooleanField(default=False)
    
    # Add these more useful fields instead
    view_name = models.CharField(max_length=255, blank=True)
    url_path = models.CharField(max_length=255, blank=True)
    stack_trace = models.TextField(blank=True)
    query_params = models.JSONField(default=dict, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_content_type = models.CharField(
        max_length=100, 
        blank=True,
        help_text="Content-Type header of the request"
    )
    response_status_code = models.PositiveSmallIntegerField(
        null=True,
        help_text="HTTP status code of the response"
    )

    class Meta:
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['is_slow']),
            models.Index(fields=['duration']),
            models.Index(fields=['view_name']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"Query at {self.timestamp} ({self.duration}s)"

    def get_absolute_url(self):
        return reverse('query_optimizer:query_detail', args=[str(self.id)])


    @property
    def formatted_duration(self):
        return f"{self.duration:.3f}s"
    
    @property
    def short_query(self):
        return self.query[:100] + ('...' if len(self.query) > 100 else '')
    
    @classmethod
    def get_slow_queries(cls, threshold=0.5):
        return cls.objects.filter(duration__gt=threshold).order_by('-duration')
    
    @classmethod
    def get_queries_by_view(cls, view_name):
        return cls.objects.filter(view_name=view_name).order_by('-duration')