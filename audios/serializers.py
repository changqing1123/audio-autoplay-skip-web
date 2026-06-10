from pathlib import Path

from rest_framework import serializers
from django.urls import reverse
from urllib.parse import urlencode

from .models import AUDIO_COVER_MAX_SIZE, Audio, UserListened
from .playback import make_play_token


ALLOWED_COVER_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}


class AudioListSerializer(serializers.ModelSerializer):
    group_cover_url = serializers.SerializerMethodField()
    group_name = serializers.CharField(source='group.name', read_only=True)
    group_weight = serializers.SerializerMethodField()
    play_url = serializers.SerializerMethodField()

    class Meta:
        model = Audio
        fields = ('id', 'filename', 'upload_time', 'duration', 'group_name', 'group_weight', 'group_cover_url', 'play_url')

    def get_group_weight(self, obj):
        profile = getattr(obj.group, 'profile', None)
        return profile.weight if profile else 100

    def get_group_cover_url(self, obj):
        if obj.cover:
            request = self.context.get('request')
            url = obj.cover.url
            return request.build_absolute_uri(url) if request else url
        profile = getattr(obj.group, 'profile', None)
        if not profile or not profile.default_cover:
            return None
        request = self.context.get('request')
        url = profile.default_cover.url
        return request.build_absolute_uri(url) if request else url

    def get_play_url(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return None
        url = '{}?{}'.format(
            reverse('audio-stream', kwargs={'pk': obj.pk}),
            urlencode({'token': make_play_token(request.user, obj)}),
        )
        return request.build_absolute_uri(url)


class UserListenedSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='audio.id', read_only=True)
    filename = serializers.CharField(source='audio.filename', read_only=True)
    upload_time = serializers.DateTimeField(source='audio.upload_time', read_only=True)
    group_name = serializers.CharField(source='audio.group.name', read_only=True)
    group_weight = serializers.SerializerMethodField()
    group_cover_url = serializers.SerializerMethodField()
    play_url = serializers.SerializerMethodField()

    class Meta:
        model = UserListened
        fields = ('id', 'filename', 'upload_time', 'listened_time', 'group_name', 'group_weight', 'group_cover_url', 'play_url')

    def get_group_weight(self, obj):
        profile = getattr(obj.audio.group, 'profile', None)
        return profile.weight if profile else 100

    def get_group_cover_url(self, obj):
        if obj.audio.cover:
            request = self.context.get('request')
            url = obj.audio.cover.url
            return request.build_absolute_uri(url) if request else url
        profile = getattr(obj.audio.group, 'profile', None)
        if not profile or not profile.default_cover:
            return None
        request = self.context.get('request')
        url = profile.default_cover.url
        return request.build_absolute_uri(url) if request else url

    def get_play_url(self, obj):
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            return None
        url = '{}?{}'.format(
            reverse('audio-stream', kwargs={'pk': obj.audio.pk}),
            urlencode({'token': make_play_token(request.user, obj.audio)}),
        )
        return request.build_absolute_uri(url)


class MarkListenedSerializer(serializers.Serializer):
    audio_id = serializers.IntegerField()


class AudioUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    cover = serializers.FileField(required=False, allow_null=True)
    duration = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    filename = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_file(self, value):
        if Path(value.name).suffix.lower() != '.mp3':
            raise serializers.ValidationError('只支持上传 mp3 文件。')
        return value

    def validate_cover(self, value):
        if not value:
            return value
        extension = Path(value.name).suffix.lower()
        if extension not in ALLOWED_COVER_EXTENSIONS:
            raise serializers.ValidationError('封面只支持 jpg、jpeg、png、webp。')
        if value.size > AUDIO_COVER_MAX_SIZE:
            raise serializers.ValidationError('音频图片大小不能超过 100KB。')
        return value

    def validate(self, attrs):
        upload_token = self.context['upload_token']
        file = attrs['file']
        filename = (attrs.get('filename') or Path(file.name).name).strip()
        if not filename:
            raise serializers.ValidationError({'filename': '文件名不能为空。'})
        if Audio.objects.filter(group=upload_token.group, filename=filename).exists():
            raise serializers.ValidationError({'filename': '当前分组下已存在同名音频。'})
        attrs['filename'] = filename
        return attrs

    def create(self, validated_data):
        upload_token = self.context['upload_token']
        display_filename = validated_data['filename']
        audio = Audio.objects.create(
            file=validated_data['file'],
            cover=validated_data.get('cover'),
            duration=validated_data.get('duration'),
            filename=display_filename,
            group=upload_token.group,
        )
        if audio.filename != display_filename:
            audio.filename = display_filename
            audio.save(update_fields=['filename'])
        return audio
