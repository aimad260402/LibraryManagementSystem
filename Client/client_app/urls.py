from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('create_book/', views.create_book_view, name='create_book'),
]