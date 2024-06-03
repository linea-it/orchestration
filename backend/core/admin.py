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

    exclude = ["path"]

    search_fields = ("pipeline",)
