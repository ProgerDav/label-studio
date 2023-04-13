from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi as openapi
from io_storages.deeplake.models import DeepLakeImportStorage, DeepLakeExportStorage
from io_storages.deeplake.serializers import DeepLakeImportStorageSerializer, DeepLakeExportStorageSerializer

from io_storages.api import (
    ImportStorageListAPI,
    ImportStorageDetailAPI,
    ImportStorageSyncAPI,
    ExportStorageListAPI,
    ExportStorageDetailAPI,
    ExportStorageSyncAPI,
    ImportStorageValidateAPI,
    ExportStorageValidateAPI,
    ImportStorageFormLayoutAPI,
    ExportStorageFormLayoutAPI,
)


@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=['Storage:DeepLake'],
        operation_summary='Get import storage',
        operation_description='Get a list of all DeepLake import storage connections.',
        manual_parameters=[
            openapi.Parameter(
                name='project',
                type=openapi.TYPE_INTEGER,
                in_=openapi.IN_QUERY,
                description='Project ID',
            ),
        ],
    ),
)
@method_decorator(
    name='post',
    decorator=swagger_auto_schema(
        tags=['Storage:DeepLake'], operation_summary='Create new storage', operation_description='Get new DeepLake import storage'
    ),
)
class DeepLakeImportStorageListAPI(ImportStorageListAPI):
    queryset = DeepLakeImportStorage.objects.all()
    serializer_class = DeepLakeImportStorageSerializer


@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=['Storage:DeepLake'],
        operation_summary='Get import storage',
        operation_description='Get a specific DeepLake import storage connection.',
    ),
)
@method_decorator(
    name='patch',
    decorator=swagger_auto_schema(
        tags=['Storage:DeepLake'],
        operation_summary='Update import storage',
        operation_description='Update a specific DeepLake import storage connection.',
    ),
)
@method_decorator(
    name='delete',
    decorator=swagger_auto_schema(
        tags=['Storage:DeepLake'],
        operation_summary='Delete import storage',
        operation_description='Delete a specific DeepLake import storage connection.',
    ),
)
class DeepLakeImportStorageDetailAPI(ImportStorageDetailAPI):
    queryset = DeepLakeImportStorage.objects.all()
    serializer_class = DeepLakeImportStorageSerializer


@method_decorator(
    name='post',
    decorator=swagger_auto_schema(
        tags=['Storage:DeepLake'],
        operation_summary='Sync import storage',
        operation_description='Sync tasks from an DeepLake import storage connection.',
    ),
)
class DeepLakeImportStorageSyncAPI(ImportStorageSyncAPI):
    serializer_class = DeepLakeImportStorageSerializer


@method_decorator(
    name='post',
    decorator=swagger_auto_schema(
        tags=['Storage:DeepLake'],
        operation_summary='Sync export storage',
        operation_description='Sync tasks from a specific DeepLake export storage connection.',
    ),
)
class DeepLakeExportStorageSyncAPI(ExportStorageSyncAPI):
    serializer_class = DeepLakeExportStorageSerializer


@method_decorator(
    name='post',
    decorator=swagger_auto_schema(
        tags=['Storage:DeepLake'],
        operation_summary='Validate export storage',
        operation_description='Validate a specific DeepLake export storage connection.',
    ),
)
class DeepLakeExportStorageValidateAPI(ExportStorageValidateAPI):
    serializer_class = DeepLakeExportStorageSerializer


@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=['Storage:DeepLake'],
        operation_summary='Get all export storage',
        operation_description='Get a list of all DeepLake export storage connections.',
        manual_parameters=[
            openapi.Parameter(
                name='project',
                type=openapi.TYPE_INTEGER,
                in_=openapi.IN_QUERY,
                description='Project ID',
            ),
        ],
    ),
)
@method_decorator(
    name='post',
    decorator=swagger_auto_schema(
        tags=['Storage: DeepLake'],
        operation_summary='Create export storage',
        operation_description='Create a new DeepLake export storage connection to store annotations.',
    ),
)
class DeepLakeExportStorageListAPI(ExportStorageListAPI):
    queryset = DeepLakeExportStorage.objects.all()
    serializer_class = DeepLakeExportStorageSerializer


@method_decorator(
    name='get',
    decorator=swagger_auto_schema(
        tags=['Storage:DeepLake'],
        operation_summary='Get export storage',
        operation_description='Get a specific DeepLake export storage connection.',
    ),
)
@method_decorator(
    name='patch',
    decorator=swagger_auto_schema(
        tags=['Storage:DeepLake'],
        operation_summary='Update export storage',
        operation_description='Update a specific DeepLake export storage connection.',
    ),
)
@method_decorator(
    name='delete',
    decorator=swagger_auto_schema(
        tags=['Storage:DeepLake'],
        operation_summary='Delete export storage',
        operation_description='Delete a specific DeepLake export storage connection.',
    ),
)
class DeepLakeExportStorageDetailAPI(ExportStorageDetailAPI):
    queryset = DeepLakeExportStorage.objects.all()
    serializer_class = DeepLakeExportStorageSerializer


class DeepLakeImportStorageFormLayoutAPI(ImportStorageFormLayoutAPI):
    pass


@method_decorator(
    name='post',
    decorator=swagger_auto_schema(
        tags=['Storage:DeepLake'],
        operation_summary='Validate import storage',
        operation_description='Validate a specific DeepLake import storage connection.',
    ),
)
class DeepLakeImportStorageValidateAPI(ImportStorageValidateAPI):
    serializer_class = DeepLakeImportStorageSerializer


class DeepLakeExportStorageFormLayoutAPI(ExportStorageFormLayoutAPI):
    pass