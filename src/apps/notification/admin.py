from django.contrib import admin

from apps.notification.models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    pass
