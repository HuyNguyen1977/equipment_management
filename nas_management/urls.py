from django.urls import path
from . import views

app_name = 'nas_management'

urlpatterns = [
    path('', views.nas_dashboard, name='dashboard'),
    path('login-history/', views.login_history, name='login_history'),
    path('login-history/sync/<int:nas_id>/', views.sync_login_history, name='sync_login_history'),
    path('logs/', views.nas_logs, name='nas_logs'),
    path('logs/dashboard/', views.logs_dashboard, name='logs_dashboard'),
    path('logs/dashboard/syslog/', views.syslog_dashboard, name='syslog_dashboard'),
    path('logs/dashboard/connectlog/', views.connectlog_dashboard, name='connectlog_dashboard'),
    path('logs/dashboard/filexferlog/', views.filexferlog_dashboard, name='filexferlog_dashboard'),
    path('logs/sync/<int:nas_id>/', views.sync_logs, name='sync_logs'),
    path('logs/upload-csv/', views.upload_logs_csv, name='upload_logs_csv'),
    path('logs/clear-all/', views.clear_all_logs, name='clear_all_logs'),
    path('files/', views.file_manager, name='file_manager'),
    path('files/upload/<int:nas_id>/', views.upload_file, name='upload_file'),
    path('files/download/<int:nas_id>/', views.download_file, name='download_file'),
    path('files/create-folder/<int:nas_id>/', views.create_folder, name='create_folder'),
    path('files/delete/<int:nas_id>/', views.delete_file, name='delete_file'),
    path('file-operations/', views.file_operations, name='file_operations'),
]
