from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect
from django.urls import path
from . import views
from .views import ExpenseAnalysisView

# app_name = 'finance'

urlpatterns = [
    path('transactions/', views.transaction_list, name='transaction'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/edit/', views.transaction_edit, name='transaction_edit'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
    path('transactions/import/', views.transaction_import, name='transaction_import'),
    path('ajax/get_categories/', views.get_categories_by_type, name='get_categories_by_type'),
    path('analytics/', ExpenseAnalysisView.as_view(), name='analytics'),
    path('goals/add/', views.add_goal_view, name='add_goal'),
    # path('recommendations/', views.recommendations_view, name='recommendations'),
    path('recommendations/', views.expense_analysis, name='recommendations'),
]