import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models


User = get_user_model()
GROUP_COVER_MAX_SIZE = 100 * 1024


def group_default_cover_upload_to(instance, filename):
    group_part = f'group_{instance.group_id}' if instance.group_id else 'ungrouped'
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
    return f'group_covers/{group_part}/{uuid.uuid4().hex}.{extension}'


def validate_group_cover_size(file):
    if file and file.size > GROUP_COVER_MAX_SIZE:
        raise ValidationError('分组默认图片大小不能超过 100KB。')


class ManagedUser(User):
    class Meta:
        proxy = True
        verbose_name = '账号'
        verbose_name_plural = '账号管理'


class ManagedGroup(Group):
    class Meta:
        proxy = True
        verbose_name = '分组'
        verbose_name_plural = '分组管理'


class GroupProfile(models.Model):
    group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Group',
    )
    default_password = models.CharField(
        max_length=128,
        default=settings.ADMIN_DEFAULT_PASSWORD,
        verbose_name='Default Password',
    )
    default_cover = models.FileField(
        upload_to=group_default_cover_upload_to,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp']),
            validate_group_cover_size,
        ],
        verbose_name='Audio Default Image',
    )
    is_default_group = models.BooleanField(default=False, verbose_name='Default Group')
    weight = models.PositiveIntegerField(default=100, verbose_name='Weight')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        verbose_name = '分组配置'
        verbose_name_plural = '分组配置'

    def __str__(self):
        return f'{self.group.name} profile'


class UserGroupMembership(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_membership',
        verbose_name='User',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='user_memberships',
        verbose_name='Group',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

    class Meta:
        verbose_name = '用户分组关系'
        verbose_name_plural = '用户分组关系'
        ordering = ('user_id',)

    def __str__(self):
        return f'{self.user.username} -> {self.group.name}'
