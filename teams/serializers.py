from rest_framework import serializers
from .models import Teams
from common.serializers import (
    ProfileSerializer,
    OrganizationSerializer,
    UserSerializer
)
from common.models import Profile

class TeamsSerializer(serializers.ModelSerializer):
    created_by = ProfileSerializer(read_only=True)
    org = OrganizationSerializer(read_only=True)
    users = ProfileSerializer(many=True, read_only=True)
    
    class Meta:
        model = Teams
        fields = (
            'id',
            'name',
            'description',
            'created_by',
            'created_at',
            'modified_at',
            'org',
            'users',
            'is_active'
        )
        read_only_fields = (
            'id',
            'created_by',
            'created_at',
            'modified_at',
            'org'
        )

class TeamCreateSerializer(serializers.ModelSerializer):
    assign_users = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    
    class Meta:
        model = Teams
        fields = (
            'name',
            'description',
            'assign_users',
            'is_active'
        )

    def __init__(self, *args, **kwargs):
        self.request_obj = kwargs.pop("request_obj", None)
        super(TeamCreateSerializer, self).__init__(*args, **kwargs)

    def validate_name(self, value):
        if self.instance:
            if Teams.objects.filter(
                name__iexact=value,
                org=self.request_obj.profile.org
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Team with this name already exists in your organization"
                )
        else:
            if Teams.objects.filter(
                name__iexact=value,
                org=self.request_obj.profile.org
            ).exists():
                raise serializers.ValidationError(
                    "Team with this name already exists in your organization"
                )
        return value

    def validate_assign_users(self, value):
        if value:
            if not all(isinstance(user_id, int) for user_id in value):
                raise serializers.ValidationError(
                    "User IDs must be integers"
                )
            
            valid_users = Profile.objects.filter(
                id__in=value,
                org=self.request_obj.profile.org,
                is_active=True
            ).count()
            
            if valid_users != len(value):
                raise serializers.ValidationError(
                    "One or more users are invalid or inactive"
                )
        return value

class TeamDetailSerializer(TeamsSerializer):
    class Meta(TeamsSerializer.Meta):
        fields = TeamsSerializer.Meta.fields + (
            'total_users',
            'active_users'
        )

    total_users = serializers.SerializerMethodField()
    active_users = serializers.SerializerMethodField()

    def get_total_users(self, obj):
        return obj.users.count()

    def get_active_users(self, obj):
        return obj.users.filter(is_active=True).count()

class TeamBulkActionSerializer(serializers.Serializer):
    team_ids = serializers.ListField(
        child=serializers.IntegerField()
    )
    users_to_add = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    users_to_remove = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    is_active = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if not any([
            attrs.get('users_to_add'),
            attrs.get('users_to_remove'),
            'is_active' in attrs
        ]):
            raise serializers.ValidationError(
                "At least one action field is required"
            )
        return attrs

class TeamSwaggerCreateSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=False)
    assign_users = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    is_active = serializers.BooleanField(required=False)

class TeamFilterSerializer(serializers.Serializer):
    team_name = serializers.CharField(required=False)
    created_by = serializers.IntegerField(required=False)
    assigned_users = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    is_active = serializers.BooleanField(required=False)

class TeamUserAssignSerializer(serializers.Serializer):
    users = serializers.ListField(
        child=serializers.IntegerField(),
        required=True
    )

    def validate_users(self, value):
        if not value:
            raise serializers.ValidationError(
                "At least one user ID is required"
            )
        return value