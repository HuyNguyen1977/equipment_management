"""
API Views cho Mobile App
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from .serializers import (
    UserSerializer, CompanySerializer,
    EquipmentSerializer, EquipmentListSerializer, EquipmentHistorySerializer,
    NASConfigSerializer, NASLogSerializer,
    TicketSerializer, TicketCategorySerializer, DepartmentSerializer,
    RenewalSerializer, RenewalTypeSerializer
)
from .permissions import IsStaffOrReadOnly, IsOwnerOrStaff
from equipment.models import Company, Equipment, EquipmentHistory
from nas_management.models import NASConfig, NASLog
from tickets.models import Ticket, TicketCategory, Department
from renewals.models import Renewal, RenewalType


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """API cho User"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Lấy thông tin user hiện tại"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    """API cho Company"""
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]


class EquipmentViewSet(viewsets.ModelViewSet):
    """API cho Equipment"""
    queryset = Equipment.objects.select_related('company', 'current_user').prefetch_related('history')
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EquipmentListSerializer
        return EquipmentSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter theo company
        company_id = self.request.query_params.get('company_id')
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        
        # Filter theo equipment_type
        equipment_type = self.request.query_params.get('equipment_type')
        if equipment_type:
            queryset = queryset.filter(equipment_type=equipment_type)
        
        # Filter theo region
        region = self.request.query_params.get('region')
        if region:
            queryset = queryset.filter(region=region)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(machine_name__icontains=search)
            )
        
        # Filter is_active
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Lấy lịch sử của thiết bị"""
        equipment = self.get_object()
        history = equipment.history.all().order_by('-action_date')
        serializer = EquipmentHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_history(self, request, pk=None):
        """Thêm lịch sử cho thiết bị"""
        equipment = self.get_object()
        serializer = EquipmentHistorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(equipment=equipment, signed_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EquipmentHistoryViewSet(viewsets.ModelViewSet):
    """API cho EquipmentHistory"""
    queryset = EquipmentHistory.objects.select_related('equipment', 'signed_by')
    serializer_class = EquipmentHistorySerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        equipment_id = self.request.query_params.get('equipment_id')
        if equipment_id:
            queryset = queryset.filter(equipment_id=equipment_id)
        return queryset.order_by('-action_date')


class NASConfigViewSet(viewsets.ReadOnlyModelViewSet):
    """API cho NASConfig"""
    queryset = NASConfig.objects.filter(is_active=True)
    serializer_class = NASConfigSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """Lấy logs của NAS"""
        nas = self.get_object()
        logs = NASLog.objects.filter(nas=nas).order_by('-timestamp')[:200]
        
        # Filter theo log_type
        log_type = request.query_params.get('log_type')
        if log_type:
            logs = logs.filter(log_type=log_type)
        
        # Filter theo level
        level = request.query_params.get('level')
        if level:
            logs = logs.filter(level=level)
        
        serializer = NASLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def dashboard(self, request, pk=None):
        """Dashboard stats cho NAS"""
        nas = self.get_object()
        
        # Thống kê logs
        total_logs = NASLog.objects.filter(nas=nas).count()
        logs_by_type = {}
        logs_by_level = {}
        
        for log_type, _ in NASLog.LOG_TYPE_CHOICES:
            count = NASLog.objects.filter(nas=nas, log_type=log_type).count()
            logs_by_type[log_type] = count
        
        for level, _ in NASLog.LOG_LEVEL_CHOICES:
            count = NASLog.objects.filter(nas=nas, level=level).count()
            logs_by_level[level] = count
        
        return Response({
            'total_logs': total_logs,
            'logs_by_type': logs_by_type,
            'logs_by_level': logs_by_level,
        })


class NASLogViewSet(viewsets.ReadOnlyModelViewSet):
    """API cho NASLog"""
    queryset = NASLog.objects.select_related('nas')
    serializer_class = NASLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter theo nas
        nas_id = self.request.query_params.get('nas_id')
        if nas_id:
            queryset = queryset.filter(nas_id=nas_id)
        
        # Filter theo log_type
        log_type = self.request.query_params.get('log_type')
        if log_type:
            queryset = queryset.filter(log_type=log_type)
        
        # Filter theo level
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        return queryset.order_by('-timestamp')


class TicketViewSet(viewsets.ModelViewSet):
    """API cho Ticket"""
    queryset = Ticket.objects.select_related(
        'requester', 'company', 'department', 'category', 'assigned_to'
    )
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # User thường chỉ xem tickets của mình, staff xem tất cả
        if not self.request.user.is_staff:
            queryset = queryset.filter(requester=self.request.user)
        
        # Filter theo status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter theo priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter theo company
        company_id = self.request.query_params.get('company_id')
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(ticket_number__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Tự động set requester khi tạo ticket"""
        serializer.save(requester=self.request.user)


class TicketCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API cho TicketCategory"""
    queryset = TicketCategory.objects.all()
    serializer_class = TicketCategorySerializer
    permission_classes = [IsAuthenticated]


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """API cho Department"""
    queryset = Department.objects.select_related('company')
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        company_id = self.request.query_params.get('company_id')
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        return queryset


class RenewalViewSet(viewsets.ModelViewSet):
    """API cho Renewal"""
    queryset = Renewal.objects.select_related('company', 'renewal_type')
    serializer_class = RenewalSerializer
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter theo company
        company_id = self.request.query_params.get('company_id')
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        
        # Filter is_active
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter sắp hết hạn (30 ngày)
        expiring_soon = self.request.query_params.get('expiring_soon')
        if expiring_soon:
            future_date = timezone.now().date() + timedelta(days=30)
            queryset = queryset.filter(
                end_date__lte=future_date,
                end_date__gte=timezone.now().date(),
                is_active=True
            )
        
        return queryset.order_by('end_date')


class RenewalTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """API cho RenewalType"""
    queryset = RenewalType.objects.all()
    serializer_class = RenewalTypeSerializer
    permission_classes = [IsAuthenticated]


# Authentication views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Đăng nhập"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Username và password là bắt buộc'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        serializer = UserSerializer(user)
        return Response({
            'user': serializer.data,
            'message': 'Đăng nhập thành công'
        })
    else:
        return Response(
            {'error': 'Username hoặc password không đúng'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Đăng xuất"""
    logout(request)
    return Response({'message': 'Đăng xuất thành công'})



