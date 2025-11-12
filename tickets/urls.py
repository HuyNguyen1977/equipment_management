from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.ticket_list, name='ticket_list'),
    path('create/', views.ticket_create, name='ticket_create'),
    path('api/search-users/', views.search_users, name='search_users'),
    path('api/create-user-quick/', views.create_user_quick, name='create_user_quick'),
    path('api/get-departments/', views.get_departments, name='get_departments'),
    path('api/get-categories/', views.get_categories, name='get_categories'),
    path('<str:ticket_number>/', views.ticket_detail, name='ticket_detail'),
    path('<str:ticket_number>/update/', views.ticket_update, name='ticket_update'),
    path('<str:ticket_number>/comment/', views.ticket_comment, name='ticket_comment'),
    path('<str:ticket_number>/attachment/', views.ticket_attachment, name='ticket_attachment'),
]

