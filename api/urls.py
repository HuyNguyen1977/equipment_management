"""
URLs cho REST API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'companies', views.CompanyViewSet, basename='company')
router.register(r'equipment', views.EquipmentViewSet, basename='equipment')
router.register(r'equipment-history', views.EquipmentHistoryViewSet, basename='equipment-history')
router.register(r'nas', views.NASConfigViewSet, basename='nas')
router.register(r'nas-logs', views.NASLogViewSet, basename='nas-log')
router.register(r'tickets', views.TicketViewSet, basename='ticket')
router.register(r'ticket-categories', views.TicketCategoryViewSet, basename='ticket-category')
router.register(r'departments', views.DepartmentViewSet, basename='department')
router.register(r'renewals', views.RenewalViewSet, basename='renewal')
router.register(r'renewal-types', views.RenewalTypeViewSet, basename='renewal-type')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', views.login_view, name='api-login'),
    path('auth/logout/', views.logout_view, name='api-logout'),
    path('auth/user/me/', views.UserViewSet.as_view({'get': 'me'}), name='api-user-me'),
]



