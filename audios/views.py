from django.http import FileResponse, Http404
from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserGroupMembership

from .models import Audio, UserListened
from .serializers import AudioListSerializer, MarkListenedSerializer, UserListenedSerializer


def api_success(data=None, message='success', status_code=status.HTTP_200_OK):
    return Response({'code': status_code, 'message': message, 'data': data}, status=status_code)


def get_user_group(user):
    membership = (
        UserGroupMembership.objects.select_related('group')
        .filter(user=user)
        .first()
    )
    return membership.group if membership else None


def accessible_audio_filter(user):
    group = get_user_group(user)
    query = Q(group__profile__is_default_group=True)
    if group:
        query |= Q(group=group)
    return query


def accessible_listened_filter(user):
    group = get_user_group(user)
    query = Q(audio__group__profile__is_default_group=True)
    if group:
        query |= Q(audio__group=group)
    return query


def get_group_audio_or_404(user, audio_id):
    try:
        return Audio.objects.select_related('group', 'group__profile').get(
            Q(pk=audio_id) & accessible_audio_filter(user),
        )
    except Audio.DoesNotExist as exc:
        raise Http404('Audio not found.') from exc


class AudioListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AudioListSerializer

    def get_queryset(self):
        return (
            Audio.objects.filter(accessible_audio_filter(self.request.user))
            .select_related('group', 'group__profile')
            .distinct()
            .order_by('-upload_time', '-id')
        )

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return api_success(serializer.data)


class AudioStreamView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        audio = get_group_audio_or_404(request.user, pk)
        if not audio.file:
            raise Http404('Audio file not found.')
        return FileResponse(audio.file.open('rb'), as_attachment=False, filename=audio.filename)


class ListenedIdsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        listened_ids = list(
            UserListened.objects.filter(user=request.user)
            .filter(accessible_listened_filter(request.user))
            .distinct()
            .values_list('audio_id', flat=True)
        )
        return api_success(listened_ids)


class MarkListenedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MarkListenedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        audio = get_group_audio_or_404(request.user, serializer.validated_data['audio_id'])
        UserListened.objects.get_or_create(user=request.user, audio=audio)
        return api_success(None, message='标记成功')


class ListenedListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserListenedSerializer

    def get_queryset(self):
        return (
            UserListened.objects.select_related('audio', 'audio__group', 'audio__group__profile')
            .filter(user=self.request.user)
            .filter(accessible_listened_filter(self.request.user))
            .distinct()
            .order_by('-listened_time', '-id')
        )

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return api_success(serializer.data)
