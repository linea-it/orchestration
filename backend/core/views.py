import json
import logging
import pathlib

from django.shortcuts import get_object_or_404
from core.utils import get_pipeline, load_config, validate_config, load_executor, get_pipelines
from core.pipeline import Pipeline
from core.models import Process
from core.release_config import ReleaseHatsConfigError, ReleaseHatsConfigRegistry
from core.serializers import (
    ProcessSerializer,
    ProcessSerializerRead,
    ReleaseHatsConfigErrorSerializer,
    ReleaseHatsConfigListSerializer,
    ReleaseHatsConfigQuerySerializer,
    ReleaseHatsConfigSerializer,
)
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope
from django.conf import settings
from rest_framework.views import APIView
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    PolymorphicProxySerializer,
    extend_schema,
)


logger = logging.getLogger("main")


class ProcessViewSet(viewsets.ModelViewSet):
    queryset = Process.objects.all()
    serializer_class = ProcessSerializer
    permission_classes = [TokenHasReadWriteScope]
    http_method_names = ["get", "post", "head", "options"]
    search_fields = [
        "pipeline",
        "user__username",
        "user__first_name",
        "user__last_name",
    ]
    ordering_fields = [
        "id",
        "status",
        "created_at",
        "started_at",
        "ended_at",
    ]
    ordering = ["-created_at"]

    def perform_create(self, serializer):
        user = self.request.user
        if not user:
            user = self.request.auth.application.user
        return serializer.save(user=user)

    def list(self, request):
        queryset = Process.objects.all()
        serializer = ProcessSerializerRead(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Process.objects.all()
        process = get_object_or_404(queryset, pk=pk)
        serializer = ProcessSerializerRead(process)
        return Response(serializer.data)

    def create(self, request):
        try:
            pipeline_data = get_pipeline(request.data["pipeline"])
            pipeline = Pipeline(**pipeline_data)
            logger.info("Starting pipeline processing: %s", pipeline.display_name)
            logger.info("Executor is %s.", pipeline.executor)
            Executor = load_executor(pipeline.executor)
        except Exception as err:
            # TODO: Tratar errors individuais
            logger.error(err)
            content = {"error": f"[pipeline loader] {str(err)}"}
            return Response(content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            used_config = request.data["used_config"]
            assert validate_config(used_config), f"Bad config -> {used_config}"
            if used_config:
                if not isinstance(used_config, dict):
                    used_config = json.loads(used_config)
                used_config = load_config(pipeline.schema_config, used_config)
            else:
                used_config = load_config(pipeline.schema_config)
            used_config = used_config.model_dump()
            logger.info("Configuration is valid.")
        except Exception as err:
            # TODO: Tratar errors individuais
            logger.error(err)
            content = {"error": f"[config loader] {str(err)}"}
            return Response(content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            with transaction.atomic():
                data = {
                    "used_config": json.dumps(used_config),
                    "pipeline": pipeline.name,
                }
                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                instance = self.perform_create(serializer)
                process = Process.objects.get(pk=instance.pk)

                # fill the current pipeline version
                process.pipeline_version = pipeline.version
                process.used_config = json.dumps(used_config)

                # create process path
                path = pathlib.Path(process.pipeline, str(instance.pk).zfill(8))
                process.path = path
                process.executor = pipeline.executor
                process.save()

                executor = Executor(instance.pk)
                task_id = executor.submit()

                process.task_id = task_id
                process.save()
                data = self.get_serializer(instance=process).data
        except Exception as e:
            content = {"error": f"[process register] {str(e)}"}
            return Response(content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.info("Process[%s] submitted!", str(process))
        return Response(data, status=status.HTTP_201_CREATED)

    @action(methods=["Get"], detail=True)
    def status(self, request, **kwargs):
        """Status processing"""

        try:
            instance = self.get_object()
            process = Process.objects.get(pk=instance.pk)
            data = {
                "status": process.get_status_display(),
                "started_at": process.started_at,
                "ended_at": process.ended_at
            }
        except Exception as err:
            content = {"error": str(err)}
            return Response(content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.info("Process[%s]: %s", str(process), data)
        return Response(data, status=status.HTTP_200_OK)

    @action(methods=["Get"], detail=True)
    def finish(self, request, **kwargs):
        """Finish processing"""

        try:
            instance = self.get_object()
            process = Process.objects.get(pk=instance.pk)
            Executor = load_executor(process.executor)
            executor = Executor(process.pk)
            executor.finish()
            data = self.get_serializer(instance=process).data
            code_status = status.HTTP_200_OK
        except Exception as err:
            data = {"error": str(err)}
            code_status = status.HTTP_500_INTERNAL_SERVER_ERROR

        logger.info("Process[%s]: %s", str(process), data)
        return Response(data, status=code_status)

    @action(methods=["Get"], detail=True)
    def stop(self, request, **kwargs):
        """Stop processing"""

        try:
            instance = self.get_object()
            process = Process.objects.get(pk=instance.pk)
            data = self.get_serializer(instance=process).data

            if process.status in (3, 4):
                msg = f"Process[{process}] has already been marked to be stopped."
                logger.info(msg)
                return Response({"message": msg}, status=status.HTTP_200_OK)

            if process.status in (0, 5):
                msg = (
                    f"Process[{process}] has already finished. status={process.status}"
                )
                logger.info(msg)
                return Response({"message": msg}, status=status.HTTP_200_OK)

            Executor = load_executor(process.executor)
            executor = Executor(process.pk)
            executor.stop()
            process.status = 3  # number representing 'revoking' in db
            process.save()
            data = self.get_serializer(instance=process).data
        except Exception as err:
            content = {"error": str(err)}
            return Response(content, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.info("Process[%s] marked to be stopped.", str(process))
        return Response(data, status=status.HTTP_200_OK)


class SystemInformationView(APIView):

    permission_classes = [TokenHasReadWriteScope]
    http_method_names = ["get",]

    def get(self, request):    
        data = {
            'pipelines_dir': settings.PIPELINES_DIR,
            'processing_dir': settings.PROCESSING_DIR,
            'datasets_dir': settings.DATASETS_DIR,
        }
        return Response(data)


class ReleaseHatsConfigView(APIView):
    """Expose HATS manifests stored alongside datasets."""

    permission_classes = [TokenHasReadWriteScope]
    http_method_names = ["get", "head", "options"]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="release",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description=(
                    "Release identifier. When omitted, only summaries for the "
                    "available release configurations are returned."
                ),
            )
        ],
        responses={
            200: PolymorphicProxySerializer(
                component_name="ReleaseHatsConfigResponse",
                serializers=[
                    ReleaseHatsConfigSerializer,
                    ReleaseHatsConfigListSerializer,
                ],
                resource_type_field_name=None,
            ),
            400: ReleaseHatsConfigErrorSerializer,
            404: ReleaseHatsConfigErrorSerializer,
            413: ReleaseHatsConfigErrorSerializer,
            422: ReleaseHatsConfigErrorSerializer,
            500: OpenApiResponse(description="Unexpected server error."),
        },
    )
    def get(self, request):
        query_data = (
            {"release": request.query_params.get("release")}
            if "release" in request.query_params
            else {}
        )
        query = ReleaseHatsConfigQuerySerializer(data=query_data)
        if not query.is_valid():
            error = query.errors.get("release", ["Invalid query parameters."])[0]
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        release = query.validated_data.get("release")
        registry = ReleaseHatsConfigRegistry()

        try:
            if release:
                data = registry.get(release)
                return Response(ReleaseHatsConfigSerializer(data).data)

            data = {"results": registry.list()}
            return Response(ReleaseHatsConfigListSerializer(data).data)
        except ReleaseHatsConfigError as exc:
            logger.warning("Release HATS configuration request failed: %s", exc)
            return Response({"error": str(exc)}, status=exc.status_code)


class PipelinesView(APIView):

    permission_classes = [TokenHasReadWriteScope]
    http_method_names = ["get",]

    def get(self, request):    
        pipelines = get_pipelines()
        return Response({"pipelines": pipelines})
