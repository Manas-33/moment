from django.urls import path
from .views import ShortsGeneratorView, VideoProcessingStatusView, UserVideosView, LanguageDubbingView, DubbingStatusView, UserDubbingsView

urlpatterns = [
    path('shorts/', ShortsGeneratorView.as_view(), name='generate-shorts'),
    path('shorts/status/<int:processing_id>/', VideoProcessingStatusView.as_view(), name='processing-status'),
    path('shorts/user/', UserVideosView.as_view(), name='user-videos'),

    # Language dubbing endpoints
    path('dubbing/', LanguageDubbingView.as_view(), name='dub-video'),
    path('dubbing/status/<int:dubbing_id>/', DubbingStatusView.as_view(), name='dubbing-status'),
    path('dubbing/user/', UserDubbingsView.as_view(), name='user-dubbings'),
    # Social media uploads (Instagram, etc.) are intentionally disabled in
    # local mode. Re-enable the route in views.py when needed.
]
