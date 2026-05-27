from django.urls import path

from .views import AudioListView, AudioStreamView, ListenedIdsView, ListenedListView, MarkListenedView


urlpatterns = [
    path('audios/', AudioListView.as_view(), name='audio-list'),
    path('audios/<int:pk>/stream/', AudioStreamView.as_view(), name='audio-stream'),
    path('listened/ids/', ListenedIdsView.as_view(), name='listened-ids'),
    path('listened/mark/', MarkListenedView.as_view(), name='listened-mark'),
    path('listened/', ListenedListView.as_view(), name='listened-list'),
]
