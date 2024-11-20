from rest_framework import serializers
from .models import Contact
from common.serializers import (
    UserSerializer,
    ProfileSerializer,
    AttachmentSerializer,
    CommentSerializer,
    BillingAddressSerializer,
    OrganizationSerializer
)
from teams.serializers import TeamsSerializer
from tasks.serializers import TaskSerializer

class ContactSerializer(serializers.ModelSerializer):
    created_by = ProfileSerializer(read_only=True)
    org = OrganizationSerializer(read_only=True)
    teams = TeamsSerializer(many=True, read_only=True)
    assigned_to = ProfileSerializer(many=True, read_only=True)
    contact_attachments = AttachmentSerializer(many=True, read_only=True)
    address = BillingAddressSerializer(read_only=True)
    
    class Meta:
        model = Contact
        fields = (
            'id',
            'first_name',
            'last_name',
            'org',
            'primary_email',
            'secondary_email',
            'mobile_number',
            'secondary_number',
            'department',
            'title',
            'created_by',
            'created_at',
            'is_active',
            'address',
            'description',
            'linked_in_url',
            'facebook_url',
            'twitter_username',
            'contact_attachments',
            'assigned_to',
            'teams',
            'status',
            'source',
            'modified_by',
            'modified_at',
            'company_name'
        )
        read_only_fields = (
            'id',
            'created_by',
            'created_at',
            'modified_by',
            'modified_at',
            'org'
        )

class ContactCreateSerializer(serializers.ModelSerializer):
    address = BillingAddressSerializer(required=False)
    assigned_to = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    teams = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    contact_attachment = serializers.FileField(required=False)

    class Meta:
        model = Contact
        fields = (
            'first_name',
            'last_name',
            'primary_email',
            'secondary_email',
            'mobile_number',
            'secondary_number',
            'department',
            'title',
            'description',
            'linked_in_url',
            'facebook_url',
            'twitter_username',
            'status',
            'source',
            'company_name',
            'address',
            'assigned_to',
            'teams',
            'contact_attachment'
        )

    def validate_primary_email(self, value):
        if value:
            if Contact.objects.filter(
                primary_email__iexact=value,
                org=self.context['request'].profile.org
            ).exists():
                raise serializers.ValidationError(
                    "Contact with this email already exists"
                )
        return value

class ContactDetailSerializer(ContactSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    tasks = TaskSerializer(many=True, read_only=True, source='contacts_tasks')
    
    class Meta(ContactSerializer.Meta):
        fields = ContactSerializer.Meta.fields + (
            'comments',
            'tasks'
        )

class ContactCommentSerializer(serializers.Serializer):
    comment = serializers.CharField()

class ContactAttachmentSerializer(serializers.Serializer):
    attachment = serializers.FileField()

class ContactEmailSerializer(serializers.Serializer):
    subject = serializers.CharField()
    message = serializers.CharField()
    recipients = serializers.ListField(
        child=serializers.EmailField()
    )
    scheduled_later = serializers.BooleanField(default=False)
    scheduled_date_time = serializers.DateTimeField(required=False)
    timezone = serializers.CharField(required=False)
    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False
    )

class ContactBulkActionSerializer(serializers.Serializer):
    contact_ids = serializers.ListField(
        child=serializers.IntegerField()
    )
    status = serializers.CharField(required=False)
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
            attrs.get('assigned_to'),
            attrs.get('teams')
        ]):
            raise serializers.ValidationError(
                "At least one action field is required"
            )
        return attrs