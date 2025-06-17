from django.contrib import admin
from .models import QueryRecord, QueryAnalysis

@admin.register(QueryRecord)
class QueryRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'duration', 'is_slow', 'view_name', 'url_path', 'timestamp')
    list_filter = ('is_slow', 'timestamp', 'request_method')
    search_fields = ('query', 'view_name', 'url_path')
    readonly_fields = ('timestamp', 'query', 'duration', 'stack_trace', 'query_params')
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        (None, {
            'fields': ('timestamp', 'duration', 'is_slow')
        }),
        ('Request Info', {
            'fields': ('view_name', 'url_path', 'request_method', 'query_params')
        }),
        ('Query Details', {
            'fields': ('query', 'stack_trace')
        }),
    )
    
    def has_add_permission(self, request):
        return False

@admin.register(QueryAnalysis)
class QueryAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'query_record', 'applied', 'created_at')
    list_filter = ('applied', 'created_at')
    readonly_fields = ('created_at', 'query_record', 'analysis', 'suggested_optimization')
    raw_id_fields = ('query_record',)
    
    actions = ['mark_as_applied']
    
    def mark_as_applied(self, request, queryset):
        queryset.update(applied=True)
    mark_as_applied.short_description = "Mark selected analyses as applied"