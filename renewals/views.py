from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import timedelta
from .models import Renewal, RenewalType, RenewalHistory
from .forms import RenewalForm, RenewalHistoryForm


@login_required
def renewal_list(request):
    """Danh sách các dịch vụ cần gia hạn"""
    renewals = Renewal.objects.all().select_related(
        'renewal_type', 'company', 'responsible_person', 'created_by'
    )
    
    # Filters
    renewal_type_id = request.GET.get('type')
    status = request.GET.get('status')
    company_id = request.GET.get('company')
    search_query = request.GET.get('search')
    expiring_soon = request.GET.get('expiring_soon')
    
    if renewal_type_id:
        renewals = renewals.filter(renewal_type_id=renewal_type_id)
    
    if status:
        renewals = renewals.filter(status=status)
    
    if company_id:
        renewals = renewals.filter(company_id=company_id)
    
    if search_query:
        renewals = renewals.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(provider__icontains=search_query)
        )
    
    if expiring_soon == 'true':
        # Chỉ lấy các dịch vụ sắp hết hạn (trong vòng 30 ngày)
        today = timezone.now().date()
        future_date = today + timedelta(days=30)
        renewals = renewals.filter(
            expiry_date__gte=today,
            expiry_date__lte=future_date,
            status='active'
        )
    
    # Sắp xếp theo ngày hết hạn
    renewals = renewals.order_by('expiry_date', 'renewal_type')
    
    # Pagination
    paginator = Paginator(renewals, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_count = Renewal.objects.count()
    active_count = Renewal.objects.filter(status='active').count()
    expired_count = Renewal.objects.filter(status='expired').count()
    expiring_soon_count = Renewal.objects.filter(
        expiry_date__gte=timezone.now().date(),
        expiry_date__lte=timezone.now().date() + timedelta(days=30),
        status='active'
    ).count()
    
    # Filter options
    renewal_types = RenewalType.objects.all().order_by('order', 'name')
    companies = Renewal.objects.exclude(company__isnull=True).values_list(
        'company', flat=True
    ).distinct()
    companies = [c for c in companies if c]  # Remove None
    
    context = {
        'page_obj': page_obj,
        'renewal_types': renewal_types,
        'selected_type': renewal_type_id,
        'selected_status': status,
        'selected_company': company_id,
        'search_query': search_query,
        'expiring_soon': expiring_soon,
        'total_count': total_count,
        'active_count': active_count,
        'expired_count': expired_count,
        'expiring_soon_count': expiring_soon_count,
    }
    
    return render(request, 'renewals/renewal_list.html', context)


@login_required
def renewal_detail(request, pk):
    """Chi tiết dịch vụ gia hạn"""
    renewal = get_object_or_404(
        Renewal.objects.select_related(
            'renewal_type', 'company', 'responsible_person', 'created_by'
        ),
        pk=pk
    )
    
    history = renewal.history.all().order_by('-renewal_date', '-created_at')
    
    context = {
        'renewal': renewal,
        'history': history,
    }
    
    return render(request, 'renewals/renewal_detail.html', context)


@staff_member_required
def renewal_create(request):
    """Tạo mới dịch vụ gia hạn"""
    if request.method == 'POST':
        form = RenewalForm(request.POST)
        if form.is_valid():
            renewal = form.save(commit=False)
            renewal.created_by = request.user
            renewal.save()
            messages.success(request, f'Đã tạo dịch vụ gia hạn "{renewal.name}" thành công!')
            return redirect('renewals:renewal_detail', pk=renewal.pk)
    else:
        form = RenewalForm()
    
    return render(request, 'renewals/renewal_form.html', {
        'form': form,
        'title': 'Tạo mới dịch vụ gia hạn'
    })


@staff_member_required
def renewal_edit(request, pk):
    """Chỉnh sửa dịch vụ gia hạn"""
    renewal = get_object_or_404(Renewal, pk=pk)
    
    if request.method == 'POST':
        form = RenewalForm(request.POST, instance=renewal)
        if form.is_valid():
            renewal = form.save()
            messages.success(request, f'Đã cập nhật dịch vụ gia hạn "{renewal.name}" thành công!')
            return redirect('renewals:renewal_detail', pk=renewal.pk)
    else:
        form = RenewalForm(instance=renewal)
    
    return render(request, 'renewals/renewal_form.html', {
        'form': form,
        'renewal': renewal,
        'title': f'Chỉnh sửa: {renewal.name}'
    })


@staff_member_required
def renewal_delete(request, pk):
    """Xóa dịch vụ gia hạn"""
    renewal = get_object_or_404(Renewal, pk=pk)
    
    if request.method == 'POST':
        renewal_name = renewal.name
        renewal.delete()
        messages.success(request, f'Đã xóa dịch vụ gia hạn "{renewal_name}" thành công!')
        return redirect('renewals:renewal_list')
    
    return render(request, 'renewals/renewal_delete.html', {
        'renewal': renewal
    })


@staff_member_required
def renewal_renew(request, pk):
    """Gia hạn dịch vụ"""
    renewal = get_object_or_404(Renewal, pk=pk)
    
    if request.method == 'POST':
        form = RenewalHistoryForm(request.POST, renewal=renewal)
        if form.is_valid():
            history = form.save(commit=False)
            history.renewal = renewal
            history.renewed_by = request.user
            
            # Cập nhật renewal
            renewal.expiry_date = history.new_expiry_date
            renewal.status = 'active'
            renewal.save()
            
            history.save()
            
            messages.success(request, f'Đã gia hạn dịch vụ "{renewal.name}" thành công!')
            return redirect('renewals:renewal_detail', pk=renewal.pk)
    else:
        form = RenewalHistoryForm(renewal=renewal)
    
    return render(request, 'renewals/renewal_renew.html', {
        'renewal': renewal,
        'form': form
    })


@login_required
def search_users(request):
    """AJAX endpoint để tìm kiếm users"""
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse({'users': []})
    
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).filter(is_active=True)[:10]
    
    results = []
    for user in users:
        display_name = user.get_full_name() or user.username
        results.append({
            'id': user.id,
            'username': user.username,
            'display': f"{user.username} ({display_name})",
            'full_name': display_name
        })
    
    return JsonResponse({'users': results})


@login_required
@require_http_methods(["POST"])
def create_user_quick(request):
    """Tạo user nhanh - chỉ cần Name và Email, có thể thêm Username"""
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    username = request.POST.get('username', '').strip()
    
    if not name:
        return JsonResponse({'success': False, 'error': 'Tên là bắt buộc'}, status=400)
    
    if not email:
        return JsonResponse({'success': False, 'error': 'Email là bắt buộc'}, status=400)
    
    # Nếu có username từ form, validate và sử dụng
    if username:
        import re
        # Validate username chỉ chứa chữ cái, số và dấu gạch dưới
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return JsonResponse({'success': False, 'error': 'Tên đăng nhập chỉ được chứa chữ cái, số và dấu gạch dưới (_)'}, status=400)
        
        # Kiểm tra username đã tồn tại chưa
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': f'Tên đăng nhập "{username}" đã tồn tại. Vui lòng chọn tên khác.'}, status=400)
    else:
        # Tạo username từ name (loại bỏ dấu, khoảng trắng, chuyển thành chữ thường)
        import re
        username = re.sub(r'[^a-zA-Z0-9]', '', name.lower())
        if not username:
            username = 'user' + str(User.objects.count() + 1)
        
        # Đảm bảo username là duy nhất
        original_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
    
    try:
        # Tách name thành first_name và last_name
        name_parts = name.split(maxsplit=1)
        first_name = name_parts[0] if name_parts else name
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Tạo user mới với password mặc định Pega@2025
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password='Pega@2025'
        )
        
        display_name = user.get_full_name() or user.username
        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'display': f"{user.username} ({display_name})",
                'full_name': display_name
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
