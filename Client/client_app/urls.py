
from django.urls import path
from . import views

urlpatterns = [
    # Login path handles both GET (display form) and POST (process form)
    path('login/', views.staff_login, name='staff_login'), 
    
    # Dashboard path handles the book search form submission (via GET parameters)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-book/', views.add_book, name='add_book'),
    path('profile/', views.staff_profile, name='staff_profile'),
    path('logout/', views.staff_logout, name='staff_logout'),
    path('', views.staff_login, name='home'), # Default route redirects to login
    path('users/create/', views.create_user, name='create_user'),
    path('users/', views.users_list, name='users_list'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users/delete/<int:user_id>/', views.delete_user_action, name='delete_user_action'),
    path('clients/', views.clients_list, name='clients_list'),
    path('clients/create/', views.create_client, name='create_client'),
    path('clients/view/<int:client_id>/', views.view_client, name='view_client'),
    path('clients/edit/<int:client_id>/', views.edit_client, name='edit_client'),
    path('clients/delete/<int:client_id>/', views.delete_client_action, name='delete_client_action'),
    #######Commendes#######
    path('emprunts/', views.emprunts_list, name='emprunts_list'),
    path('emprunts/add/', views.add_emprunt, name='add_emprunt'),
    path('emprunts/return/<int:emprunt_id>/', views.return_emprunt, name='return_emprunt'),
    path('emprunts/delete/<int:emprunt_id>/', views.delete_emprunt, name='delete_emprunt'),
    path('emprunts/edit/<int:emprunt_id>/', views.edit_emprunt, name='edit_emprunt')


]