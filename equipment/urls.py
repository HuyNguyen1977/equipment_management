from django.urls import path
from . import views

app_name = 'equipment'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/search-users/', views.search_users, name='search_users'),
    path('api/create-user-quick/', views.create_user_quick, name='create_user_quick'),
    path('api/get-next-code/', views.get_next_code, name='get_next_code'),
    path('equipment/create/', views.equipment_create, name='equipment_create'),
    path('equipment/<int:pk>/', views.equipment_detail, name='equipment_detail'),
    path('equipment/<int:pk>/edit/', views.equipment_edit, name='equipment_edit'),
    path('equipment/<int:pk>/delete/', views.equipment_delete, name='equipment_delete'),
    path('equipment/<int:pk>/history/', views.equipment_history, name='equipment_history'),
    path('equipment/<int:equipment_pk>/history/add/', views.history_add, name='history_add'),
    path('history/<int:pk>/edit/', views.history_edit, name='history_edit'),
    path('history/<int:pk>/delete/', views.history_delete, name='history_delete'),
    path('report/', views.report, name='report'),
]

