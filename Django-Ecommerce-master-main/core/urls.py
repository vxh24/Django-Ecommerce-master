from django.urls import path
from . import views
from .views import (
    ItemDetailView,
    HomeView,
    add_to_cart,
    remove_from_cart,
    ShopView,
    OrderSummaryView,
    remove_single_item_from_cart,
    CheckoutView,
    PaymentView,
    AddCouponView,
    RequestRefundView,
    CategoryView,
    SearchView,
    ProfileView,
    OrderDeliveryView,
    RevenueAnalyticsView
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('profile/', ProfileView.as_view(), name='view_profile'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('category/<slug>/', CategoryView.as_view(), name='category'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('add_coupon/', AddCouponView.as_view(), name='add-coupon'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('shop/', ShopView.as_view(), name='shop'),
    path('search', SearchView.as_view(), name='search'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('remove-item-from-cart/<slug>/', remove_single_item_from_cart,
         name='remove-single-item-from-cart'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('order-delivery/', OrderDeliveryView.as_view(), name='order-delivery'),
    path('revenue-analytics/', RevenueAnalyticsView.as_view(), name='revenue-analytics'),
    path('request-refund/', RequestRefundView.as_view(), name='request-refund')
]
