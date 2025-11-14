from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime, timedelta
from .models import Ticket, TicketComment, TicketAttachment, Company, Department, TicketCategory
from .forms import TicketForm, TicketUpdateForm, TicketCommentForm, TicketAttachmentForm


def ticket_create(request):
    """Tạo ticket mới từ webform (không cần đăng nhập)"""
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save()
            
            # Xử lý file đính kèm nếu có
            if 'attachment' in request.FILES:
                attachment = TicketAttachment(
                    ticket=ticket,
                    file=request.FILES['attachment'],
                    filename=request.FILES['attachment'].name,
                    uploaded_by=ticket.requester
                )
                attachment.save()
            
            # Kiểm tra số lần lặp lại trong tháng
            month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            similar_tickets = Ticket.objects.filter(
                requester=ticket.requester,
                category=ticket.category,
                title__icontains=ticket.title[:50],  # So sánh 50 ký tự đầu
                created_at__gte=month_start
            ).exclude(id=ticket.id)
            
            ticket.repeat_count = similar_tickets.count()
            ticket.save()
            
            # Gửi email thông báo
            try:
                send_ticket_emails(ticket, request)
            except Exception as e:
                # Log lỗi nhưng không làm gián đoạn quá trình tạo ticket
                import logging
                logger = logging.getLogger('tickets')
                logger.error(f'Error sending ticket emails: {str(e)}')
            
            messages.success(
                request,
                f'Ticket {ticket.ticket_number} đã được tạo thành công! '
                f'Chúng tôi sẽ liên hệ với bạn sớm nhất có thể.'
            )
            # return redirect('tickets:ticket_detail', ticket_number=ticket.ticket_number)
            return redirect("https://saigonbooks.vn")
    else:
        form = TicketForm()
    
    context = {
        'form': form,
        'title': 'Yêu cầu hỗ trợ IT'
    }
    return render(request, 'tickets/ticket_form.html', context)


@login_required
def ticket_list(request):
    """Danh sách ticket (cần đăng nhập)"""
    tickets = Ticket.objects.select_related(
        'requester', 'company', 'department', 'category', 'assigned_to'
    ).all()
    
    # Filter theo trạng thái
    status = request.GET.get('status')
    if status:
        tickets = tickets.filter(status=status)
    
    # Filter theo mức độ ưu tiên
    priority = request.GET.get('priority')
    if priority:
        tickets = tickets.filter(priority=priority)
    
    # Filter theo công ty
    company_id = request.GET.get('company')
    if company_id:
        tickets = tickets.filter(company_id=company_id)
    
    # Filter theo loại yêu cầu
    category_id = request.GET.get('category')
    if category_id:
        tickets = tickets.filter(category_id=category_id)
    
    # Filter theo người được phân công
    assigned_to_id = request.GET.get('assigned_to')
    if assigned_to_id:
        tickets = tickets.filter(assigned_to_id=assigned_to_id)
    
    # Search
    search = request.GET.get('search', '').strip()
    if search:
        tickets = tickets.filter(
            Q(ticket_number__icontains=search) |
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(requester_name__icontains=search) |
            Q(requester_email__icontains=search)
        )
    
    # Nếu không phải staff, chỉ hiển thị ticket của mình
    if not request.user.is_staff:
        tickets = tickets.filter(requester=request.user)
    
    # Sắp xếp
    order_by = request.GET.get('order_by', '-created_at')
    tickets = tickets.order_by(order_by)
    
    # Phân trang
    paginator = Paginator(tickets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Thống kê
    stats = {
        'total': Ticket.objects.count(),
        'new': Ticket.objects.filter(status='new').count(),
        'in_progress': Ticket.objects.filter(status='in_progress').count(),
        'resolved': Ticket.objects.filter(status='resolved').count(),
        'closed': Ticket.objects.filter(status='closed').count(),
    }
    
    # Nếu không phải staff, chỉ đếm ticket của mình
    if not request.user.is_staff:
        user_tickets = Ticket.objects.filter(requester=request.user)
        stats = {
            'total': user_tickets.count(),
            'new': user_tickets.filter(status='new').count(),
            'in_progress': user_tickets.filter(status='in_progress').count(),
            'resolved': user_tickets.filter(status='resolved').count(),
            'closed': user_tickets.filter(status='closed').count(),
        }
    
    context = {
        'page_obj': page_obj,
        'tickets': page_obj,
        'stats': stats,
        'companies': Company.objects.all().order_by('name'),
        'categories': TicketCategory.objects.filter(parent__isnull=False).order_by('order', 'name'),
        'selected_status': status,
        'selected_priority': priority,
        'selected_company': company_id,
        'selected_category': category_id,
        'selected_assigned_to': assigned_to_id,
        'search_query': search,
        'order_by': order_by,
    }
    return render(request, 'tickets/ticket_list.html', context)


def ticket_detail(request, ticket_number):
    """Chi tiết ticket"""
    ticket = get_object_or_404(Ticket, ticket_number=ticket_number)
    
    # Kiểm tra quyền xem
    if not request.user.is_staff and ticket.requester != request.user:
        messages.error(request, 'Bạn không có quyền xem ticket này!')
        return redirect('tickets:ticket_list')
    
    # Form cập nhật (chỉ IT mới thấy)
    update_form = None
    if request.user.is_staff:
        update_form = TicketUpdateForm(instance=ticket)
    
    # Form bình luận
    comment_form = TicketCommentForm()
    
    # Form upload file
    attachment_form = TicketAttachmentForm()
    
    # Lấy bình luận (ẩn internal nếu không phải staff)
    comments = ticket.comments.all()
    if not request.user.is_staff:
        comments = comments.filter(is_internal=False)
    
    context = {
        'ticket': ticket,
        'comments': comments,
        'attachments': ticket.attachments.all(),
        'update_form': update_form,
        'comment_form': comment_form,
        'attachment_form': attachment_form,
        'can_edit': request.user.is_staff or ticket.requester == request.user,
    }
    return render(request, 'tickets/ticket_detail.html', context)


@login_required
def ticket_update(request, ticket_number):
    """Cập nhật ticket (chỉ IT)"""
    if not request.user.is_staff:
        messages.error(request, 'Bạn không có quyền thực hiện thao tác này!')
        return redirect('tickets:ticket_list')
    
    ticket = get_object_or_404(Ticket, ticket_number=ticket_number)
    
    if request.method == 'POST':
        form = TicketUpdateForm(request.POST, instance=ticket)
        if form.is_valid():
            old_status = ticket.status
            ticket = form.save()
            
            # Tạo bình luận tự động khi thay đổi trạng thái
            if old_status != ticket.status:
                old_status_display = dict(Ticket.STATUS_CHOICES).get(old_status, old_status)
                new_status_display = ticket.get_status_display()
                comment = TicketComment(
                    ticket=ticket,
                    author=request.user,
                    content=f'Trạng thái đã thay đổi từ "{old_status_display}" sang "{new_status_display}"',
                    is_internal=False
                )
                comment.save()
            
            messages.success(request, f'Đã cập nhật ticket {ticket.ticket_number}!')
            return redirect('tickets:ticket_detail', ticket_number=ticket.ticket_number)
    else:
        form = TicketUpdateForm(instance=ticket)
    
    context = {
        'ticket': ticket,
        'form': form,
    }
    return render(request, 'tickets/ticket_update.html', context)


@login_required
def ticket_comment(request, ticket_number):
    """Thêm bình luận vào ticket"""
    ticket = get_object_or_404(Ticket, ticket_number=ticket_number)
    
    # Kiểm tra quyền
    if not request.user.is_staff and ticket.requester != request.user:
        messages.error(request, 'Bạn không có quyền bình luận ticket này!')
        return redirect('tickets:ticket_list')
    
    if request.method == 'POST':
        form = TicketCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.author = request.user
            comment.save()
            
            # Cập nhật thời gian cập nhật ticket
            ticket.updated_at = timezone.now()
            ticket.save(update_fields=['updated_at'])
            
            messages.success(request, 'Đã thêm bình luận!')
            return redirect('tickets:ticket_detail', ticket_number=ticket_number)
    
    return redirect('tickets:ticket_detail', ticket_number=ticket_number)


@login_required
def ticket_attachment(request, ticket_number):
    """Upload file đính kèm"""
    ticket = get_object_or_404(Ticket, ticket_number=ticket_number)
    
    # Kiểm tra quyền
    if not request.user.is_staff and ticket.requester != request.user:
        messages.error(request, 'Bạn không có quyền upload file cho ticket này!')
        return redirect('tickets:ticket_list')
    
    if request.method == 'POST':
        form = TicketAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.ticket = ticket
            attachment.uploaded_by = request.user
            attachment.filename = request.FILES['file'].name
            attachment.save()
            
            messages.success(request, 'Đã upload file thành công!')
            return redirect('tickets:ticket_detail', ticket_number=ticket_number)
    
    return redirect('tickets:ticket_detail', ticket_number=ticket_number)


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


@require_http_methods(["GET"])
def get_departments(request):
    """AJAX endpoint để lấy danh sách departments con theo parent"""
    parent_id = request.GET.get('parent_id')
    if not parent_id:
        return JsonResponse({'departments': []})
    
    try:
        departments = Department.objects.filter(parent_id=parent_id).order_by('order', 'name')
        results = [{'id': dept.id, 'name': dept.name} for dept in departments]
        return JsonResponse({'departments': results})
    except Exception as e:
        return JsonResponse({'departments': [], 'error': str(e)})


@require_http_methods(["GET"])
def get_categories(request):
    """AJAX endpoint để lấy danh sách categories con theo parent"""
    parent_id = request.GET.get('parent_id')
    if not parent_id:
        return JsonResponse({'categories': []})
    
    try:
        categories = TicketCategory.objects.filter(parent_id=parent_id).order_by('order', 'name')
        results = [{'id': cat.id, 'name': cat.name} for cat in categories]
        return JsonResponse({'categories': results})
    except Exception as e:
        return JsonResponse({'categories': [], 'error': str(e)})


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
            password='Pega@2025'  # Password mặc định
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


def send_ticket_emails(ticket, request):
    """Gửi email thông báo khi tạo ticket mới"""
    # Tạo URL cho ticket
    ticket_url = request.build_absolute_uri(ticket.get_absolute_url())
    
    # 1. Gửi email cho người yêu cầu
    if ticket.requester_email:
        subject_requester = f'[Ticket {ticket.ticket_number}] Yêu cầu hỗ trợ IT đã được tiếp nhận'
        
        # Render email template
        html_message_requester = render_to_string(
            'tickets/emails/ticket_created_requester.html',
            {
                'ticket': ticket,
                'ticket_url': ticket_url,
            }
        )
        text_message_requester = render_to_string(
            'tickets/emails/ticket_created_requester.txt',
            {
                'ticket': ticket,
                'ticket_url': ticket_url,
            }
        )
        
        try:
            msg_requester = EmailMultiAlternatives(
                subject=subject_requester,
                body=text_message_requester,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[ticket.requester_email],
            )
            msg_requester.attach_alternative(html_message_requester, "text/html")
            msg_requester.send()
        except Exception as e:
            import logging
            logger = logging.getLogger('tickets')
            logger.error(f'Error sending email to requester {ticket.requester_email}: {str(e)}')
    
    # 2. Gửi email cho tất cả staff members
    staff_users = User.objects.filter(is_staff=True, is_active=True, email__isnull=False).exclude(email='')
    
    if staff_users.exists():
        subject_staff = f'[Ticket {ticket.ticket_number}] Ticket hỗ trợ IT mới - {ticket.title}'
        
        # Render email template
        html_message_staff = render_to_string(
            'tickets/emails/ticket_created_staff.html',
            {
                'ticket': ticket,
                'ticket_url': ticket_url,
            }
        )
        text_message_staff = render_to_string(
            'tickets/emails/ticket_created_staff.txt',
            {
                'ticket': ticket,
                'ticket_url': ticket_url,
            }
        )
        
        # Gửi email cho từng staff member
        staff_emails = [user.email for user in staff_users]
        
        try:
            msg_staff = EmailMultiAlternatives(
                subject=subject_staff,
                body=text_message_staff,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=staff_emails,
            )
            msg_staff.attach_alternative(html_message_staff, "text/html")
            msg_staff.send()
        except Exception as e:
            import logging
            logger = logging.getLogger('tickets')
            logger.error(f'Error sending email to staff: {str(e)}')
