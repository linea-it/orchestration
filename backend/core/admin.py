from django.contrib import admin
from core.models import Process


@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "pipeline",
        "status",
        "user",
    )

    search_fields = ("pipeline",)
