from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse, FileResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from datetime import datetime, timedelta
import json
import csv
import io

from .models import NASConfig, LoginHistory, SystemStats, NASLog, FileOperation
from .synology_api import SynologyAPIClient, SynologyAPIError


@staff_member_required
def nas_dashboard(request):
    """Dashboard theo dõi CPU/RAM/Disk"""
    nas_list = NASConfig.objects.filter(is_active=True)
    
    # Lấy NAS được chọn hoặc NAS đầu tiên
    nas_id = request.GET.get('nas_id')
    selected_nas = None
    stats_data = None
    recent_stats = None
    
    if nas_id:
        selected_nas = get_object_or_404(NASConfig, id=nas_id, is_active=True)
    elif nas_list.exists():
        selected_nas = nas_list.first()
    
    if selected_nas:
        try:
            with SynologyAPIClient(selected_nas) as client:
                # Lấy thông tin CPU và Memory
                cpu_info = client.get_cpu_info()
                memory_info = client.get_memory_info()
                disk_info = client.get_disk_info()
                
                # Tính toán stats
                cpu_usage = cpu_info.get('cpu', {}).get('system_load', 0)
                memory_data = cpu_info.get('memory', {})
                memory_total = memory_data.get('total', 0)
                memory_used = memory_data.get('real_usage', 0)
                memory_usage = (memory_used / memory_total * 100) if memory_total > 0 else 0
                
                stats_data = {
                    'cpu_usage': round(cpu_usage, 2),
                    'memory_usage': round(memory_usage, 2),
                    'memory_total': memory_total,
                    'memory_used': memory_used,
                    'memory_free': memory_total - memory_used,
                    'disk_info': disk_info,
                }
                
                # Lưu vào database
                SystemStats.objects.create(
                    nas=selected_nas,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    memory_total=memory_total,
                    memory_used=memory_used,
                    disk_usage=disk_info,
                )
                
        except SynologyAPIError as e:
            messages.error(request, f"Lỗi kết nối NAS: {str(e)}")
        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")
        
        # Lấy stats gần đây để vẽ biểu đồ
        recent_stats = SystemStats.objects.filter(
            nas=selected_nas
        ).order_by('-timestamp')[:60]  # 60 điểm gần nhất
    
    context = {
        'nas_list': nas_list,
        'selected_nas': selected_nas,
        'stats_data': stats_data,
        'recent_stats': recent_stats,
    }
    return render(request, 'nas_management/dashboard.html', context)


@staff_member_required
def login_history(request):
    """Xem lịch sử đăng nhập"""
    nas_list = NASConfig.objects.filter(is_active=True)
    
    # Filter
    nas_id = request.GET.get('nas_id')
    username = request.GET.get('username', '').strip()
    is_success = request.GET.get('is_success')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    login_history = LoginHistory.objects.all()
    
    if nas_id:
        login_history = login_history.filter(nas_id=nas_id)
    
    if username:
        login_history = login_history.filter(username__icontains=username)
    
    if is_success:
        login_history = login_history.filter(is_success=(is_success == '1'))
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            login_history = login_history.filter(login_time__gte=date_from_obj)
        except:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            login_history = login_history.filter(login_time__lt=date_to_obj)
        except:
            pass
    
    # Phân trang
    paginator = Paginator(login_history.order_by('-login_time'), 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Thống kê login failures
    failure_stats = LoginHistory.objects.filter(
        is_success=False
    ).values('ip_address').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'nas_list': nas_list,
        'page_obj': page_obj,
        'login_history': page_obj,
        'failure_stats': failure_stats,
        'selected_nas_id': nas_id,
        'username_filter': username,
        'is_success_filter': is_success,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'nas_management/login_history.html', context)


@staff_member_required
def sync_login_history(request, nas_id):
    """Đồng bộ lịch sử đăng nhập từ NAS"""
    nas = get_object_or_404(NASConfig, id=nas_id, is_active=True)
    
    try:
        with SynologyAPIClient(nas) as client:
            login_logs = client.get_login_history(limit=500)
            
            count = 0
            for log in login_logs:
                username = log.get('user', '')
                ip_address = log.get('ip', '')
                login_time_str = log.get('time', '')
                is_success = log.get('result', '') == 'success'
                failure_reason = log.get('reason', '') if not is_success else ''
                
                # Parse time
                try:
                    login_time = datetime.fromtimestamp(int(login_time_str))
                except:
                    continue
                
                # Tạo hoặc cập nhật
                LoginHistory.objects.update_or_create(
                    nas=nas,
                    username=username,
                    ip_address=ip_address,
                    login_time=login_time,
                    defaults={
                        'is_success': is_success,
                        'failure_reason': failure_reason,
                        'user_agent': log.get('user_agent', ''),
                    }
                )
                count += 1
            
            messages.success(request, f'Đã đồng bộ {count} bản ghi đăng nhập từ {nas.name}')
            
    except SynologyAPIError as e:
        messages.error(request, f"Lỗi: {str(e)}")
    except Exception as e:
        messages.error(request, f"Lỗi: {str(e)}")
    
    return redirect('nas_management:login_history')


def _get_logs_dashboard_data(request, log_type):
    """Helper function để lấy dữ liệu dashboard cho từng loại log"""
    nas_list = NASConfig.objects.filter(is_active=True)
    
    # Filter
    nas_id = request.GET.get('nas_id')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Mặc định lấy 30 ngày gần nhất
    if not date_to:
        date_to = timezone.now().date()
    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    
    logs = NASLog.objects.filter(log_type=log_type)
    
    if nas_id:
        logs = logs.filter(nas_id=nas_id)
        selected_nas = get_object_or_404(NASConfig, id=nas_id, is_active=True)
    else:
        selected_nas = None
    
    # Filter theo ngày
    if date_from:
        try:
            date_from_obj = datetime.strptime(str(date_from), '%Y-%m-%d')
            if timezone.is_naive(date_from_obj):
                date_from_obj = timezone.make_aware(date_from_obj)
            logs = logs.filter(timestamp__gte=date_from_obj)
        except:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(str(date_to), '%Y-%m-%d') + timedelta(days=1)
            if timezone.is_naive(date_to_obj):
                date_to_obj = timezone.make_aware(date_to_obj)
            logs = logs.filter(timestamp__lt=date_to_obj)
        except:
            pass
    
    # Thống kê tổng quan
    total_logs = logs.count()
    logs_by_level = logs.values('level').annotate(count=Count('id')).order_by('level')
    logs_by_nas = logs.values('nas__name').annotate(count=Count('id')).order_by('-count')
    logs_by_category = logs.values('category').annotate(count=Count('id')).order_by('-count')[:10]
    logs_by_source = logs.values('source').annotate(count=Count('id')).order_by('-count')[:10]
    
    # Thống kê theo ngày (30 ngày gần nhất)
    daily_stats = []
    for i in range(30):
        day = (timezone.now() - timedelta(days=29-i)).date()
        day_start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
        day_end = day_start + timedelta(days=1)
        day_logs = logs.filter(timestamp__gte=day_start, timestamp__lt=day_end)
        daily_stats.append({
            'date': day,
            'total': day_logs.count(),
            'info': day_logs.filter(level='info').count(),
            'warning': day_logs.filter(level='warning').count(),
            'error': day_logs.filter(level='error').count(),
            'critical': day_logs.filter(level='critical').count(),
        })
    
    # Logs gần đây
    recent_logs = logs.order_by('-timestamp')[:20]
    
    # Tổng hợp theo level
    level_stats = {
        'info': logs.filter(level='info').count(),
        'warning': logs.filter(level='warning').count(),
        'error': logs.filter(level='error').count(),
        'critical': logs.filter(level='critical').count(),
    }
    
    # Thống kê đặc biệt cho filexferlog
    filexfer_stats = None
    if log_type == 'filexferlog':
        filexfer_stats = {
            'by_operation': logs.values('operation').annotate(count=Count('id')).order_by('-count')[:10],
            'by_user': logs.values('source').annotate(count=Count('id')).order_by('-count')[:10],
            'top_files': logs.exclude(file_path='').values('file_path').annotate(count=Count('id')).order_by('-count')[:10],
        }
    elif log_type == 'connectlog':
        # Thống kê đặc biệt cho connectlog
        filexfer_stats = {
            'by_user': logs.values('source').annotate(count=Count('id')).order_by('-count')[:10],
            'by_category': logs.values('category').annotate(count=Count('id')).order_by('-count')[:10],
        }
    
    return {
        'nas_list': nas_list,
        'selected_nas': selected_nas,
        'selected_nas_id': str(nas_id) if nas_id else '',
        'date_from': str(date_from) if date_from else '',
        'date_to': str(date_to) if date_to else '',
        'log_type': log_type,
        'total_logs': total_logs,
        'level_stats': level_stats,
        'logs_by_level': logs_by_level,
        'logs_by_nas': logs_by_nas,
        'logs_by_category': logs_by_category,
        'logs_by_source': logs_by_source,
        'daily_stats': daily_stats,
        'recent_logs': recent_logs,
        'filexfer_stats': filexfer_stats,
    }


@staff_member_required
def syslog_dashboard(request):
    """Dashboard thống kê System Logs"""
    context = _get_logs_dashboard_data(request, 'syslog')
    context['log_type_display'] = 'System Logs'
    return render(request, 'nas_management/logs_dashboard.html', context)


@staff_member_required
def connectlog_dashboard(request):
    """Dashboard thống kê Connection Logs"""
    context = _get_logs_dashboard_data(request, 'connectlog')
    context['log_type_display'] = 'Connection Logs'
    return render(request, 'nas_management/logs_dashboard.html', context)


@staff_member_required
def filexferlog_dashboard(request):
    """Dashboard thống kê File Transfer Logs"""
    context = _get_logs_dashboard_data(request, 'filexferlog')
    context['log_type_display'] = 'File Transfer Logs'
    return render(request, 'nas_management/logs_dashboard.html', context)


@staff_member_required
def logs_dashboard(request):
    """Dashboard thống kê logs NAS - tổng hợp tất cả"""
    nas_list = NASConfig.objects.filter(is_active=True)
    
    # Filter
    nas_id = request.GET.get('nas_id')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # Mặc định lấy 30 ngày gần nhất
    if not date_to:
        date_to = timezone.now().date()
    if not date_from:
        date_from = (timezone.now() - timedelta(days=30)).date()
    
    logs = NASLog.objects.all()
    
    if nas_id:
        logs = logs.filter(nas_id=nas_id)
        selected_nas = get_object_or_404(NASConfig, id=nas_id, is_active=True)
    else:
        selected_nas = None
    
    # Filter theo ngày
    if date_from:
        try:
            date_from_obj = datetime.strptime(str(date_from), '%Y-%m-%d')
            if timezone.is_naive(date_from_obj):
                date_from_obj = timezone.make_aware(date_from_obj)
            logs = logs.filter(timestamp__gte=date_from_obj)
        except:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(str(date_to), '%Y-%m-%d') + timedelta(days=1)
            if timezone.is_naive(date_to_obj):
                date_to_obj = timezone.make_aware(date_to_obj)
            logs = logs.filter(timestamp__lt=date_to_obj)
        except:
            pass
    
    # Thống kê theo loại log
    logs_by_type = logs.values('log_type').annotate(count=Count('id')).order_by('log_type')
    
    # Thống kê tổng quan
    total_logs = logs.count()
    level_stats = {
        'info': logs.filter(level='info').count(),
        'warning': logs.filter(level='warning').count(),
        'error': logs.filter(level='error').count(),
        'critical': logs.filter(level='critical').count(),
    }
    
    # Thống kê theo ngày (30 ngày gần nhất)
    daily_stats = []
    for i in range(30):
        day = (timezone.now() - timedelta(days=29-i)).date()
        day_start = timezone.make_aware(datetime.combine(day, datetime.min.time()))
        day_end = day_start + timedelta(days=1)
        day_logs = logs.filter(timestamp__gte=day_start, timestamp__lt=day_end)
        daily_stats.append({
            'date': day,
            'total': day_logs.count(),
            'syslog': day_logs.filter(log_type='syslog').count(),
            'connectlog': day_logs.filter(log_type='connectlog').count(),
            'filexferlog': day_logs.filter(log_type='filexferlog').count(),
        })
    
    context = {
        'nas_list': nas_list,
        'selected_nas': selected_nas,
        'selected_nas_id': str(nas_id) if nas_id else '',
        'date_from': str(date_from) if date_from else '',
        'date_to': str(date_to) if date_to else '',
        'total_logs': total_logs,
        'level_stats': level_stats,
        'logs_by_type': logs_by_type,
        'daily_stats': daily_stats,
        'log_type': None,  # Tổng hợp
        'log_type_display': 'All Logs',
    }
    return render(request, 'nas_management/logs_dashboard.html', context)


@staff_member_required
def nas_logs(request):
    """Xem logs của NAS"""
    nas_list = NASConfig.objects.filter(is_active=True)
    
    # Filter
    nas_id = request.GET.get('nas_id')
    log_type = request.GET.get('log_type')
    level = request.GET.get('level')
    category = request.GET.get('category', '').strip()
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    logs = NASLog.objects.all()
    
    if nas_id:
        logs = logs.filter(nas_id=nas_id)
    
    if log_type:
        logs = logs.filter(log_type=log_type)
    
    if level:
        logs = logs.filter(level=level)
    
    if category:
        logs = logs.filter(category__icontains=category)
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            logs = logs.filter(timestamp__gte=date_from_obj)
        except:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            logs = logs.filter(timestamp__lt=date_to_obj)
        except:
            pass
    
    # Phân trang
    paginator = Paginator(logs.order_by('-timestamp'), 100)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    from .forms import LogCSVUploadForm
    upload_form = LogCSVUploadForm()
    
    context = {
        'nas_list': nas_list,
        'page_obj': page_obj,
        'logs': page_obj,
        'selected_nas_id': str(nas_id) if nas_id else '',
        'log_type_filter': log_type or '',
        'level_filter': level or '',
        'category_filter': category or '',
        'date_from': date_from or '',
        'date_to': date_to or '',
        'upload_form': upload_form,
    }
    return render(request, 'nas_management/logs.html', context)


@staff_member_required
def sync_logs(request, nas_id):
    """Đồng bộ logs từ NAS"""
    nas = get_object_or_404(NASConfig, id=nas_id, is_active=True)
    
    try:
        with SynologyAPIClient(nas) as client:
            # Thử lấy logs với limit lớn hơn
            nas_logs = client.get_logs(limit=1000)
            
            # Debug: log số lượng logs nhận được
            import logging
            logger = logging.getLogger('nas_management')
            logger.info(f"Received {len(nas_logs)} logs from {nas.name}")
            
            if not nas_logs:
                # Thử kiểm tra xem có thể kết nối được không và API nào có sẵn
                try:
                    # Test một API đơn giản để xem có kết nối được không
                    test_info = client.get_system_info()
                    logger.info(f"System info retrieved: {test_info}")
                    
                    # Kiểm tra API info
                    eventlog_info = client.get_api_info('SYNO.Core.EventLog')
                    has_eventlog_api = bool(eventlog_info)
                    
                    # Lấy danh sách tất cả API để debug
                    all_apis = client.list_all_apis()
                    log_related_apis = [api for api in all_apis.keys() if 'log' in api.lower() or 'event' in api.lower()]
                    
                    if not has_eventlog_api:
                        error_msg = (
                            f'Không tìm thấy API SYNO.Core.EventLog từ {nas.name}.\n\n'
                            f'⚠️ Log Center package có thể chưa được cài đặt hoặc chưa được kích hoạt trên NAS.\n\n'
                            f'📋 Hướng dẫn:\n'
                            f'1. Đăng nhập vào DSM của NAS\n'
                            f'2. Vào Package Center\n'
                            f'3. Tìm và cài đặt "Log Center"\n'
                            f'4. Sau khi cài đặt, mở Log Center và kích hoạt\n'
                            f'5. Đảm bảo user "{nas.username}" có quyền truy cập Log Center\n\n'
                        )
                        if log_related_apis:
                            error_msg += f'📌 Các API liên quan đến log tìm thấy: {", ".join(log_related_apis[:5])}\n\n'
                        error_msg += f'Hoặc chạy command để kiểm tra chi tiết:\n'
                        error_msg += f'python manage.py test_nas_logs --nas-id {nas_id}'
                    else:
                        error_msg = (
                            f'Không tìm thấy log nào từ {nas.name}.\n\n'
                            f'Có thể:\n'
                            f'1. NAS không có log nào trong thời gian này\n'
                            f'2. User "{nas.username}" không có quyền truy cập logs\n'
                            f'3. Log Center chưa được cấu hình để thu thập logs\n\n'
                            f'Vui lòng kiểm tra Log Center trên NAS hoặc chạy command:\n'
                            f'python manage.py test_nas_logs --nas-id {nas_id}'
                        )
                except Exception as e:
                    error_msg = (
                        f'Không thể kết nối đến NAS {nas.name}: {str(e)}\n\n'
                        f'Vui lòng kiểm tra:\n'
                        f'1. NAS có đang hoạt động không\n'
                        f'2. Thông tin đăng nhập có đúng không\n'
                        f'3. Firewall có chặn kết nối không'
                    )
                
                messages.warning(request, error_msg)
                # Giữ lại filter khi redirect
                redirect_url = reverse('nas_management:nas_logs')
                if nas_id:
                    redirect_url += f'?nas_id={nas_id}'
                return redirect(redirect_url)
            
            count = 0
            errors = []
            skipped_invalid = 0
            skipped_short = 0
            
            for log_entry in nas_logs:
                try:
                    # Xử lý level - normalize về lowercase
                    level_raw = log_entry.get('level', 'info')
                    level = level_raw.lower() if isinstance(level_raw, str) else 'info'
                    if level not in ['info', 'warning', 'error', 'critical']:
                        level = 'info'
                    
                    # Xử lý category
                    category = log_entry.get('category', '') or log_entry.get('program', '') or ''
                    
                    # Xử lý message
                    message = log_entry.get('message', '') or log_entry.get('msg', '') or log_entry.get('content', '') or str(log_entry)
                    
                    # Xử lý source
                    source = log_entry.get('source', '') or log_entry.get('host_name', '') or log_entry.get('module', '') or log_entry.get('program', '') or ''
                    
                    # Xử lý timestamp
                    timestamp_str = log_entry.get('time', '') or log_entry.get('timestamp', '')
                    timestamp = None
                    
                    if timestamp_str:
                        try:
                            # Có thể là Unix timestamp (số) hoặc string
                            if isinstance(timestamp_str, (int, float)):
                                timestamp = datetime.fromtimestamp(timestamp_str)
                            elif isinstance(timestamp_str, str) and timestamp_str.isdigit():
                                timestamp = datetime.fromtimestamp(int(timestamp_str))
                            else:
                                # Thử parse từ datetime string (nhiều format khác nhau)
                                for fmt in ['%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                                    try:
                                        timestamp = datetime.strptime(str(timestamp_str), fmt)
                                        break
                                    except:
                                        continue
                                if not timestamp:
                                    timestamp = timezone.now()
                        except (ValueError, TypeError) as e:
                            timestamp = timezone.now()
                    else:
                        timestamp = timezone.now()
                    
                    # Đảm bảo timestamp có timezone
                    if timezone.is_naive(timestamp):
                        timestamp = timezone.make_aware(timestamp)
                    
                    # Kiểm tra xem đây có phải là log entry hợp lệ không
                    # Bỏ qua các response lỗi API (chứa JSON error)
                    message_lower = message.lower() if message else ''
                    if any(indicator in message_lower for indicator in ['{"error":', '"success":false', '"code":', 'api error']):
                        skipped_invalid += 1
                        logger.debug(f"Skipping invalid log entry (API error response): {message[:100]}")
                        continue
                    
                    # Kiểm tra message không được quá ngắn hoặc chỉ là JSON rỗng
                    if len(message.strip()) < 5:
                        skipped_short += 1
                        continue
                    
                    # Tạo unique key để tránh duplicate
                    # Sử dụng nas + timestamp + message để tạo unique
                    # Giới hạn độ dài để tránh lỗi database
                    message_short = message[:500] if message else ''
                    category_short = category[:100] if category else ''
                    source_short = source[:200] if source else ''
                    
                    NASLog.objects.update_or_create(
                        nas=nas,
                        timestamp=timestamp,
                        message=message_short,
                        defaults={
                            'level': level,
                            'category': category_short,
                            'source': source_short,
                        }
                    )
                    count += 1
                except Exception as e:
                    errors.append(f"Entry error: {str(e)}")
                    logger.error(f"Error processing log entry: {str(e)}, Entry: {log_entry}")
                    continue
            
            # Thông báo kết quả chi tiết
            if count > 0:
                messages.success(request, f'Đã đồng bộ {count} log từ {nas.name}')
                if skipped_invalid > 0 or skipped_short > 0:
                    skip_msg = []
                    if skipped_invalid > 0:
                        skip_msg.append(f'{skipped_invalid} log không hợp lệ (API error)')
                    if skipped_short > 0:
                        skip_msg.append(f'{skipped_short} log quá ngắn')
                    if skip_msg:
                        messages.info(request, f'Đã bỏ qua: {", ".join(skip_msg)}')
            else:
                # Thông báo chi tiết hơn khi không có log nào được lưu
                detail_msg = f'Không thể đồng bộ log từ {nas.name}.\n\n'
                if len(nas_logs) > 0:
                    detail_msg += f'Đã nhận được {len(nas_logs)} log entries nhưng:\n'
                    if skipped_invalid > 0:
                        detail_msg += f'- {skipped_invalid} log không hợp lệ (chứa JSON error response)\n'
                    if skipped_short > 0:
                        detail_msg += f'- {skipped_short} log quá ngắn\n'
                    if len(errors) > 0:
                        detail_msg += f'- {len(errors)} log gặp lỗi khi xử lý\n'
                    detail_msg += '\nCó thể format dữ liệu từ NAS không đúng hoặc cần cấu hình lại.'
                else:
                    detail_msg += 'Không nhận được log nào từ NAS. Vui lòng kiểm tra:\n'
                    detail_msg += '1. NAS có đang tạo logs không\n'
                    detail_msg += '2. User có quyền truy cập logs không\n'
                    detail_msg += '3. Log Center có được cài đặt và kích hoạt không'
                
                messages.warning(request, detail_msg)
            
            if errors:
                messages.warning(request, f'Có {len(errors)} lỗi khi xử lý logs. Đã đồng bộ được {count} log.')
            
    except SynologyAPIError as e:
        messages.error(request, f"Lỗi API: {str(e)}")
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        messages.error(request, f"Lỗi: {str(e)}")
        # Log chi tiết lỗi để debug
        import logging
        logger = logging.getLogger('nas_management')
        logger.error(f"Error syncing logs: {error_detail}")
    
    # Giữ lại filter khi redirect
    redirect_url = reverse('nas_management:nas_logs')
    if nas_id:
        redirect_url += f'?nas_id={nas_id}'
    return redirect(redirect_url)


@staff_member_required
def upload_logs_csv(request):
    """Upload và import logs từ file CSV export từ NAS - hỗ trợ 3 loại: syslog, connectlog, filexferlog"""
    from .forms import LogCSVUploadForm
    from django.db import IntegrityError
    
    if request.method == 'POST':
        form = LogCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            nas = form.cleaned_data['nas']
            csv_file = form.cleaned_data['csv_file']
            
            try:
                # Đọc file CSV
                if csv_file.name.endswith('.csv'):
                    # Detect loại log từ filename
                    filename_lower = csv_file.name.lower()
                    log_type = None
                    if 'syslog' in filename_lower:
                        log_type = 'syslog'
                    elif 'connectlog' in filename_lower:
                        log_type = 'connectlog'
                    elif 'filexferlog' in filename_lower or 'filexfer' in filename_lower:
                        log_type = 'filexferlog'
                    
                    # Decode file content
                    file_content = csv_file.read()
                    try:
                        text_content = file_content.decode('utf-8')
                    except UnicodeDecodeError:
                        text_content = file_content.decode('utf-8-sig')  # BOM
                    
                    # Parse CSV
                    csv_reader = csv.reader(io.StringIO(text_content))
                    rows = list(csv_reader)
                    
                    if len(rows) < 2:
                        messages.error(request, 'File CSV không hợp lệ. Cần có ít nhất header và 1 dòng dữ liệu.')
                        return redirect('nas_management:nas_logs')
                    
                    # Detect loại log từ content nếu chưa detect từ filename
                    if not log_type:
                        first_row = rows[0] if rows else []
                        if first_row and len(first_row) == 1:
                            if first_row[0] == 'System':
                                log_type = 'syslog'
                            elif first_row[0] == 'Connection':
                                log_type = 'connectlog'
                            elif first_row[0] == 'File Transfer':
                                log_type = 'filexferlog'
                    
                    # Nếu vẫn chưa detect được, thử từ header
                    if not log_type:
                        for i in range(min(3, len(rows))):
                            if rows[i] and len(rows[i]) >= 2:
                                header_lower = ' '.join(rows[i]).lower()
                                if 'ip address' in header_lower and 'file' in header_lower:
                                    log_type = 'filexferlog'
                                    break
                                elif 'level' in header_lower and 'log' in header_lower:
                                    # Có thể là syslog hoặc connectlog
                                    if i > 0 and rows[i-1] and len(rows[i-1]) == 1:
                                        if rows[i-1][0] == 'System':
                                            log_type = 'syslog'
                                        elif rows[i-1][0] == 'Connection':
                                            log_type = 'connectlog'
                                    else:
                                        log_type = 'syslog'  # Default
                                    break
                    
                    if not log_type:
                        messages.error(request, 'Không thể xác định loại log. Vui lòng đặt tên file chứa: syslog, connectlog, hoặc filexferlog')
                        return redirect('nas_management:nas_logs')
                    
                    # Tính toán khoảng thời gian: tháng hiện tại và tháng trước
                    now = timezone.now()
                    current_month_start = datetime(now.year, now.month, 1)
                    if now.month == 1:
                        previous_month_start = datetime(now.year - 1, 12, 1)
                    else:
                        previous_month_start = datetime(now.year, now.month - 1, 1)
                    
                    # Đảm bảo timezone aware
                    if timezone.is_naive(current_month_start):
                        current_month_start = timezone.make_aware(current_month_start)
                    if timezone.is_naive(previous_month_start):
                        previous_month_start = timezone.make_aware(previous_month_start)
                    
                    # Lấy timestamp của log mới nhất trong database cho NAS và log_type này
                    last_log = NASLog.objects.filter(nas=nas, log_type=log_type).order_by('-timestamp').first()
                    last_timestamp = last_log.timestamp if last_log else None
                    
                    # Parse theo loại log
                    logs_to_create = []  # Danh sách logs để bulk create
                    count = 0
                    errors = []
                    skipped = 0
                    skipped_old = 0  # Đếm số log bị bỏ qua vì quá cũ
                    skipped_existing = 0  # Đếm số log đã tồn tại (timestamp <= last_timestamp)
                    
                    if log_type in ['syslog', 'connectlog']:
                        # Format: Level,Log,Time,User,Event
                        start_row = 0
                        if rows[0] and len(rows[0]) == 1 and rows[0][0] in ['System', 'Connection']:
                            start_row = 1
                        
                        header_row = None
                        for i in range(start_row, min(start_row + 3, len(rows))):
                            if len(rows[i]) >= 5:
                                header_row = i
                                break
                        
                        if header_row is None:
                            messages.error(request, f'Không tìm thấy header trong file CSV {log_type}. Format cần: Level,Log,Time,User,Event')
                            return redirect('nas_management:nas_logs')
                        
                        for row_idx in range(header_row + 1, len(rows)):
                            if len(rows[row_idx]) < 5:
                                continue
                            
                            try:
                                level_str = rows[row_idx][0].strip() if len(rows[row_idx]) > 0 else 'Info'
                                category = rows[row_idx][1].strip() if len(rows[row_idx]) > 1 else (log_type.capitalize())
                                time_str = rows[row_idx][2].strip() if len(rows[row_idx]) > 2 else ''
                                user = rows[row_idx][3].strip() if len(rows[row_idx]) > 3 else ''
                                event = rows[row_idx][4].strip() if len(rows[row_idx]) > 4 else ''
                                
                                # Validate message
                                if not event or len(event.strip()) < 5:
                                    skipped += 1
                                    continue
                                
                                # Normalize level
                                level = level_str.lower()
                                if level not in ['info', 'warning', 'error', 'critical']:
                                    if 'error' in level_str.lower() or 'failed' in level_str.lower():
                                        level = 'error'
                                    elif 'warn' in level_str.lower():
                                        level = 'warning'
                                    else:
                                        level = 'info'
                                
                                # Parse timestamp
                                timestamp = None
                                if time_str:
                                    try:
                                        timestamp = datetime.strptime(time_str, '%Y/%m/%d %H:%M:%S')
                                    except ValueError:
                                        try:
                                            timestamp = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                                        except ValueError:
                                            timestamp = timezone.now()
                                else:
                                    timestamp = timezone.now()
                                
                                if timezone.is_naive(timestamp):
                                    timestamp = timezone.make_aware(timestamp)
                                
                                # Chỉ lấy log của tháng hiện tại và tháng trước
                                if timestamp < previous_month_start:
                                    skipped_old += 1
                                    continue
                                
                                # Chỉ lấy log mới hơn log cuối cùng trong database
                                if last_timestamp and timestamp <= last_timestamp:
                                    skipped_existing += 1
                                    continue
                                
                                # Thêm vào danh sách để bulk create
                                message_short = event[:500]
                                logs_to_create.append(
                                    NASLog(
                                        nas=nas,
                                        log_type=log_type,
                                        timestamp=timestamp,
                                        message=message_short,
                                        level=level,
                                        category=category[:100] if category else (log_type.capitalize()),
                                        source=user[:200] if user else 'SYSTEM',
                                    )
                                )
                                count += 1
                                    
                            except Exception as e:
                                errors.append(f"Row {row_idx + 1}: {str(e)}")
                                continue
                    
                    elif log_type == 'filexferlog':
                        # Format: Log,Time,IP address,User,Event,File/Folder,File size,File name
                        header_row = None
                        for i in range(min(3, len(rows))):
                            if rows[i] and len(rows[i]) >= 8:
                                header_lower = ' '.join(rows[i]).lower()
                                if 'ip address' in header_lower and 'file' in header_lower:
                                    header_row = i
                                    break
                        
                        if header_row is None:
                            messages.error(request, 'Không tìm thấy header trong file filexferlog. Format cần: Log,Time,IP address,User,Event,File/Folder,File size,File name')
                            return redirect('nas_management:nas_logs')
                        
                        for row_idx in range(header_row + 1, len(rows)):
                            if len(rows[row_idx]) < 8:
                                continue
                            
                            try:
                                log_protocol = rows[row_idx][0].strip() if len(rows[row_idx]) > 0 else 'SMB'
                                time_str = rows[row_idx][1].strip() if len(rows[row_idx]) > 1 else ''
                                ip_address = rows[row_idx][2].strip() if len(rows[row_idx]) > 2 else ''
                                user = rows[row_idx][3].strip() if len(rows[row_idx]) > 3 else ''
                                operation = rows[row_idx][4].strip() if len(rows[row_idx]) > 4 else ''
                                file_type = rows[row_idx][5].strip() if len(rows[row_idx]) > 5 else ''
                                file_size = rows[row_idx][6].strip() if len(rows[row_idx]) > 6 else ''
                                file_path = rows[row_idx][7].strip() if len(rows[row_idx]) > 7 else ''
                                
                                # Validate
                                if not time_str or not file_path:
                                    skipped += 1
                                    continue
                                
                                # Parse timestamp
                                timestamp = None
                                try:
                                    timestamp = datetime.strptime(time_str, '%Y/%m/%d %H:%M:%S')
                                except ValueError:
                                    try:
                                        timestamp = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                                    except ValueError:
                                        timestamp = timezone.now()
                                
                                if timezone.is_naive(timestamp):
                                    timestamp = timezone.make_aware(timestamp)
                                
                                # Chỉ lấy log của tháng hiện tại và tháng trước
                                if timestamp < previous_month_start:
                                    skipped_old += 1
                                    continue
                                
                                # Chỉ lấy log mới hơn log cuối cùng trong database
                                if last_timestamp and timestamp <= last_timestamp:
                                    skipped_existing += 1
                                    continue
                                
                                # Tạo message từ các thông tin
                                message = f"{operation} {file_type}: {file_path}"
                                message_short = message[:500]
                                
                                # Extract file name từ path
                                file_name = file_path.split('/')[-1] if '/' in file_path else file_path
                                
                                # Thêm vào danh sách để bulk create
                                logs_to_create.append(
                                    NASLog(
                                        nas=nas,
                                        log_type=log_type,
                                        timestamp=timestamp,
                                        message=message_short,
                                        level='info',
                                        category=log_protocol,
                                        source=user[:200] if user else '',
                                        ip_address=ip_address if ip_address else None,
                                        operation=operation[:50] if operation else '',
                                        file_path=file_path[:1000] if file_path else '',
                                        file_size=file_size[:100] if file_size else '',
                                        file_name=file_name[:500] if file_name else '',
                                    )
                                )
                                count += 1
                                    
                            except Exception as e:
                                errors.append(f"Row {row_idx + 1}: {str(e)}")
                                continue
                    
                    # Bulk create tất cả logs (chỉ insert, không check duplicate)
                    if logs_to_create:
                        try:
                            # Chia nhỏ thành batch 1000 để tránh lỗi memory
                            batch_size = 1000
                            for i in range(0, len(logs_to_create), batch_size):
                                batch = logs_to_create[i:i + batch_size]
                                NASLog.objects.bulk_create(batch, ignore_conflicts=True)
                        except Exception as e:
                            import logging
                            logger = logging.getLogger('nas_management')
                            logger.error(f"Error bulk creating logs: {str(e)}")
                            messages.error(request, f'Lỗi khi lưu logs: {str(e)}')
                            return redirect('nas_management:nas_logs')
                    
                    # Thông báo kết quả
                    log_type_display = dict(NASLog.LOG_TYPE_CHOICES).get(log_type, log_type)
                    if count > 0:
                        msg = f'Đã import {count} {log_type_display} vào {nas.name}'
                        if skipped_existing > 0:
                            msg += f' ({skipped_existing} log đã tồn tại đã bỏ qua)'
                        messages.success(request, msg)
                        if skipped > 0:
                            messages.info(request, f'Đã bỏ qua {skipped} log không hợp lệ')
                        if skipped_old > 0:
                            messages.info(request, f'Đã bỏ qua {skipped_old} log cũ (chỉ import tháng hiện tại và tháng trước)')
                        if errors:
                            messages.warning(request, f'Có {len(errors)} lỗi khi xử lý. Đã import được {count} log.')
                    else:
                        if skipped_existing > 0:
                            messages.info(request, f'Tất cả {skipped_existing} bản ghi đã tồn tại trong database (không có log mới).')
                        elif skipped_old > 0:
                            messages.warning(request, f'Tất cả logs trong file đều cũ hơn tháng hiện tại và tháng trước. Đã bỏ qua {skipped_old} log.')
                        else:
                            messages.warning(request, f'Không thể import {log_type_display}. Có thể format file không đúng hoặc không có dữ liệu hợp lệ.')
                            if errors:
                                messages.error(request, f'Lỗi: {errors[0] if len(errors) == 1 else f"{len(errors)} lỗi"}')
                else:
                    messages.error(request, 'File phải có định dạng CSV (.csv)')
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                messages.error(request, f'Lỗi khi đọc file CSV: {str(e)}')
                import logging
                logger = logging.getLogger('nas_management')
                logger.error(f"Error uploading CSV: {error_detail}")
        else:
            messages.error(request, 'Form không hợp lệ. Vui lòng kiểm tra lại.')
    else:
        form = LogCSVUploadForm()
    
    # Giữ lại filter khi redirect
    redirect_url = reverse('nas_management:nas_logs')
    nas_id = request.GET.get('nas_id')
    if nas_id:
        redirect_url += f'?nas_id={nas_id}'
    
    if form.errors:
        context = {
            'form': form,
            'show_upload_modal': True,
        }
        return render(request, 'nas_management/logs.html', context)
    
    return redirect(redirect_url)


@staff_member_required
def clear_all_logs(request):
    """Xóa tất cả logs trong database"""
    if request.method == 'POST':
        try:
            # Lấy số lượng logs trước khi xóa
            total_count = NASLog.objects.count()
            
            # Xóa tất cả logs
            NASLog.objects.all().delete()
            
            messages.success(request, f'Đã xóa tất cả {total_count} logs trong database.')
        except Exception as e:
            messages.error(request, f'Lỗi khi xóa logs: {str(e)}')
            import logging
            logger = logging.getLogger('nas_management')
            logger.error(f"Error clearing logs: {str(e)}")
    
    # Redirect về trang logs
    redirect_url = reverse('nas_management:nas_logs')
    nas_id = request.GET.get('nas_id')
    if nas_id:
        redirect_url += f'?nas_id={nas_id}'
    return redirect(redirect_url)


@staff_member_required
def file_manager(request):
    """Quản lý file/folder"""
    nas_list = NASConfig.objects.filter(is_active=True)
    
    nas_id = request.GET.get('nas_id')
    path = request.GET.get('path', '/')
    
    selected_nas = None
    files = []
    current_path = path
    
    if nas_id:
        selected_nas = get_object_or_404(NASConfig, id=nas_id, is_active=True)
    elif nas_list.exists():
        selected_nas = nas_list.first()
    
    if selected_nas:
        try:
            with SynologyAPIClient(selected_nas) as client:
                files_data = client.list_files(folder_path=current_path)
                files = files_data
        except SynologyAPIError as e:
            messages.error(request, f"Lỗi: {str(e)}")
        except Exception as e:
            messages.error(request, f"Lỗi: {str(e)}")
    
    context = {
        'nas_list': nas_list,
        'selected_nas': selected_nas,
        'files': files,
        'current_path': current_path,
    }
    return render(request, 'nas_management/file_manager.html', context)


@staff_member_required
@require_http_methods(["POST"])
def upload_file(request, nas_id):
    """Upload file lên NAS"""
    nas = get_object_or_404(NASConfig, id=nas_id, is_active=True)
    
    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'Không có file'})
    
    file = request.FILES['file']
    folder_path = request.POST.get('path', '/')
    
    try:
        with SynologyAPIClient(nas) as client:
            file_content = file.read()
            success = client.upload_file(folder_path, file_content)
            
            if success:
                # Ghi log
                FileOperation.objects.create(
                    nas=nas,
                    user=request.user,
                    operation='upload',
                    file_path=f"{folder_path}/{file.name}",
                    file_size=file.size,
                    is_success=True,
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
                
                return JsonResponse({'success': True, 'message': 'Upload thành công'})
            else:
                return JsonResponse({'success': False, 'error': 'Upload thất bại'})
                
    except SynologyAPIError as e:
        FileOperation.objects.create(
            nas=nas,
            user=request.user,
            operation='upload',
            file_path=f"{folder_path}/{file.name}",
            file_size=file.size,
            is_success=False,
            error_message=str(e),
            ip_address=request.META.get('REMOTE_ADDR'),
        )
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
def download_file(request, nas_id):
    """Download file từ NAS"""
    nas = get_object_or_404(NASConfig, id=nas_id, is_active=True)
    file_path = request.GET.get('path')
    
    if not file_path:
        messages.error(request, 'Không có đường dẫn file')
        return redirect('nas_management:file_manager')
    
    try:
        with SynologyAPIClient(nas) as client:
            file_content = client.download_file(file_path)
            
            # Ghi log
            FileOperation.objects.create(
                nas=nas,
                user=request.user,
                operation='download',
                file_path=file_path,
                file_size=len(file_content),
                is_success=True,
                ip_address=request.META.get('REMOTE_ADDR'),
            )
            
            # Trả về file
            import os
            filename = os.path.basename(file_path)
            response = HttpResponse(file_content, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
    except SynologyAPIError as e:
        FileOperation.objects.create(
            nas=nas,
            user=request.user,
            operation='download',
            file_path=file_path,
            is_success=False,
            error_message=str(e),
            ip_address=request.META.get('REMOTE_ADDR'),
        )
        messages.error(request, f"Lỗi: {str(e)}")
        return redirect('nas_management:file_manager')
    except Exception as e:
        messages.error(request, f"Lỗi: {str(e)}")
        return redirect('nas_management:file_manager')


@staff_member_required
@require_http_methods(["POST"])
def create_folder(request, nas_id):
    """Tạo folder mới"""
    nas = get_object_or_404(NASConfig, id=nas_id, is_active=True)
    
    folder_path = request.POST.get('path', '/')
    folder_name = request.POST.get('name', '').strip()
    
    if not folder_name:
        return JsonResponse({'success': False, 'error': 'Tên folder không được để trống'})
    
    try:
        with SynologyAPIClient(nas) as client:
            success = client.create_folder(folder_path, folder_name)
            
            if success:
                FileOperation.objects.create(
                    nas=nas,
                    user=request.user,
                    operation='create_folder',
                    file_path=f"{folder_path}/{folder_name}",
                    is_success=True,
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
                return JsonResponse({'success': True, 'message': 'Tạo folder thành công'})
            else:
                return JsonResponse({'success': False, 'error': 'Tạo folder thất bại'})
                
    except SynologyAPIError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
@require_http_methods(["POST"])
def delete_file(request, nas_id):
    """Xóa file/folder"""
    nas = get_object_or_404(NASConfig, id=nas_id, is_active=True)
    
    file_path = request.POST.get('path')
    
    if not file_path:
        return JsonResponse({'success': False, 'error': 'Không có đường dẫn file'})
    
    try:
        with SynologyAPIClient(nas) as client:
            success = client.delete_file(file_path)
            
            if success:
                FileOperation.objects.create(
                    nas=nas,
                    user=request.user,
                    operation='delete',
                    file_path=file_path,
                    is_success=True,
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
                return JsonResponse({'success': True, 'message': 'Xóa thành công'})
            else:
                return JsonResponse({'success': False, 'error': 'Xóa thất bại'})
                
    except SynologyAPIError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@staff_member_required
def file_operations(request):
    """Lịch sử thao tác file"""
    nas_list = NASConfig.objects.filter(is_active=True)
    
    nas_id = request.GET.get('nas_id')
    operation = request.GET.get('operation')
    user_id = request.GET.get('user_id')
    
    operations = FileOperation.objects.all()
    
    if nas_id:
        operations = operations.filter(nas_id=nas_id)
    
    if operation:
        operations = operations.filter(operation=operation)
    
    if user_id:
        operations = operations.filter(user_id=user_id)
    
    # Phân trang
    paginator = Paginator(operations.order_by('-timestamp'), 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'nas_list': nas_list,
        'page_obj': page_obj,
        'operations': page_obj,
        'selected_nas_id': nas_id,
        'operation_filter': operation,
        'user_id_filter': user_id,
    }
    return render(request, 'nas_management/file_operations.html', context)
