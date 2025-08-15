from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('merchant/dashboard/', views.merchant_dashboard, name='merchant_dashboard'),
    path('user/dashboard/', views.user_dashboard, name='user_dashboard'),
    path('merchant/register-shop/', views.register_shop, name='register_shop'),
    path('merchant/add-product/', views.add_product, name='add_product'),
    path('merchant/view-products/', views.view_products, name='view_products'),
    path('merchant/edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('', views.home_redirect, name='home'),
] 