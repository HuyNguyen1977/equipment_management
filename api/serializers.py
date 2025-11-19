"""
Serializers cho REST API
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from equipment.models import Company, Equipment, EquipmentHistory
from nas_management.models import NASConfig, NASLog
from tickets.models import Ticket, TicketCategory, Department
from renewals.models import Renewal, RenewalType


class UserSerializer(serializers.ModelSerializer):
    """Serializer cho User"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class CompanySerializer(serializers.ModelSerializer):
    """Serializer cho Company"""
    class Meta:
        model = Company
        fields = ['id', 'name', 'code', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class EquipmentHistorySerializer(serializers.ModelSerializer):
    """Serializer cho EquipmentHistory"""
    action_type_display = serializers.CharField(source='get_action_type_display', read_only=True)
    signed_by_name = serializers.CharField(source='signed_by.get_full_name', read_only=True)
    
    class Meta:
        model = EquipmentHistory
        fields = [
            'id', 'equipment', 'action_date', 'action_type', 'action_type_display',
            'description', 'signed_by', 'signed_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class EquipmentSerializer(serializers.ModelSerializer):
    """Serializer cho Equipment"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_code = serializers.CharField(source='company.code', read_only=True)
    equipment_type_display = serializers.CharField(source='get_equipment_type_display', read_only=True)
    region_display = serializers.CharField(source='get_region_display', read_only=True)
    current_user_name = serializers.CharField(source='current_user.get_full_name', read_only=True)
    dxdiag_file_url = serializers.SerializerMethodField()
    history = EquipmentHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Equipment
        fields = [
            'id', 'company', 'company_name', 'company_code',
            'region', 'region_display', 'name', 'code',
            'equipment_type', 'equipment_type_display',
            'commission_date', 'machine_name', 'operating_system',
            'system_manufacturer', 'system_model', 'processor',
            'memory', 'storage', 'graphics_card', 'monitor_name',
            'monitor_model', 'technical_specs', 'documentation',
            'dxdiag_file', 'dxdiag_file_url', 'current_user',
            'current_user_name', 'is_active', 'created_at',
            'updated_at', 'history'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_dxdiag_file_url(self, obj):
        """Lấy URL của file DxDiag nếu có"""
        if obj.dxdiag_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.dxdiag_file.url)
        return None


class EquipmentListSerializer(serializers.ModelSerializer):
    """Serializer rút gọn cho danh sách Equipment"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    equipment_type_display = serializers.CharField(source='get_equipment_type_display', read_only=True)
    current_user_name = serializers.CharField(source='current_user.get_full_name', read_only=True)
    
    class Meta:
        model = Equipment
        fields = [
            'id', 'company_name', 'name', 'code',
            'equipment_type', 'equipment_type_display',
            'current_user_name', 'is_active', 'created_at'
        ]


class NASConfigSerializer(serializers.ModelSerializer):
    """Serializer cho NASConfig"""
    class Meta:
        model = NASConfig
        fields = [
            'id', 'name', 'host', 'port', 'username',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True},
        }


class NASLogSerializer(serializers.ModelSerializer):
    """Serializer cho NASLog"""
    nas_name = serializers.CharField(source='nas.name', read_only=True)
    log_type_display = serializers.CharField(source='get_log_type_display', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    
    class Meta:
        model = NASLog
        fields = [
            'id', 'nas', 'nas_name', 'log_type', 'log_type_display',
            'level', 'level_display', 'category', 'message',
            'source', 'timestamp', 'ip_address', 'file_path',
            'file_size', 'file_name', 'operation', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer cho Department"""
    class Meta:
        model = Department
        fields = ['id', 'name', 'code', 'company', 'description']
        read_only_fields = ['id']


class TicketCategorySerializer(serializers.ModelSerializer):
    """Serializer cho TicketCategory"""
    class Meta:
        model = TicketCategory
        fields = ['id', 'name', 'description', 'color']
        read_only_fields = ['id']


class TicketSerializer(serializers.ModelSerializer):
    """Serializer cho Ticket"""
    requester_name = serializers.CharField(source='requester.get_full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_number', 'title', 'description',
            'requester', 'requester_name', 'requester_email',
            'requester_phone', 'company', 'company_name',
            'department', 'department_name', 'category',
            'category_name', 'priority', 'priority_display',
            'status', 'status_display', 'assigned_to',
            'assigned_to_name', 'created_at', 'updated_at',
            'resolved_at', 'closed_at'
        ]
        read_only_fields = [
            'id', 'ticket_number', 'created_at', 'updated_at',
            'resolved_at', 'closed_at'
        ]


class RenewalTypeSerializer(serializers.ModelSerializer):
    """Serializer cho RenewalType"""
    class Meta:
        model = RenewalType
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


class RenewalSerializer(serializers.ModelSerializer):
    """Serializer cho Renewal"""
    renewal_type_name = serializers.CharField(source='renewal_type.name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    
    class Meta:
        model = Renewal
        fields = [
            'id', 'company', 'company_name', 'renewal_type',
            'renewal_type_name', 'service_name', 'provider',
            'start_date', 'end_date', 'cost', 'notes',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']



