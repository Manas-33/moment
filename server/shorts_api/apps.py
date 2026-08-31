from django.apps import AppConfig
import os


class ShortsApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shorts_api'

    def ready(self):
        # Create necessary directories
        media_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'media')
        if not os.path.exists(media_dir):
            os.makedirs(media_dir)
            
        videos_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'videos')
        if not os.path.exists(videos_dir):
            os.makedirs(videos_dir)
