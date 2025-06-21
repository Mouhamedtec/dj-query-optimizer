from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.contrib import messages
from .models import QueryRecord, QueryAnalysis
from .services import QueryOptimizerAI
from datetime import datetime, timedelta


class QueryListView(ListView):
    template_name = 'query_optimizer/query_list.html'
    model = QueryRecord
    paginate_by = 15
    context_object_name = 'queries'
    
    def get_queryset(self):
        queryset = QueryRecord.objects.select_related('analysis').order_by('-timestamp')
        
        # Apply filters
        filters = {}
        
        # Date range filter
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d')
                filters['timestamp__date__gte'] = date_from
            except (ValueError, TypeError):
                pass
                
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d')
                filters['timestamp__date__lte'] = date_to
            except (ValueError, TypeError):
                pass
        
        # Slowness filter
        slowness = self.request.GET.get('slowness')
        if slowness == 'slow':
            filters['is_slow'] = True
        elif slowness == 'fast':
            filters['is_slow'] = False
            
        # Analysis status filter
        analysis_status = self.request.GET.get('analysis_status')
        if analysis_status == 'analyzed':
            filters['analysis__isnull'] = False
        elif analysis_status == 'unanalyzed':
            filters['analysis__isnull'] = True
            
        # View name filter
        view_name = self.request.GET.get('view_name')
        if view_name:
            filters['view_name__icontains'] = view_name
            
        # Duration range filter
        min_duration = self.request.GET.get('min_duration')
        max_duration = self.request.GET.get('max_duration')
        
        if min_duration:
            try:
                filters['duration__gte'] = float(min_duration)
            except ValueError:
                pass
                
        if max_duration:
            try:
                filters['duration__lte'] = float(max_duration)
            except ValueError:
                pass
        
        # Apply all filters
        if filters:
            queryset = queryset.filter(**filters)
            
        # Sort by
        sort_by = self.request.GET.get('sort_by', '-timestamp')
        valid_sort_fields = {
            'timestamp': 'timestamp',
            '-timestamp': '-timestamp',
            'duration': 'duration',
            '-duration': '-duration',
            'view_name': 'view_name',
            '-view_name': '-view_name'
        }
        if sort_by in valid_sort_fields:
            queryset = queryset.order_by(valid_sort_fields[sort_by])
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter values to context
        context.update({
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'slowness': self.request.GET.get('slowness', ''),
            'analysis_status': self.request.GET.get('analysis_status', ''),
            'view_name': self.request.GET.get('view_name', ''),
            'min_duration': self.request.GET.get('min_duration', ''),
            'max_duration': self.request.GET.get('max_duration', ''),
            'sort_by': self.request.GET.get('sort_by', '-timestamp'),
            
            # Add statistics
            'total_count': self.get_queryset().count(),
            'slow_count': self.get_queryset().filter(is_slow=True).count(),
            'analyzed_count': self.get_queryset().filter(analysis__isnull=False).count(),
            
            # Add unique view names for filter dropdown
            'view_names': QueryRecord.objects.values_list('view_name', flat=True)
                .distinct().order_by('view_name'),
                
            # Add sort options
            'sort_options': [
                {'value': '-timestamp', 'label': 'Newest First'},
                {'value': 'timestamp', 'label': 'Oldest First'},
                {'value': '-duration', 'label': 'Slowest First'},
                {'value': 'duration', 'label': 'Fastest First'},
                {'value': 'view_name', 'label': 'View Name (A-Z)'},
                {'value': '-view_name', 'label': 'View Name (Z-A)'}
            ]
        })
        
        return context


class QueryDetailView(DetailView):
    template_name = 'query_optimizer/query_detail.html'
    model = QueryRecord
    context_object_name = 'selected_query'


def query_analyze_view(request):
    if request.method != 'POST':
        return redirect('query_optimizer:query_list')

    query_id = request.POST.get('query_id')
    if not query_id:
        messages.error(request, 'No query selected for analysis.')
        return redirect('query_optimizer:query_list')

    try:
        query_record = QueryRecord.objects.get(id=query_id)
    except QueryRecord.DoesNotExist:
        messages.error(request, 'Query not found.')
        return redirect('query_optimizer:query_list')

    # Check if already analyzed
    if hasattr(query_record, 'analysis'):
        messages.info(request, 'This query has already been analyzed.')
        return redirect('query_optimizer:query_detail', pk=query_record.id)

    # Run analysis
    optimizer = QueryOptimizerAI()
    analysis = optimizer.analyze_query(query_record)
    if not analysis:
        messages.error(request, 'Failed to analyze the query. Please try again later.')
        return redirect('query_optimizer:query_detail', pk=query_record.id)

    QueryAnalysis.objects.create(
        query_record=query_record,
        analysis=analysis,
        suggested_optimization=analysis.get('optimization_suggestions', '')
    )
    messages.success(request, 'Query analyzed successfully!')
    return redirect('query_optimizer:query_detail', pk=query_record.id)


class AnalysisListView(ListView):
    template_name = 'query_optimizer/analysis_list.html'
    model = QueryAnalysis
    paginate_by = 10
    context_object_name = 'analysis_list'
    
    def get_queryset(self):
        queryset = QueryAnalysis.objects.order_by('-created_at')
        
        # Apply filters
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d')
                queryset = queryset.filter(created_at__date__gte=date_from)
            except (ValueError, TypeError):
                pass
                
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d')
                queryset = queryset.filter(created_at__date__lte=date_to)
            except (ValueError, TypeError):
                pass

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter values to context
        context.update({
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
        })
        
        return context


class AnalysisDetailView(DetailView):
    template_name = 'query_optimizer/analysis_detail.html'
    model = QueryAnalysis
    context_object_name = 'analysis'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_record = self.object.query_record

        query_context = {
            'query_preview': query_record.short_query,
            'formatted_duration': query_record.formatted_duration,
            'is_slow': query_record.is_slow,
            'created_at': self.object.created_at,
            'applied': self.object.applied,
            'applied_at': self.object.applied_at,
            'analysis_data': {
                'analysis': self.object.analysis.get('analysis', ''),
                'optimization_suggestions': self.object.suggested_optimization,
                'optimized_query': self.object.analysis.get('optimized_query', ''),
                'index_suggestions': self.object.analysis.get('index_suggestions', ''),
                'django_orm_improvements': self.object.analysis.get('django_orm_improvements', '')
            }
        }

        context.update(query_context)
        
        return context
