from core.models import Process
from rest_framework import serializers
import json


class ProcessSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    path_str = serializers.SerializerMethodField()


    class Meta:
        model = Process
        # fields = '__all__'
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
            "path_str",
        )
        exclude = ["path"]

    def get_owner(self, obj):
        return obj.user.username

    def get_path_str(self, obj):
        return str(obj.path)


class ProcessSerializerRead(ProcessSerializer):
    used_config = serializers.SerializerMethodField()

    def get_used_config(self, obj):
        config = obj.used_config
        if not config: return dict()
        return json.loads(config)


class ReleaseHatsConfigQuerySerializer(serializers.Serializer):
    release = serializers.CharField(required=False, allow_blank=False, max_length=255)


class ReleaseHatsConfigSummarySerializer(serializers.Serializer):
    release = serializers.CharField()
    last_modified = serializers.DateTimeField()


class ReleaseHatsConfigSerializer(ReleaseHatsConfigSummarySerializer):
    config = serializers.JSONField()


class ReleaseHatsConfigListSerializer(serializers.Serializer):
    results = ReleaseHatsConfigSummarySerializer(many=True)


class ReleaseHatsConfigErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
