from django.urls import path
from . import views, escrow_views

app_name = 'marketplace'

urlpatterns = [
    # Purchase endpoints
    path('purchases/<uuid:purchase_id>/', views.update_purchase, name='update_purchase'),
    path('purchases/<uuid:purchase_id>/details/', views.get_purchase, name='get_purchase'),
    path('purchases/', views.list_user_purchases, name='list_purchases'),
    
    # Escrow endpoints
    path('purchases/<uuid:purchase_id>/escrow/', escrow_views.create_escrow, name='create_escrow'),
    path('escrows/<uuid:escrow_id>/', escrow_views.get_escrow, name='get_escrow'),
    path('escrows/<uuid:escrow_id>/confirm-delivery/', escrow_views.confirm_delivery, name='confirm_delivery'),
    path('escrows/<uuid:escrow_id>/confirm-receipt/', escrow_views.confirm_receipt, name='confirm_receipt'),
    path('escrows/<uuid:escrow_id>/dispute/', escrow_views.create_dispute, name='create_dispute'),
    path('escrows/<uuid:escrow_id>/resolve/', escrow_views.resolve_dispute, name='resolve_dispute'),
    path('escrows/<uuid:escrow_id>/auto-release/', escrow_views.auto_release_escrow, name='auto_release_escrow'),
    path('escrows/', escrow_views.list_user_escrows, name='list_user_escrows'),
]
