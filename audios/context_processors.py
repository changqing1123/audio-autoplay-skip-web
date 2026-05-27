from datetime import timedelta

from django.utils import timezone

from .models import Audio, UserListened


def admin_dashboard_stats(request):
    if request.path != '/admin/':
        return {}

    now = timezone.localtime()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    fifteen_days_ago = now - timedelta(days=15)
    thirty_days_ago = now - timedelta(days=30)

    return {
        'dashboard_stats': {
            'today_listened_count': UserListened.objects.filter(listened_time__gte=today_start).count(),
            'yesterday_listened_count': UserListened.objects.filter(
                listened_time__gte=yesterday_start,
                listened_time__lt=today_start,
            ).count(),
            'audio_count': Audio.objects.count(),
            'older_than_15_count': Audio.objects.filter(upload_time__lt=fifteen_days_ago).count(),
            'older_than_30_count': Audio.objects.filter(upload_time__lt=thirty_days_ago).count(),
        },
    }
