from django.urls import path
from . import views

urlpatterns = [
    path('apply/', views.apply_for_job, name='apply'),
    path('applications/', views.admin_applications_view, name='admin_applications'),
    path('applications/<int:pk>/<str:status>/', views.update_status, name='update_status'),
    path('',views.home,name="delivery_home"),
    path('privacy/',views.privacy,name='privacy'),
    path('edit-application/<int:application_id>/', views.edit_application, name='edit_application'),
    path('delete-application/<int:application_id>/', views.delete_application, name='delete_application'),
]
