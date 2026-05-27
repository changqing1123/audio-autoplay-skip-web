from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import unquote

from .forms import ManagedGroupForm, ManagedUserChangeForm, ManagedUserCreationForm
from .models import GroupProfile, ManagedGroup, ManagedUser


User = get_user_model()

admin.site.disable_action('delete_selected')

for model in (User, Group):
    try:
        admin.site.unregister(model)
    except admin.sites.NotRegistered:
        pass


class DirectDeleteMixin:
    changelist_url_name = ''

    def delete_view(self, request, object_id, extra_context=None):
        if request.method == 'GET':
            obj = self.get_object(request, unquote(object_id))
            if obj is None:
                return self._get_obj_does_not_exist_redirect(request, self.model._meta, object_id)
            if not self.has_delete_permission(request, obj):
                raise PermissionDenied
            obj_display = str(obj)
            self.log_deletion(request, obj, obj_display)
            self.delete_model(request, obj)
            self.message_user(request, f'已删除：{obj_display}', level=messages.SUCCESS)
            return HttpResponseRedirect(reverse(self.changelist_url_name))
        return super().delete_view(request, object_id, extra_context)

    @admin.action(description='删除所选项')
    def direct_delete_selected(self, request, queryset):
        if not self.has_delete_permission(request):
            raise PermissionDenied
        total = queryset.count()
        for obj in queryset:
            self.log_deletion(request, obj, str(obj))
        self.delete_queryset(request, queryset)
        self.message_user(request, f'已删除 {total} 项', level=messages.SUCCESS)
        return HttpResponseRedirect(reverse(self.changelist_url_name))

    def response_action(self, request, queryset):
        action = request.POST.get('action')
        if action in {'delete_selected', 'direct_delete_selected'}:
            if not self.has_delete_permission(request):
                raise PermissionDenied
            total = queryset.count()
            for obj in queryset:
                self.log_deletion(request, obj, str(obj))
            self.delete_queryset(request, queryset)
            self.message_user(request, f'已删除 {total} 项', level=messages.SUCCESS)
            return HttpResponseRedirect(reverse(self.changelist_url_name))
        return super().response_action(request, queryset)

    def changelist_view(self, request, extra_context=None):
        action = request.POST.get('action')
        if request.method == 'POST' and action in {'delete_selected', 'direct_delete_selected'}:
            if not self.has_delete_permission(request):
                raise PermissionDenied
            selected_ids = request.POST.getlist(ACTION_CHECKBOX_NAME)
            queryset = self.model._default_manager.filter(pk__in=selected_ids)
            total = queryset.count()
            for obj in queryset:
                self.log_deletion(request, obj, str(obj))
            self.delete_queryset(request, queryset)
            self.message_user(request, f'已删除 {total} 项', level=messages.SUCCESS)
            return HttpResponseRedirect(reverse(self.changelist_url_name))
        return super().changelist_view(request, extra_context)


@admin.register(ManagedUser)
class ManagedUserAdmin(DirectDeleteMixin, UserAdmin):
    add_form = ManagedUserCreationForm
    add_form_template = 'admin/accounts/manageduser/add_form.html'
    form = ManagedUserChangeForm
    changelist_url_name = 'admin:accounts_manageduser_changelist'
    actions = ('direct_delete_selected',)
    list_display = ('username', 'business_group_name', 'last_login', 'edit_action')
    list_display_links = None
    list_filter = ('group_membership__group',)
    ordering = ('-date_joined', '-id')
    search_fields = ('username',)
    save_on_top = False
    readonly_fields = ('last_login', 'date_joined')

    fieldsets = (
        ('账号信息', {'fields': ('username', 'business_group')}),
        ('密码设置', {'fields': ('new_password', 'reset_password_to_default')}),
        ('系统信息', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (
            '新增账号',
            {
                'classes': ('wide',),
                'fields': ('username', 'password', 'business_group'),
            },
        ),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.filter(is_staff=False, is_superuser=False).select_related('group_membership__group')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        form._save_group_membership(obj)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context['show_save_and_continue'] = False
        return super().render_change_form(request, context, add, change, form_url, obj)

    def response_add(self, request, obj, post_url_continue=None):
        if '_addanother' in request.POST:
            return super().response_add(request, obj, post_url_continue)
        return HttpResponseRedirect(reverse(self.changelist_url_name))

    def response_change(self, request, obj):
        if '_addanother' in request.POST:
            return super().response_change(request, obj)
        return HttpResponseRedirect(reverse(self.changelist_url_name))

    @admin.display(description='所属分组')
    def business_group_name(self, obj):
        membership = getattr(obj, 'group_membership', None)
        return membership.group.name if membership else '-'

    @admin.display(description='编辑')
    def edit_action(self, obj):
        url = reverse('admin:accounts_manageduser_change', args=[obj.pk])
        return format_html('<a href="{}" style="font-size:14px;">编辑</a>', url)


@admin.register(ManagedGroup)
class ManagedGroupAdmin(DirectDeleteMixin, GroupAdmin):
    form = ManagedGroupForm
    changelist_url_name = 'admin:accounts_managedgroup_changelist'
    actions = ('direct_delete_selected',)
    list_display = ('name', 'member_count', 'weight_display', 'is_default_group_display', 'default_password_display', 'default_cover_preview', 'edit_action')
    list_display_links = None
    search_fields = ('name',)
    ordering = ('name',)
    exclude = ('permissions',)
    save_on_top = False

    fieldsets = (
        ('分组信息', {'fields': ('name', 'weight', 'is_default_group', 'default_password', 'default_cover')}),
    )

    add_fieldsets = (
        (
            '新增分组',
            {
                'classes': ('wide',),
                'fields': ('name', 'weight', 'is_default_group', 'default_password', 'default_cover'),
            },
        ),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(total_members=Count('user_memberships')).select_related('profile')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        default_password = getattr(obj, '_default_password_from_form', None) or form.cleaned_data.get('default_password')
        profile, _ = GroupProfile.objects.get_or_create(
            group=obj,
            defaults={'default_password': default_password},
        )
        profile.default_password = default_password
        profile.is_default_group = getattr(obj, '_is_default_group_from_form', None)
        if profile.is_default_group is None:
            profile.is_default_group = form.cleaned_data.get('is_default_group', False)
        profile.weight = getattr(obj, '_weight_from_form', None) or form.cleaned_data.get('weight') or 100
        update_fields = ['default_password', 'is_default_group', 'weight', 'updated_at']
        default_cover = getattr(obj, '_default_cover_from_form', None) or form.cleaned_data.get('default_cover')
        if default_cover:
            profile.default_cover = default_cover
            update_fields.append('default_cover')
        profile.save(update_fields=update_fields)

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context['show_save_and_continue'] = False
        return super().render_change_form(request, context, add, change, form_url, obj)

    def response_add(self, request, obj, post_url_continue=None):
        if '_addanother' in request.POST:
            return super().response_add(request, obj, post_url_continue)
        return HttpResponseRedirect(reverse(self.changelist_url_name))

    def response_change(self, request, obj):
        if '_addanother' in request.POST:
            return super().response_change(request, obj)
        return HttpResponseRedirect(reverse(self.changelist_url_name))

    @admin.display(description='成员数量')
    def member_count(self, obj):
        return getattr(obj, 'total_members', 0)

    @admin.display(description='权重', ordering='profile__weight')
    def weight_display(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.weight if profile else 100

    @admin.display(description='默认分组', boolean=True)
    def is_default_group_display(self, obj):
        profile = getattr(obj, 'profile', None)
        return bool(profile and profile.is_default_group)

    @admin.display(description='默认密码')
    def default_password_display(self, obj):
        profile = getattr(obj, 'profile', None)
        return profile.default_password if profile and profile.default_password else '-'

    @admin.display(description='默认图片')
    def default_cover_preview(self, obj):
        profile = getattr(obj, 'profile', None)
        if not profile or not profile.default_cover:
            return '-'
        return format_html(
            '<img src="{}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;" />',
            profile.default_cover.url,
        )

    @admin.display(description='编辑')
    def edit_action(self, obj):
        url = reverse('admin:accounts_managedgroup_change', args=[obj.pk])
        return format_html('<a href="{}" style="font-size:14px;">编辑</a>', url)
