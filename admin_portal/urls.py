from django.urls import path
from . import views


urlpatterns = [
    path('', views.admin_dashboard_view, name='admin_dashboard'),
    path('users/', views.user_management_view, name='user_management'),
    path('accounts/', views.account_management_view, name='account_management'),
    path('loans/', views.loan_management_view, name='loan_management'),
    path('loans/<uuid:loan_id>/approve/', views.loan_approval_view, name='loan_approval'),
    path('audit-logs/', views.audit_log_view, name='audit_logs'),
    path('settings/', views.system_settings_view, name='system_settings'),
    path('users/<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('users/<int:user_id>/edit/', views.user_edit_view, name='user_edit'),
    path('accounts/<int:account_id>/', views.account_detail_view, name='account_detail'),
    path('accounts/<int:account_id>/edit/', views.account_edit_view, name='admin_account_edit'),
     path('transactions/pending/', views.pending_transactions_view, name='pending_transactions'),
    path('transactions/<uuid:transaction_id>/approve/', views.admin_approve_transaction, name='admin_approve_transaction'),
    path('transactions/<uuid:transaction_id>/reject/', views.admin_reject_transaction, name='admin_reject_transaction'),
]