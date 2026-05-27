from django.contrib import admin
from django.contrib.admin.views.main import ERROR_FLAG
from django.contrib.auth.models import Group
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.html import format_html
from datetime import timedelta

from .models import Audio, AudioCleanup, UserListened


class UploadTimeOlderThanFilter(admin.SimpleListFilter):
    title = '上传时间'
    parameter_name = 'older_than'
    template = 'admin/audios/audiocleanup/empty_filter.html'

    def lookups(self, request, model_admin):
        return (
            ('15', '15 天之前'),
            ('30', '30 天之前'),
            ('60', '60 天之前'),
            ('90', '90 天之前'),
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        cutoff = timezone.now() - timedelta(days=int(self.value()))
        return queryset.filter(upload_time__lt=cutoff)


class CleanAudioDeleteMixin:
    @admin.action(description='删除所选音频')
    def delete_selected_audios(self, request, queryset):
        total = queryset.count()
        listened_total = UserListened.objects.filter(audio__in=queryset).count()
        for audio in queryset.iterator():
            audio.delete()
        self.message_user(request, f'已删除 {total} 个音频，并清理 {listened_total} 条已听记录及对应文件。')

    def delete_queryset(self, request, queryset):
        for audio in queryset.iterator():
            audio.delete()


@admin.register(Audio)
class AudioAdmin(CleanAudioDeleteMixin, admin.ModelAdmin):
    list_display = ('filename', 'group', 'upload_time', 'listened_record_count')
    list_filter = ('group', 'upload_time')
    search_fields = ('filename', 'group__name')
    ordering = ('-upload_time', '-id')
    fields = ('file', 'group', 'cover')
    actions = ('delete_selected_audios',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('group').annotate(total_listened=Count('listened_users'))

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        first_group = Group.objects.order_by('id').first()
        if first_group:
            initial.setdefault('group', first_group.pk)
        return initial

    @admin.display(description='图片')
    def cover_preview(self, obj):
        cover_url = None
        if obj.cover:
            cover_url = obj.cover.url
        else:
            profile = getattr(obj.group, 'profile', None)
            if profile and profile.default_cover:
                cover_url = profile.default_cover.url
        if not cover_url:
            return '-'
        return format_html(
            '<img src="{}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;" />',
            cover_url,
        )

    @admin.display(description='已听记录数', ordering='total_listened')
    def listened_record_count(self, obj):
        return getattr(obj, 'total_listened', 0)


@admin.register(AudioCleanup)
class AudioCleanupAdmin(CleanAudioDeleteMixin, admin.ModelAdmin):
    change_list_template = 'admin/audios/audiocleanup/change_list.html'
    list_display = ('filename', 'group', 'upload_time', 'listened_record_count')
    list_display_links = None
    list_filter = (UploadTimeOlderThanFilter, 'group')
    search_fields = ('filename', 'group__name')
    ordering = ('-upload_time', '-id')
    actions = ('delete_selected_audios',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('group').annotate(total_listened=Count('listened_users'))

    def changelist_view(self, request, extra_context=None):
        if ERROR_FLAG in request.GET:
            query = request.GET.copy()
            query.pop(ERROR_FLAG, None)
            query.pop('p', None)
            query_string = query.urlencode()
            return HttpResponseRedirect(f'{request.path}?{query_string}' if query_string else request.path)

        extra_context = extra_context or {}
        active_days = request.GET.get('older_than', '')
        query = request.GET.copy()
        query.pop(ERROR_FLAG, None)
        query.pop('p', None)
        query.pop('older_than', None)

        all_query = query.copy()
        filter_links = [
            {
                'label': '全部',
                'url': f'?{all_query.urlencode()}' if all_query else '?',
                'active': active_days == '',
            },
        ]
        for days in ('15', '30', '60', '90'):
            item_query = query.copy()
            item_query['older_than'] = days
            filter_links.append({
                'label': f'{days} 天之前',
                'url': f'?{item_query.urlencode()}',
                'active': active_days == days,
            })

        extra_context['cleanup_filter_links'] = filter_links
        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description='已听记录数')
    def listened_record_count(self, obj):
        return getattr(obj, 'total_listened', 0)


@admin.register(UserListened)
class UserListenedAdmin(admin.ModelAdmin):
    list_display = ('user', 'audio', 'listened_time')
    list_filter = ('audio__group', 'listened_time')
    search_fields = ('user__username', 'audio__filename')
    ordering = ('-listened_time', '-id')
    readonly_fields = ('user', 'audio', 'listened_time')

    def has_add_permission(self, request):
        return False
