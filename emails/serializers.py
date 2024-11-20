from rest_framework import serializers
from .models import Email
from users.serializers import UserSerializer

class EmailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(many=True, read_only=True)
    assigned_to_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Email
        fields = [
            'id',
            'user',
            'subject',
            'message',
            'from_email',
            'to_email',
            'status',
            'important',
            'is_draft',
            'is_sent',
            'is_trash',
            'is_important',
            'created_by',
            'created_at',
            'modified_at',
            'assigned_to',
            'assigned_to_ids',
            'teams',
            'cc',
            'bcc',
            'attachments',
            'scheduled_later',
            'scheduled_date_time',
            'reply_to_email'
        ]
        read_only_fields = [
            'user', 
            'created_by',
            'created_at',
            'modified_at'
        ]

    def create(self, validated_data):
        assigned_to_ids = validated_data.pop('assigned_to_ids', [])
        email = Email.objects.create(**validated_data)
        email.assigned_to.set(assigned_to_ids)
        return email

    def update(self, instance, validated_data):
        assigned_to_ids = validated_data.pop('assigned_to_ids', None)
        if assigned_to_ids is not None:
            instance.assigned_to.set(assigned_to_ids)
        return super().update(instance, validated_data)