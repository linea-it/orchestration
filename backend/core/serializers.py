from core.models import Process, ProcessStatus
from rest_framework import serializers
import json


class ProcessSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()


    class Meta:
        model = Process
        read_only_fields = (
            "pipeline_version",
            "started_at",
            "ended_at",
            "status",
            "user",
            "executor",
            "worker",
            "task_id",
            "pid",
            "comment",
        )
        exclude = ["path"]

    def get_owner(self, obj):
        return obj.user.username


class ProcessSerializerRead(ProcessSerializer):
    used_config = serializers.SerializerMethodField()

    def get_used_config(self, obj):
        config = obj.used_config
        if not config: return dict()
        return json.loads(config)