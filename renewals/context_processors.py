from django.utils import timezone
from datetime import timedelta
from .models import Renewal


def renewal_notifications(request):
    """Context processor để đếm số dịch vụ sắp hết hạn"""
    expiring_soon_count = 0
    
    if request.user.is_authenticated:
        # Đếm các dịch vụ sắp hết hạn trong vòng 30 ngày
        today = timezone.now().date()
        future_date = today + timedelta(days=30)
        expiring_soon_count = Renewal.objects.filter(
            expiry_date__gte=today,
            expiry_date__lte=future_date,
            status='active'
        ).count()
    
    return {
        'expiring_soon_count': expiring_soon_count,
    }

