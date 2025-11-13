from django.urls import path
from . import views

app_name = 'renewals'

urlpatterns = [
    path('', views.renewal_list, name='renewal_list'),
    path('<int:pk>/', views.renewal_detail, name='renewal_detail'),
    path('create/', views.renewal_create, name='renewal_create'),
    path('<int:pk>/edit/', views.renewal_edit, name='renewal_edit'),
    path('<int:pk>/delete/', views.renewal_delete, name='renewal_delete'),
    path('<int:pk>/renew/', views.renewal_renew, name='renewal_renew'),
    path('api/search-users/', views.search_users, name='search_users'),
    path('api/create-user-quick/', views.create_user_quick, name='create_user_quick'),
]

