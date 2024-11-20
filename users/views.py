from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema
from django.contrib.auth import login, logout
from django.core.exceptions import ObjectDoesNotExist
import logging
import traceback

from .models import Users
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    LoginSerializer,
    UserDetailSerializer
)

class UserViewSet(viewsets.ModelViewSet):
    queryset = Users.objects.all()
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['create', 'login']:
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(tags=["Users"])
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "error": False,
                    "message": "User created successfully",
                    "user": UserSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                "error": True,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            
            if not email or not password:
                return Response(
                    {
                        "error": True,
                        "errors": "Both email and password are required"
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                user = Users.objects.get(email=email)
            except ObjectDoesNotExist:
                return Response(
                    {
                        "error": True,
                        "errors": "User not found"
                    }, 
                    status=status.HTTP_404_NOT_FOUND
                )
                
            if not user.check_password(password):
                return Response(
                    {
                        "error": True,
                        "errors": "Invalid password"
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = LoginSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {
                        "error": True,
                        "errors": serializer.errors
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            token = RefreshToken.for_user(user)
            response = {
                "error": False,
                "data": {
                    **serializer.data,
                    'access_token': str(token.access_token),
                    'refresh_token': str(token),
                    'is_superuser': user.is_superuser,
                    'user': UserSerializer(user).data
                }
            }
            
            login(request, user)
            return Response(response, status=status.HTTP_200_OK)
            
        except Exception as e:
            logging.error(f"Login error: {str(e)}\n{traceback.format_exc()}")
            return Response(
                {
                    "error": True,
                    "errors": "An unexpected error occurred"
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def logout(self, request):
        logout(request)
        return Response(
            {
                'error': False,
                'message': 'Successfully logged out.'
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user details"""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response(
                {
                    "error": True,
                    "errors": "Both old and new passwords are required"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not user.check_password(old_password):
            return Response(
                {
                    "error": True,
                    "errors": "Invalid old password"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        user.set_password(new_password)
        user.save()
        return Response(
            {
                "error": False,
                "message": "Password changed successfully"
            }
        )