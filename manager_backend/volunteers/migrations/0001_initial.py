# Generated by Django 5.1.7 on 2025-05-10 23:33

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tasks", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Volunteer",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "coordinator_volunteer_id",
                    models.CharField(max_length=255, unique=True),
                ),
                ("name", models.CharField(max_length=255)),
                ("hostname", models.CharField(max_length=255)),
                ("last_ip_address", models.GenericIPAddressField()),
                ("cpu_cores", models.IntegerField()),
                ("ram_mb", models.IntegerField()),
                ("gpu", models.BooleanField(default=False)),
                ("available", models.BooleanField(default=True)),
                ("status", models.CharField(default="available", max_length=20)),
                ("ip_address", models.GenericIPAddressField()),
                ("last_seen", models.DateTimeField(auto_now=True)),
                ("disk_gb", models.IntegerField()),
                ("tags", models.JSONField(blank=True, default=list)),
                ("meta_info", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "verbose_name": "Volontaire",
                "verbose_name_plural": "Volontaires",
                "ordering": ["hostname"],
            },
        ),
        migrations.CreateModel(
            name="VolunteerTask",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "assigned_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("progress", models.FloatField(default=0)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ASSIGNED", "Assigned"),
                            ("STARTED", "Started"),
                            ("COMPLETED", "Completed"),
                            ("FAILED", "Failed"),
                            ("EXPIRED", "Expired"),
                        ],
                        default="ASSIGNED",
                        max_length=20,
                    ),
                ),
                ("result", models.JSONField(blank=True, null=True)),
                ("error", models.TextField(blank=True, null=True)),
                (
                    "task",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="volunteer_tasks",
                        to="tasks.task",
                    ),
                ),
                (
                    "volunteer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assigned_tasks",
                        to="volunteers.volunteer",
                    ),
                ),
            ],
            options={
                "unique_together": {("task", "volunteer")},
            },
        ),
    ]
