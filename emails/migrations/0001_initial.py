# Generated by Django 4.2.1 on 2024-11-18 06:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Email',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Last Modified At')),
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('from_email', models.EmailField(max_length=200)),
                ('to_email', models.EmailField(max_length=200)),
                ('subject', models.CharField(max_length=200)),
                ('message', models.CharField(max_length=200)),
                ('file', models.FileField(null=True, upload_to='files/')),
                ('send_time', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(default='sent', max_length=200)),
                ('important', models.BooleanField(default=False, max_length=10)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created_by', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated_by', to=settings.AUTH_USER_MODEL, verbose_name='Last Modified By')),
            ],
            options={
                'verbose_name': 'Email',
                'verbose_name_plural': 'Emails',
                'db_table': 'email',
                'ordering': ('-created_at',),
            },
        ),
    ]
