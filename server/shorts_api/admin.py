from django.contrib import admin
from .models import VideoProcessing

@admin.register(VideoProcessing)
class VideoProcessingAdmin(admin.ModelAdmin):
    list_display = ('id', 'youtube_url', 'status', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('youtube_url', 'error_message')
    readonly_fields = ('created_at', 'updated_at')
