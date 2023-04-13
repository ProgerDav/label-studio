import os

from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.mixins import UpdateModelMixin
from botocore.exceptions import ParamValidationError, ClientError
from io_storages.serializers import ImportStorageSerializer, ExportStorageSerializer
from io_storages.deeplake.models import DeepLakeImportStorage, DeepLakeExportStorage


class DeepLakeImportStorageSerializer(ImportStorageSerializer):
    type = serializers.ReadOnlyField(default=os.path.basename(os.path.dirname(__file__)))
    
    class Meta:
        model = DeepLakeImportStorage
        fields = '__all__'

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result.pop('activeloop_token')
        return result
    
    def validate(self, data):
        data = super(DeepLakeImportStorageSerializer, self).validate(data)
        if not data.get('dataset_path', None):
            return data
        
        storage = self.instance
        storage = self.instance
        if storage:
            for key, value in data.items():
                setattr(storage, key, value)
        else:
            storage = DeepLakeImportStorage(**data)

        storage.validate_connection()
        
        return data



class DeepLakeExportStorageSerializer(ExportStorageSerializer):
    type = serializers.ReadOnlyField(default=os.path.basename(os.path.dirname(__file__)))
    
    class Meta:
        model = DeepLakeExportStorage
        fields = '__all__'

    def to_representation(self, instance):
        result = super().to_representation(instance)
        result.pop('activeloop_token')
        return result
    
    def validate(self, data):
        return data

