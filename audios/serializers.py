from rest_framework import serializers
from django.urls import reverse
from urllib.parse import urlencode

from .models import Audio, UserListened
from .playback import make_play_token


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
