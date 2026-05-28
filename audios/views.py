import re
from urllib.parse import urlencode

from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.urls import reverse
from rest_framework import permissions, status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserGroupMembership

from .models import Audio, UserListened
from .playback import PLAY_TOKEN_MAX_AGE_SECONDS, get_user_from_play_token, make_play_token
from .serializers import AudioListSerializer, MarkListenedSerializer, UserListenedSerializer


RANGE_RE = re.compile(r'^bytes=(\d*)-(\d*)$')
STREAM_CHUNK_SIZE = 64 * 1024


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


def get_stream_user(request, audio_id):
    token = request.query_params.get('token')
    if token:
        return get_user_from_play_token(token, audio_id)
    if request.user and request.user.is_authenticated:
        return request.user
    raise PermissionDenied('Audio play token is required.')


def parse_range_header(range_header, file_size):
    if not range_header:
        return None

    match = RANGE_RE.match(range_header.strip())
    if not match:
        return None

    start_text, end_text = match.groups()
    if not start_text and not end_text:
        return None

    if start_text:
        start = int(start_text)
        end = int(end_text) if end_text else file_size - 1
    else:
        suffix_length = int(end_text)
        if suffix_length == 0:
            return None
        start = max(file_size - suffix_length, 0)
        end = file_size - 1

    if start >= file_size or start > end:
        return 'unsatisfiable'

    return start, min(end, file_size - 1)


def ranged_file_iterator(file_obj, start, length):
    try:
        file_obj.seek(start)
        remaining = length
        while remaining > 0:
            chunk = file_obj.read(min(STREAM_CHUNK_SIZE, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk
    finally:
        file_obj.close()


def set_audio_stream_headers(response, file_size):
    response['Accept-Ranges'] = 'bytes'
    response['Content-Type'] = 'audio/mpeg'
    response['Cache-Control'] = 'private, no-store'
    response['X-Accel-Buffering'] = 'no'
    response['Content-Length'] = str(file_size)
    return response


def build_audio_stream_response(audio, request):
    file_size = audio.file.size
    range_result = parse_range_header(request.headers.get('Range'), file_size)

    if range_result == 'unsatisfiable':
        response = HttpResponse(status=416)
        response['Content-Range'] = f'bytes */{file_size}'
        response['Accept-Ranges'] = 'bytes'
        return response

    if range_result:
        start, end = range_result
        length = end - start + 1
        response = StreamingHttpResponse(
            ranged_file_iterator(audio.file.open('rb'), start, length),
            status=206,
            content_type='audio/mpeg',
        )
        response['Accept-Ranges'] = 'bytes'
        response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        response['Content-Length'] = str(length)
        response['Cache-Control'] = 'private, no-store'
        response['X-Accel-Buffering'] = 'no'
        return response

    response = FileResponse(
        audio.file.open('rb'),
        as_attachment=False,
        filename=audio.filename,
        content_type='audio/mpeg',
    )
    return set_audio_stream_headers(response, file_size)


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


class AudioPlayUrlView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        audio = get_group_audio_or_404(request.user, pk)
        if not audio.file:
            raise Http404('Audio file not found.')

        stream_url = '{}?{}'.format(
            reverse('audio-stream', kwargs={'pk': audio.pk}),
            urlencode({'token': make_play_token(request.user, audio)}),
        )
        response = api_success({
            'stream_url': stream_url,
            'expires_in': PLAY_TOKEN_MAX_AGE_SECONDS,
        })
        response['Cache-Control'] = 'no-store'
        return response


class AudioStreamView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        user = get_stream_user(request, pk)
        audio = get_group_audio_or_404(user, pk)
        if not audio.file:
            raise Http404('Audio file not found.')
        return build_audio_stream_response(audio, request)


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
