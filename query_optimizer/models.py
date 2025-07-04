from django.db import models
from django.urls import reverse

class QueryRecord(models.Model):
    query = models.TextField()  # The actual SQL query
    duration = models.FloatField()  # Execution time in seconds
    timestamp = models.DateTimeField(auto_now_add=True)
    is_slow = models.BooleanField(default=False)

    view_name = models.CharField(max_length=255, blank=True, null=True)
    url_path = models.CharField(max_length=255, blank=True, null=True)
    stack_trace = models.TextField(blank=True)
    query_params = models.JSONField(default=dict, blank=True)
    request_method = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )
    request_content_type = models.CharField(
        max_length=100, 
        blank=True,
        null=True,
        help_text="Content-Type header of the request"
    )
    response_status_code = models.PositiveSmallIntegerField(
        null=True,
        help_text="HTTP status code of the response"
    )

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Query Record"
        verbose_name_plural = "Query Records"
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['is_slow']),
            models.Index(fields=['duration']),
            models.Index(fields=['view_name']),
            models.Index(fields=['is_slow', '-duration']),
            models.Index(fields=['view_name', '-timestamp']),
        ]

    def __str__(self):
        return f"Query at {self.timestamp} ({self.duration:.3f}s)"

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


class QueryAnalysis(models.Model):
    query_record = models.OneToOneField(
        QueryRecord,
        on_delete=models.CASCADE,
        related_name='analysis'
    )
    analysis = models.JSONField()
    suggested_optimization = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    applied = models.BooleanField(default=False)
    applied_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Query Analysis"
        verbose_name_plural = "Query Analyses"
        ordering = ['-created_at']

    def __str__(self):
        return f"Analysis for {self.query_record}"