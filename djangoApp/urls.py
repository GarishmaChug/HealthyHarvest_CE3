from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('' , views.home_view,name='home'),
    path('register/',views.register_view,name='register'),
    path('login/',views.login_view,name='login'),
    path('dashboard/',views.dashboard_view,name='dashboard'),
    path('logout/',views.logout_view,name='logout'),
    # path('profile/',views.product_view,name='profile'),
    # path('product/',views.product_view,name='product'),
    path('search', views.search, name='search'),
    path('all', views.all_view, name='all'),
    path('pharmacy', views.pharmacy_view, name='pharmacy'),
    path('fruits', views.fruits_view, name='fruits'),
    path('beauty', views.beauty_view, name='beauty'),
    path('snacks', views.snacks_view, name='snacks'),
    path('faq',views.faq_view,name='faq'),
    path('cart/', views.cart_view, name='cart'),
    path('checkout', views.checkout_view, name='checkout'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart/<int:item_id>/', views.update_cart_quantity, name='update_cart_quantity'), # Added this line
    path('add-product/', views.product_form, name='product_form'),
    path('edit-product/<int:pk>/', views.product_form, name='product_edit'),
    path('save-product/', views.product_save, name='product_save'),
    path('delete-product/<int:pk>/', views.product_delete, name='product_delete'),
    path('products/', views.product_list, name='product_list'),
    path('terms/',views.terms,name='terms'),
    path('profile/', views.profile_view, name='profile'),
  
    
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    ]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
