from django.urls import path
from . import views

app_name = 'query_optimizer'

urlpatterns = [
    path('', views.QueryListView.as_view(), name='query_list'),
    path('query/<int:pk>/', views.QueryDetailView.as_view(), name='query_detail'),
    path('query_analyze/', views.query_analyze_view, name='query_analyze'),
    path('analysis/', views.AnalysisListView.as_view(), name='analysis_list'),
    path('analysis/<int:pk>/', views.AnalysisDetailView.as_view(), name='analysis_detail'),
]