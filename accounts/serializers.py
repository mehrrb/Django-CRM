from rest_framework import serializers
from .models import Account, Tags
from emails.models import Email
from common.serializers import (
    ProfileSerializer,
    OrganizationSerializer,
    CommentSerializer,
    AttachmentSerializer,
    UserSerializer
)
from teams.serializers import TeamsSerializer
from common.utils import COUNTRIES, INDCHOICES

class TagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tags
        fields = ('id', 'name')

class AccountSerializer(serializers.ModelSerializer):
    created_by = ProfileSerializer(read_only=True)
    org = OrganizationSerializer(read_only=True)
    assigned_to = ProfileSerializer(many=True, read_only=True)
    teams = TeamsSerializer(many=True, read_only=True)
    tags = TagsSerializer(many=True, read_only=True)
    
    class Meta:
        model = Account
        fields = (
            'id',
            'name',
            'email',
            'phone',
            'industry',
            'billing_address_line',
            'billing_street',
            'billing_city',
            'billing_state',
            'billing_postcode',
            'billing_country',
            'website',
            'description',
            'created_by',
            'created_at',
            'modified_at',
            'org',
            'assigned_to',
            'teams',
            'tags',
            'status',
            'contact_name',
            'is_active'
        )
        read_only_fields = (
            'id',
            'created_by',
            'created_at',
            'modified_at',
            'org'
        )

class AccountCreateSerializer(serializers.ModelSerializer):
    assigned_to = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    teams = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    
    class Meta:
        model = Account
        fields = (
            'name',
            'email',
            'phone',
            'industry',
            'billing_address_line',
            'billing_street',
            'billing_city',
            'billing_state',
            'billing_postcode',
            'billing_country',
            'website',
            'description',
            'assigned_to',
            'teams',
            'tags',
            'status',
            'contact_name',
            'is_active'
        )

    def __init__(self, *args, **kwargs):
        self.request_obj = kwargs.pop("request_obj", None)
        super(AccountCreateSerializer, self).__init__(*args, **kwargs)

    def validate_name(self, value):
        if self.instance:
            if Account.objects.filter(
                name__iexact=value,
                org=self.request_obj.profile.org
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Account with this name already exists in your organization"
                )
        else:
            if Account.objects.filter(
                name__iexact=value,
                org=self.request_obj.profile.org
            ).exists():
                raise serializers.ValidationError(
                    "Account with this name already exists in your organization"
                )
        return value

    def validate_assigned_to(self, value):
        if value:
            if not all(isinstance(user_id, int) for user_id in value):
                raise serializers.ValidationError(
                    "User IDs must be integers"
                )
        return value

    def validate_teams(self, value):
        if value:
            if not all(isinstance(team_id, int) for team_id in value):
                raise serializers.ValidationError(
                    "Team IDs must be integers"
                )
        return value

class AccountDetailSerializer(AccountSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    
    class Meta(AccountSerializer.Meta):
        fields = AccountSerializer.Meta.fields + (
            'comments',
            'attachments'
        )

class AccountBulkActionSerializer(serializers.Serializer):
    account_ids = serializers.ListField(
        child=serializers.IntegerField()
    )
    assigned_to = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    teams = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    status = serializers.ChoiceField(
        choices=['open', 'close'],
        required=False
    )

    def validate(self, attrs):
        if not any([
            attrs.get('assigned_to'),
            attrs.get('teams'),
            attrs.get('status')
        ]):
            raise serializers.ValidationError(
                "At least one action field is required"
            )
        return attrs

class AccountSwaggerSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False)
    industry = serializers.ChoiceField(choices=INDCHOICES, required=False)
    billing_address_line = serializers.CharField(required=False)
    billing_street = serializers.CharField(required=False)
    billing_city = serializers.CharField(required=False)
    billing_state = serializers.CharField(required=False)
    billing_postcode = serializers.CharField(required=False)
    billing_country = serializers.ChoiceField(choices=COUNTRIES, required=False)
    website = serializers.URLField(required=False)
    description = serializers.CharField(required=False)
    assigned_to = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    teams = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    tags = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    status = serializers.ChoiceField(
        choices=['open', 'close'],
        required=False
    )
    contact_name = serializers.CharField(required=False)
    is_active = serializers.BooleanField(required=False)

class EmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Email
        fields = (
            'recipient_email',
            'subject',
            'message',
            'from_email'
        )