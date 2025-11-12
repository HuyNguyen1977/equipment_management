from .models import Ticket


def ticket_notifications(request):
    """Context processor để đếm số ticket mới"""
    new_tickets_count = 0
    
    if request.user.is_authenticated:
        if request.user.is_staff:
            # Staff xem tất cả ticket mới
            new_tickets_count = Ticket.objects.filter(status='new').count()
        else:
            # User thường chỉ xem ticket mới của mình
            new_tickets_count = Ticket.objects.filter(
                status='new',
                requester=request.user
            ).count()
    
    return {
        'new_tickets_count': new_tickets_count,
    }

