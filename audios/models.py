import uuid
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models


User = get_user_model()
AUDIO_COVER_MAX_SIZE = 100 * 1024


def audio_upload_to(instance, filename):
    group_part = f'group_{instance.group_id}' if instance.group_id else 'ungrouped'
    extension = Path(filename).suffix.lower() or '.mp3'
    return f'audios/{group_part}/{uuid.uuid4().hex}{extension}'


def audio_cover_upload_to(instance, filename):
    group_part = f'group_{instance.group_id}' if instance.group_id else 'ungrouped'
    extension = Path(filename).suffix.lower() or '.jpg'
    return f'audio_covers/{group_part}/{uuid.uuid4().hex}{extension}'


def validate_audio_cover_size(file):
    if file and file.size > AUDIO_COVER_MAX_SIZE:
        raise ValidationError('音频图片大小不能超过 100KB。')


class Audio(models.Model):
    file = models.FileField(
        upload_to=audio_upload_to,
        validators=[FileExtensionValidator(allowed_extensions=['mp3'])],
        verbose_name='音频文件',
    )
    filename = models.CharField(max_length=255, verbose_name='文件名')
    file_path = models.CharField(max_length=500, verbose_name='文件路径')
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='audios',
        verbose_name='所属分组',
    )
    cover = models.FileField(
        upload_to=audio_cover_upload_to,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp']),
            validate_audio_cover_size,
        ],
        verbose_name='音频图片',
    )
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    file_size = models.BigIntegerField(blank=True, null=True, verbose_name='文件大小(字节)')
    duration = models.PositiveIntegerField(blank=True, null=True, verbose_name='时长(秒)')

    class Meta:
        verbose_name = '音频'
        verbose_name_plural = '音频管理'
        ordering = ('-upload_time', '-id')
        indexes = [
            models.Index(fields=['group', '-upload_time'], name='audio_group_time_idx'),
            models.Index(fields=['-upload_time'], name='audio_upload_time_idx'),
        ]

    def __str__(self):
        return self.filename

    def save(self, *args, **kwargs):
        if self.file:
            if '/' not in self.file.name and '\\' not in self.file.name:
                self.filename = Path(self.file.name).name
            elif not self.filename:
                self.filename = Path(self.file.name).name
            self.file_path = self.file.name
            try:
                self.file_size = self.file.size
            except OSError:
                pass
        super().save(*args, **kwargs)
        if self.file:
            new_path = self.file.name
            updates = []
            if self.file_path != new_path:
                self.file_path = new_path
                updates.append('file_path')
            if updates:
                super().save(update_fields=updates)

    def delete(self, *args, **kwargs):
        storage = self.file.storage if self.file else None
        file_name = self.file.name if self.file else None
        cover_storage = self.cover.storage if self.cover else None
        cover_name = self.cover.name if self.cover else None
        super().delete(*args, **kwargs)
        if storage and file_name:
            storage.delete(file_name)
        if cover_storage and cover_name:
            cover_storage.delete(cover_name)


class AudioCleanup(Audio):
    class Meta:
        proxy = True
        verbose_name = '音频清理'
        verbose_name_plural = '音频清理'


class UserListened(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='listened_audios',
        verbose_name='用户',
    )
    audio = models.ForeignKey(
        Audio,
        on_delete=models.CASCADE,
        related_name='listened_users',
        verbose_name='音频',
    )
    listened_time = models.DateTimeField(auto_now_add=True, verbose_name='听完时间')

    class Meta:
        verbose_name = '已听记录'
        verbose_name_plural = '已听记录'
        ordering = ('-listened_time', '-id')
        constraints = [
            models.UniqueConstraint(fields=['user', 'audio'], name='user_audio_listened_unique'),
        ]
        indexes = [
            models.Index(fields=['user', '-listened_time'], name='user_listened_time_idx'),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.audio.filename}'
