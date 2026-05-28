from django.contrib.auth import get_user_model
from django.core import signing
from django.core.exceptions import PermissionDenied

PLAY_TOKEN_SALT = 'audios.playback'
PLAY_TOKEN_MAX_AGE_SECONDS = 2 * 60 * 60


def make_play_token(user, audio):
    return signing.dumps(
        {'user_id': user.pk, 'audio_id': audio.pk},
        salt=PLAY_TOKEN_SALT,
    )


def get_user_from_play_token(token, audio_id):
    try:
        payload = signing.loads(
            token,
            salt=PLAY_TOKEN_SALT,
            max_age=PLAY_TOKEN_MAX_AGE_SECONDS,
        )
        if int(payload.get('audio_id')) != int(audio_id):
            raise ValueError
        user_id = int(payload.get('user_id'))
    except (signing.BadSignature, TypeError, ValueError):
        raise PermissionDenied('Invalid audio play token.')

    User = get_user_model()
    try:
        return User.objects.get(pk=user_id, is_active=True)
    except User.DoesNotExist as exc:
        raise PermissionDenied('Invalid audio play token.') from exc
