from django.urls import path
from . import views

urlpatterns = [
    # Transaction history
    path('history/', views.transaction_history_view, name='transaction_history'),

    # Deposit (no verification)
    path('deposit/', views.deposit_view, name='deposit'),

    # Instant transfer (legacy/optional)
    path('transfer/instant/', views.transfer_view, name='transfer'),

    # Verified (IMF/COT) request-based flows
    path('withdraw/request/', views.withdrawal_request, name='withdrawal_request'),
    path('transfer/request/', views.transfer_request, name='transfer_request'),

    # Verification steps (updated to accept UUIDs)
    path('verify/imf/<uuid:transaction_id>/', views.verify_imf, name='verify_imf'),
    path('verify/cot/<uuid:transaction_id>/', views.verify_cot, name='verify_cot'),
    path('verify/step1/<uuid:transaction_id>/', views.verify_step1, name='verify_step1'),
    path('verify/step2/<uuid:transaction_id>/', views.verify_step2, name='verify_step2'),
    path('verify/step3/<uuid:transaction_id>/', views.verify_step3, name='verify_step3'),
    path('verify/complete/<uuid:transaction_id>/', views.verify_complete, name='verify_complete'),
]
