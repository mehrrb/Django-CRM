from rest_framework import serializers
from .models import Task
from common.serializers import (
    ProfileSerializer,
    OrganizationSerializer,
    CommentSerializer,
    AttachmentSerializer,
    UserSerializer
)
from accounts.serializers import AccountSerializer
from teams.serializers import TeamsSerializer
from tasks.utils import PRIORITY_CHOICES, STATUS_CHOICES

class TaskSerializer(serializers.ModelSerializer):
    created_by = ProfileSerializer(read_only=True)
    org = OrganizationSerializer(read_only=True)
    assigned_to = ProfileSerializer(many=True, read_only=True)
    contacts = serializers.SerializerMethodField()
    teams = TeamsSerializer(many=True, read_only=True)
    completed_by = ProfileSerializer(read_only=True)
    task_attachments = AttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = (
            'id',
            'title',
            'description',
            'status',
            'priority',
            'due_date',
            'created_by',
            'created_at',
            'modified_at',
            'org',
            'assigned_to',
            'contacts',
            'teams',
            'completed_by',
            'completed_at',
            'task_attachments',
            'is_active'
        )
        read_only_fields = (
            'id',
            'created_by',
            'created_at',
            'modified_at',
            'completed_by',
            'completed_at',
            'org'
        )

    def get_contacts(self, obj):
        from contacts.serializers import ContactSerializer
        return ContactSerializer(obj.contacts.all(), many=True).data

class TaskCreateSerializer(serializers.ModelSerializer):
    assigned_to = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    contacts = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    teams = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False
    )

    class Meta:
        model = Task
        fields = (
            'title',
            'description',
            'status',
            'priority',
            'due_date',
            'assigned_to',
            'contacts',
            'teams',
            'attachments'
        )

    def validate_title(self, value):
        if Task.objects.filter(
            title__iexact=value,
            org=self.context['request'].profile.org
        ).exists():
            raise serializers.ValidationError(
                "Task with this title already exists"
            )
        return value

    def validate_due_date(self, value):
        from django.utils import timezone
        if value and value < timezone.now().date():
            raise serializers.ValidationError(
                "Due date cannot be in the past"
            )
        return value

class TaskDetailSerializer(TaskSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    
    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + (
            'comments',
        )

class TaskCommentSerializer(serializers.Serializer):
    comment = serializers.CharField()

class TaskAttachmentSerializer(serializers.Serializer):
    attachment = serializers.FileField()

class TaskBulkActionSerializer(serializers.Serializer):
    task_ids = serializers.ListField(
        child=serializers.IntegerField()
    )
    status = serializers.ChoiceField(
        choices=STATUS_CHOICES,
        required=False
    )
    priority = serializers.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False
    )
    assigned_to = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    teams = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )

    def validate(self, attrs):
        if not any([
            attrs.get('status'),
            attrs.get('priority'),
            attrs.get('assigned_to'),
            attrs.get('teams')
        ]):
            raise serializers.ValidationError(
                "At least one action field is required"
            )
        return attrs

class TaskFilterSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    status = serializers.ChoiceField(
        choices=STATUS_CHOICES,
        required=False
    )
    priority = serializers.ChoiceField(
        choices=PRIORITY_CHOICES,
        required=False
    )
    assigned_to = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    due_date = serializers.DateField(required=False)
    created_by = serializers.IntegerField(required=False)
    teams = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )

class TaskExportSerializer(serializers.Serializer):
    file_format = serializers.ChoiceField(
        choices=['csv', 'xls'],
        default='csv'
    )
    status = serializers.ChoiceField(
        choices=STATUS_CHOICES,
        required=False
    )
    date_range_start = serializers.DateField(required=False)
    date_range_end = serializers.DateField(required=False)

    def validate(self, attrs):
        if attrs.get('date_range_start') and attrs.get('date_range_end'):
            if attrs['date_range_start'] > attrs['date_range_end']:
                raise serializers.ValidationError(
                    "Start date cannot be after end date"
                )
        return attrs