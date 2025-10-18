"""
URL configuration for api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
import app_api.users.account_view as account_views
import app_api.users.address_view as address_views
import app_api.users.payment_view as payment_views
import app_api.users.wishlist_view as wishlist_views
import app_api.carts.view as cart_views
import app_api.products.view as product_views
import app_api.orders.view as order_views

urlpatterns = [
    path('users/admin/register/', account_views.register_admin),
    path('users/staff/register/', account_views.register_staff),
    path('users/login/', account_views.login_view),
    path('users/register/', account_views.register),
    path('users/logout/', account_views.logout_view),
    path('users/is_logged_in/', account_views.is_logged_in),
    path('users/delete/', account_views.delete_user),
    path('users/profile/', account_views.get_users_profile),
    path('users/profile/update/', account_views.update_user_profile),
    path('users/profile/upload_profile_picture/', account_views.upload_profile_picture),
    path('users/change_password/', account_views.change_password),
    path('users/address/add/', address_views.add_address),
    path('users/address/edit/', address_views.edit_address),
    path('users/address/set_default/', address_views.set_default_address),
    path('users/address/delete/', address_views.remove_address),
    path('users/address/', address_views.get_addresses),
    path('users/payment_methods/add_credit_card/', payment_views.add_credit_card),
    path('users/payment_methods/', payment_views.list_credit_cards),
    path('users/payment_methods/remove_credit_card/<int:pm_id>/', payment_views.remove_credit_card),
    path('users/payment_methods/add_bank_account/', payment_views.add_bank_account),
    path('users/payment_methods/list_bank_accounts/', payment_views.list_bank_accounts),
    path('users/payment_methods/remove_bank_account/<int:ba_id>/', payment_views.remove_bank_account),
    path('users/wishlist/add/', wishlist_views.add_to_wishlist),
    path('users/wishlist/remove/<int:product_id>/', wishlist_views.remove_from_wishlist),
    path('users/wishlist/', wishlist_views.get_wishlist),
    path('products/add/', product_views.add_product),
    path('products/get_product_detail/<int:product_id>/', product_views.get_product_detail),
    path('products/get_3d_model/<int:model_id>/', product_views.get_3d_model),
    path('products/get_display_scene/<int:display_scene_id>/', product_views.get_display_scene),
    path('products/get_texture/<int:model_id>/', product_views.get_textures),
    path('products/update/', product_views.update_product),
    path('products/delete/<int:product_id>/', product_views.delete_product),
    path('products/list/', product_views.get_products),
    path('products/categories/', product_views.get_all_categories),
    path('products/types/', product_views.get_all_product_types),
    path('carts/add_item/', cart_views.add_to_cart),
    path('carts/remove_item/<int:cart_item_id>/', cart_views.remove_from_cart),
    path('carts/view/', cart_views.view_cart),
    path('carts/clear_cart/', cart_views.clear_cart),
    path('carts/summary/', cart_views.get_cart_summary),
    path('orders/checkout/', order_views.checkout),
    path('orders/list/', order_views.list_orders),
    path('orders/payment_completed/<int:order_id>/', order_views.payment_completed),
    path('orders/cancel/<int:order_id>/', order_views.cancel_order),
    path("orders/complete/<int:order_id>/", order_views.complete_order),

    # For debugging purposes
    path('test/add_3d_model/', product_views.add_3d_model),
    path('test/add_texture/', product_views.add_texture),
    path('test/get_texture/<int:texture_id>/', product_views.get_texture),
    path('test/add_display_scene/', product_views.add_display_scene),
    path('test/get_display_scene/<int:product_id>/', product_views.get_display_scenes),

]
