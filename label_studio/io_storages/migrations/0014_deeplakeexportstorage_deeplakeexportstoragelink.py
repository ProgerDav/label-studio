# Generated by Django 3.2.16 on 2023-04-04 05:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0021_merge_20230215_1943'),
        ('tasks', '0038_auto_20230209_1412'),
        ('io_storages', '0013_deeplakeimportstoragelink'),
    ]

    operations = [
        migrations.CreateModel(
            name='DeepLakeExportStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, help_text='Cloud storage title', max_length=256, null=True, verbose_name='title')),
                ('description', models.TextField(blank=True, help_text='Cloud storage description', null=True, verbose_name='description')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Creation time', verbose_name='created at')),
                ('last_sync', models.DateTimeField(blank=True, help_text='Last sync finished time', null=True, verbose_name='last sync')),
                ('last_sync_count', models.PositiveIntegerField(blank=True, help_text='Count of tasks synced last time', null=True, verbose_name='last sync count')),
                ('last_sync_job', models.CharField(blank=True, help_text='Last sync job ID', max_length=256, null=True, verbose_name='last_sync_job')),
                ('can_delete_objects', models.BooleanField(blank=True, help_text='Deletion from storage enabled', null=True, verbose_name='can_delete_objects')),
                ('dataset_path', models.TextField(blank=True, help_text='DeepLake dataset path', null=True, verbose_name='dataset_path')),
                ('source_tensor_name', models.TextField(blank=True, help_text='Name of the tensor containing the source data', null=True, verbose_name='source_tensor_name')),
                ('activeloop_token', models.TextField(blank=True, help_text='Activeloop token', null=True, verbose_name='activeloop_token')),
                ('project', models.ForeignKey(help_text='A unique integer value identifying this project.', on_delete=django.db.models.deletion.CASCADE, related_name='io_storages_deeplakeexportstorages', to='projects.project')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DeepLakeExportStorageLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_exists', models.BooleanField(default=True, help_text='Whether object under external link still exists', verbose_name='object exists')),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text='Creation time', verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, help_text='Update time', verbose_name='updated at')),
                ('annotation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='io_storages_deeplakeexportstoragelink', to='tasks.annotation')),
                ('storage', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='links', to='io_storages.deeplakeexportstorage')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
