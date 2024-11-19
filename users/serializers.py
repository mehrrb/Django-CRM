from rest_framework import serializers
from .models import Users



class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = Users
        fields = ['email', 'password', 'username']
        extra_kwargs = {
            'email': {'required': True},
            'password': {'write_only': True}
        }
        
    def validate_email(self, value):
        if Users.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()