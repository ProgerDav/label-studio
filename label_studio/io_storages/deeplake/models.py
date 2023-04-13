import re
import logging
import json
import deeplake
import numpy as np

from core.redis import start_job_async_or_sync
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete

from tasks.validation import ValidationError as TaskValidationError
from tasks.models import Annotation
from io_storages.base_models import (
    ExportStorage,
    ExportStorageLink,
    ImportStorage,
    ImportStorageLink,
    ProjectStorageMixin,
)

logger = logging.getLogger(__name__)
# logging.getLogger('deeplake').setLevel(logging.CRITICAL)


class DeepLakeStorageMixin(models.Model):
    dataset_path = models.TextField(
        _("dataset_path"), null=True, blank=True, help_text="DeepLake dataset path"
    )
    activeloop_token = models.TextField(
        _("activeloop_token"), null=True, blank=True, help_text="Activeloop token"
    )

    def get_dataset(self, read_only=True):
        return deeplake.load(
            self.dataset_path,
            token="eyJhbGciOiJIUzUxMiIsImlhdCI6MTY4MDAwNTU3MiwiZXhwIjoxNjg1NTM1MTIwfQ.eyJpZCI6InByb2dlcmRhdiJ9.1HKf6qCNn-3JzODXsxlaBjyz-ipcDymyXKCWl3QbmtErYKf9dy_6M6LwNaGm5uJ6rhveO-YCDME8pY_fpflvOQ",
            read_only=read_only,
            verbose=False,
        )

    def get_source_tensor(self):
        return self.get_dataset()[self.source_tensor_name]

    @property
    def path_full(self):
        return self.dataset_path

    @property
    def type_full(self):
        return "Deep Lake"

    class Meta:
        abstract = True


class DeepLakeImportStorageBase(DeepLakeStorageMixin, ImportStorage):
    source_tensor_name = models.TextField(
        _("source_tensor_name"),
        null=True,
        blank=True,
        help_text="Name of the tensor containing the source data",
    )
    server_base_url = models.TextField(
        _("server_base_url"),
        null=True,
        blank=True,
        help_text="Base URL of the server",
    )

    url_scheme = "hub"

    def iterkeys(self):
        for i in range(10):
            yield str(i)

    def validate_connection(self, client=None):
        if client is None:
            client = self.get_dataset()

        if self.source_tensor_name not in client.tensors:
            raise KeyError(
                f'Tensor "{self.source_tensor_name}" not found in dataset "{self.dataset_path}"'
            )

    def get_data(self, key):
        org, ds = self.dataset_path[6:].split("/")
        base_url = self.server_base_url
        if base_url.endswith("/"):
            base_url = base_url[:-1]

        template = (
            f"{base_url}/api/dataset/{org}/{ds}/{self.source_tensor_name}/data/{key}"
        )
        return {settings.DATA_UNDEFINED_NAME: template}

    # def generate_http_url(self, url):
    #     return GCS.generate_http_url(
    #         url=url,
    #         google_application_credentials=self.google_application_credentials,
    #         google_project_id=self.google_project_id,
    #         presign_ttl=self.presign_ttl
    #     )

    def scan_and_create_links(self):
        return self._scan_and_create_links(DeepLakeImportStorageLink)

    class Meta:
        abstract = True


class DeepLakeImportStorage(ProjectStorageMixin, DeepLakeImportStorageBase):
    class Meta:
        abstract = False


class DeepLakeExportStorage(DeepLakeStorageMixin, ExportStorage):
    source_key = models.TextField(
        _("source_key"), null=True, blank=True, help_text="Key of the source Task JSON"
    )
    destination_tensor = models.TextField(
        _("destination_tensor"),
        null=True,
        blank=True,
        help_text="Name of the tensor to store the data in",
    )

    def save_annotation(self, annotation):
        dataset = self.get_dataset(read_only=False)
        logger.debug(
            f"Creating new object on {self.__class__.__name__} Storage {self} for annotation {annotation}"
        )
        ser_annotation = self._get_serialized_data(annotation)
        image_url = ser_annotation[self.source_key]
        parts = image_url.split("/")[3:]
        org_id = parts[2]
        dataset_name = parts[3]
        tensor_name = parts[4]
        key = parts[6]
        dataset_path = f"hub://{org_id}/{dataset_name}"

        if self.dataset_path != dataset_path:
            raise Exception("Dataset path mismatch")

        if self.destination_tensor not in dataset.tensors:
            dataset.create_tensor(self.destination_tensor, htype="polygon")

        if "labels" not in dataset.tensors:
            dataset.create_tensor("labels", htype="class_label")

        print("annotation: ", ser_annotation)

        dataset[self.destination_tensor].append(ser_annotation[self.source_key])
        for ann in ser_annotation["annotations"]:
            for result in ann["result"]:
                if result["type"] == "polygonlabels":
                    points = result["value"]["points"]
                    points = np.array(points, dtype="uint16")
                    labels = result["value"]["polygonlabels"]

                    print(labels)

            dataset[self.destination_tensor][key] = [points]
            dataset.labels[key] = labels

        if "json" not in dataset.tensors:
            dataset.create_tensor("json", htype="json")

        # get key that identifies this object in storage
        key = DeepLakeExportStorageLink.get_key(annotation)
        dataset.json.append(json.dumps(ser_annotation))
        # key = str(self.prefix) + '/' + key if self.prefix else key

        # # put object into storage
        # s3.Object(self.bucket, key).put(Body=json.dumps(ser_annotation))

        # create link if everything ok
        DeepLakeExportStorageLink.create(annotation, self)

    # def delete_annotation(self, annotation):
    #     client, s3 = self.get_client_and_resource()
    #     logger.debug(f'Deleting object on {self.__class__.__name__} Storage {self} for annotation {annotation}')

    #     # get key that identifies this object in storage
    #     key = S3ExportStorageLink.get_key(annotation)
    #     key = str(self.prefix) + '/' + key if self.prefix else key

    #     # delete object from storage
    #     s3.Object(self.bucket, key).delete()

    #     # delete link if everything ok
    #     S3ExportStorageLink.objects.filter(storage=self, annotation=annotation).delete()


class DeepLakeImportStorageLink(ImportStorageLink):
    storage = models.ForeignKey(
        DeepLakeImportStorage, on_delete=models.CASCADE, related_name="links"
    )


class DeepLakeExportStorageLink(ExportStorageLink):
    storage = models.ForeignKey(
        DeepLakeExportStorage, on_delete=models.CASCADE, related_name="links"
    )
