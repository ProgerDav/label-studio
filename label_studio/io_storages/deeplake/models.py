import re
import logging
import json
import deeplake
import numpy as np
import django_rq

from core.redis import start_job_async_or_sync
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete
from django_rq import job
from core.redis import is_job_in_queue, redis_connected, is_job_on_worker

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
        ds = deeplake.load(
            self.dataset_path,
            token=self.activeloop_token,
            read_only=read_only,
            verbose=False,
        )
        return ds

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

    url_scheme = "hub"

    def iterkeys(self):
        client = self.get_dataset()
        for i in range(client[self.source_tensor_name].num_samples):
            yield str(i)

    def validate_connection(self, client=None):
        if client is None:
            client = self.get_dataset()

        if self.source_tensor_name not in client.tensors:
            raise KeyError(
                f'Tensor "{self.source_tensor_name}" not found in dataset "{self.dataset_path}"'
            )

    def get_data(self, key):
        return {
            settings.DATA_UNDEFINED_NAME: f"/data/deeplake-files/?key={key}&storage_id={self.pk}"
        }

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

    def save_annotation_old(self, annotation, token: str, dataset=None):
        from requests import get

        ser_annotation = self._get_serialized_data(annotation)

        if dataset is None:
            dataset = self.get_dataset(read_only=False)

        logger.debug(
            f"Creating new object on {self.__class__.__name__} Storage {self} for annotation {annotation}"
        )
        with dataset:
            task = ser_annotation["task"]
            image_url = task["data"][self.source_key]
            sample = deeplake.read(settings.HOSTNAME + image_url)
            dataset[self.destination_tensor].append(sample)

            all_results = []
            all_polygons = []
            all_labels = []
            for result in ser_annotation["result"]:
                all_results.append(result)
                if result["type"] == "polygonlabels":
                    points = result["value"]["points"]
                    points = np.array(points, dtype="float32")
                    label = result["value"]["polygonlabels"][0]
                    all_polygons.append(points)
                    all_labels.append(label)

            dataset["polygons"].append(all_polygons)
            dataset["labels"].append(all_labels)
            dataset["annotations"].append(json.dumps(all_results))

        dataset._unlock()
        # get key that identifies this object in storage
        key = DeepLakeExportStorageLink.get_key(annotation)

        # create link if everything ok
        DeepLakeExportStorageLink.create(annotation, self)

    def _process_image_url(self, image_url: str):
        prefix = "/data/deeplake-files/"
        if not image_url.startswith(prefix):
            raise ValueError(f"Unsupported protocol for sample url in {image_url}")

        uri = image_url[len(prefix) :]
        parts = uri.split("/")
        assert len(parts) == 7, f"Unsupported sample url in {image_url}"

        _, _, org, ds, tensor, _, key = parts

        return f"{org}/{ds}", tensor, int(key)

    def _handle_non_same_dataset(self, dataset: deeplake.Dataset, image_url: str):
        dataset_id, tensor, key = self._process_image_url(image_url)

        sample = deeplake.read(settings.HOSTNAME + image_url)
        if tensor not in dataset.tensors:
            dataset.create_tensor(tensor, htype="image", sample_compression="jpeg")

        dataset[tensor].append(sample)

    def save_annotation(self, annotation, token: str = "", dataset=None):
        ser_annotation = self._get_serialized_data(annotation)
        if dataset is None:
            dataset = self.get_dataset(read_only=False)

        logger.debug(
            f"Creating new object on {self.__class__.__name__} Storage {self} for annotation {annotation}"
        )

        task = ser_annotation["task"]
        image_url = task["data"][self.source_key]
        dataset_id, tensor, key = self._process_image_url(image_url)
        is_same_dataset = dataset_id in self.dataset_path

        if not is_same_dataset:
            self._handle_non_same_dataset(dataset, key)

        if self.destination_tensor not in dataset.tensors:
            dataset.create_tensor(self.destination_tensor, htype="json")

        objects = []
        width = ser_annotation["result"][0]["original_width"]
        height = ser_annotation["result"][0]["original_height"]
        for id, result in enumerate(ser_annotation["result"]):
            if result["type"] == "polygonlabels":
                points = result["value"]["points"]
                label = result["value"]["polygonlabels"][0]
                objects.append(
                    {
                        "id": id,
                        "label": label,
                        "polygon": points,
                    }
                )

        json_data = {"objects": objects, "width": width, "height": height}

        if is_same_dataset:
            dataset[self.destination_tensor][key] = json_data
        else:
            dataset[self.destination_tensor].append(json_data)

        # get key that identifies this object in storage
        key = DeepLakeExportStorageLink.get_key(annotation)

        # create link if everything ok
        DeepLakeExportStorageLink.create(annotation, self)

    def save_all_annotations(self, token: str):
        annotation_exported = 0
        dataset = self.get_dataset(read_only=False)

        with dataset:
            for annotation in Annotation.objects.filter(project=self.project):
                self.save_annotation(annotation, token, dataset)
                annotation_exported += 1

        dataset._unlock()
        self.last_sync = timezone.now()
        self.last_sync_count = annotation_exported
        self.save()

    def sync(self, token: str = ""):
        if redis_connected():
            queue = django_rq.get_queue("low")
            job = queue.enqueue(
                export_sync_background,
                self.__class__,
                self.id,
                job_timeout=settings.RQ_LONG_JOB_TIMEOUT,
            )
            logger.info(
                f"Storage sync background job {job.id} for storage {self} has been started"
            )
        else:
            logger.info(f"Start syncing storage {self}")
            self.save_all_annotations(token)


@job("low", timeout=settings.RQ_LONG_JOB_TIMEOUT)
def export_sync_background(storage_class, storage_id):
    storage = storage_class.objects.get(id=storage_id)
    storage.save_all_annotations()


class DeepLakeImportStorageLink(ImportStorageLink):
    storage = models.ForeignKey(
        DeepLakeImportStorage, on_delete=models.CASCADE, related_name="links"
    )


class DeepLakeExportStorageLink(ExportStorageLink):
    storage = models.ForeignKey(
        DeepLakeExportStorage, on_delete=models.CASCADE, related_name="links"
    )


def parse_json(json_path, label_studio_url, label_studio_token):
    file = open(json_path)
    json_file = json.load(file)
    for image in json_file:
        file_name = image["image"].split("-", 1)[1].rsplit(".", 1)[0]
        objects = []
        height = image["label"][0]["original_height"]
        width = image["label"][0]["original_width"]
        for index, label in enumerate(image["label"]):
            object = {}
            object["id"] = index
            object["label"] = label["polygonlabels"][0]
            object["polygon"] = label["points"]
            objects.append(object)

        json_data = {"objects": objects, "height": height, "width": width}

        downloaded_image = get_image(
            label_studio_url + image["image"], label_studio_token
        )
        os.makedirs("labeled_data", exist_ok=True)
        with open(f"labeled_data/{file_name}.jpg", "wb") as f:
            f.write(downloaded_image)
        with open(f"labeled_data/{file_name}.json", "w") as f:
            f.write(json.dumps(json_data, indent=2))
