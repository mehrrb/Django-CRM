from rest_framework import serializers
from .models import Contact
from common.models import Comment  # Add this import
from common.serializers import (
    UserSerializer,
    ProfileSerializer,
    AttachmentSerializer,
    CommentSerializer,  # We'll use this instead of defining our own
    BillingAddressSerializer,
    OrganizationSerializer
)
from teams.serializers import TeamsSerializer
from tasks.serializers import TaskSerializer

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = (
            'id',
            'first_name',
            'last_name', 
            'primary_email',
            'secondary_email',
            'mobile_number',
            'secondary_number',
            'department',
            'title',
            'description',
            'status',
            'source',
            'company_name',
            'created_by',
            'created_at',
            'is_active'
        )
        read_only_fields = ('created_by', 'created_at', 'is_active')

    def validate_mobile_number(self, value):
        """Additional validation for mobile number"""
        if value:
            import re
            pattern = r'^\+?1?\d{9,15}$'
            if not re.match(pattern, value):
                raise serializers.ValidationError('Invalid phone number format')
        return value

class ContactCreateSerializer(serializers.ModelSerializer):
    address = BillingAddressSerializer(required=False)
    assigned_to = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    teams = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )
    contact_attachment = serializers.FileField(required=False, allow_null=True)

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
            'status',
            'source',
            'company_name',
            'address',
            'assigned_to',
            'teams',
            'contact_attachment'
        )

    def validate(self, attrs):
        # Remove None values for optional fields
        cleaned_data = {k: v for k, v in attrs.items() if v is not None}
        
        # Ensure required fields are present
        required_fields = ['first_name', 'last_name', 'primary_email']
        for field in required_fields:
            if field not in cleaned_data:
                raise serializers.ValidationError(f"{field} is required")
                
        return cleaned_data

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
    assigned_to = ProfileSerializer(many=True, read_only=True)
    teams = TeamsSerializer(many=True, read_only=True)
    
    class Meta(ContactSerializer.Meta):
        fields = ContactSerializer.Meta.fields + (
            'assigned_to',
            'teams'
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
