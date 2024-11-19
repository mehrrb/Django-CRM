from django.shortcuts import render
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login, logout
from .models import Users
from .serializers import UserSerializer, LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
import logging
import traceback


class UsersView(ModelViewSet):
    queryset = Users.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        data = request.data
        ser_data = UserSerializer(data=data)
        if ser_data.is_valid():
            email = ser_data.validated_data['email']
            password = ser_data.validated_data['password']
            
            user = Users(
                email = email,            
            )
            user.set_password(password)
            user.save()
            return Response({"info" : "successfully created"}, status=status.HTTP_201_CREATED)
        else:
            return Response(ser_data.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
    

class LoginView(APIView):
    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')
            
            if not email or not password:
                return Response(
                    {"error": "Both email and password are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                user = Users.objects.get(email=email)
            except ObjectDoesNotExist:
                return Response(
                    {"error": "User not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
                
            if not user.check_password(password):
                return Response(
                    {"error": "Invalid password"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            ser_user = LoginSerializer(data=request.data)
            if not ser_user.is_valid():
                return Response(
                    ser_user.errors, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            token = RefreshToken.for_user(user)
            response = {
                **ser_user.data,
                'access_token': str(token.access_token),
                'refresh_token': str(token),
                'is_superuser': user.is_superuser
            }
            
            login(request, user)
            return Response(response, status=status.HTTP_200_OK)
            
        except Exception as e:
            logging.error(f"Login error: {str(e)}\n{traceback.format_exc()}")
            return Response(
                {"error": "An unexpected error occurred"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


#    
# def post(request):


class LogoutView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self,request):
        logout(request)
        return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)