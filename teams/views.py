from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Teams
from .serializers import (
    TeamsSerializer,
    TeamCreateSerializer,
    TeamDetailSerializer,
    TeamBulkActionSerializer,
    TeamSwaggerCreateSerializer
)
from common.models import Profile
from common.serializers import ProfileSerializer
from teams.tasks import remove_users, update_team_users

class TeamViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination
    
    def get_queryset(self):
        params = self.request.query_params
        queryset = Teams.objects.filter(org=self.request.profile.org).order_by('-created_at')
        
        # Filter based on user role
        if not self.request.profile.is_admin and self.request.profile.role != "ADMIN":
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Apply filters
        if params.get('team_name'):
            queryset = queryset.filter(name__icontains=params.get('team_name'))
        if params.get('created_by'):
            queryset = queryset.filter(created_by=params.get('created_by'))
        if params.getlist('assigned_users'):
            queryset = queryset.filter(
                users__id__in=params.getlist('assigned_users')
            ).distinct()
            
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return TeamCreateSerializer
        elif self.action == 'retrieve':
            return TeamDetailSerializer
        return TeamsSerializer

    @extend_schema(
        tags=["Teams"],
        request=TeamSwaggerCreateSerializer
    )
    def create(self, request, *args, **kwargs):
        if not request.profile.is_admin and request.profile.role != "ADMIN":
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.get_serializer(data=request.data, request_obj=request)
        if serializer.is_valid():
            team = serializer.save(
                created_by=request.profile,
                org=request.profile.org
            )
            
            if request.data.get('assign_users'):
                profiles = Profile.objects.filter(
                    id__in=request.data.get('assign_users'),
                    org=request.profile.org,
                    is_active=True
                )
                team.users.add(*profiles)

            return Response(
                {"error": False, "message": "Team Created Successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        tags=["Teams"],
        request=TeamSwaggerCreateSerializer
    )
    def update(self, request, *args, **kwargs):
        if not request.profile.is_admin and request.profile.role != "ADMIN":
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        team = self.get_object()
        actual_users = team.get_users()
        
        serializer = self.get_serializer(team, data=request.data, partial=True, request_obj=request)
        if serializer.is_valid():
            team = serializer.save()
            
            # Update users
            if 'assign_users' in request.data:
                team.users.clear()
                if request.data.get('assign_users'):
                    profiles = Profile.objects.filter(
                        id__in=request.data.get('assign_users'),
                        org=request.profile.org,
                        is_active=True
                    )
                    team.users.add(*profiles)
                
                # Handle removed users
                update_team_users.delay(team.id)
                latest_users = team.get_users()
                removed_users = [user for user in actual_users if user not in latest_users]
                if removed_users:
                    remove_users.delay(removed_users, team.id)

            return Response(
                {"error": False, "message": "Team Updated Successfully"},
                status=status.HTTP_200_OK
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(tags=["Teams"])
    def destroy(self, request, *args, **kwargs):
        if not request.profile.is_admin and request.profile.role != "ADMIN":
            return Response(
                {
                    "error": True,
                    "errors": "You don't have permission to perform this action.",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        team = self.get_object()
        team.delete()
        return Response(
            {"error": False, "message": "Team Deleted Successfully"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def add_users(self, request, pk=None):
        team = self.get_object()
        user_ids = request.data.get('users', [])
        
        if not user_ids:
            return Response(
                {'error': True, 'errors': 'No users provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        profiles = Profile.objects.filter(
            id__in=user_ids,
            org=request.profile.org,
            is_active=True
        )
        team.users.add(*profiles)
        update_team_users.delay(team.id)
        
        return Response(
            {"error": False, "message": "Users added successfully"},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def remove_users(self, request, pk=None):
        team = self.get_object()
        user_ids = request.data.get('users', [])
        
        if not user_ids:
            return Response(
                {'error': True, 'errors': 'No users provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        profiles = Profile.objects.filter(
            id__in=user_ids,
            org=request.profile.org
        )
        team.users.remove(*profiles)
        remove_users.delay(list(profiles), team.id)
        
        return Response(
            {"error": False, "message": "Users removed successfully"},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def my_teams(self, request):
        """Get teams where current user is a member"""
        teams = Teams.objects.filter(
            users=request.profile,
            org=request.profile.org
        )
        page = self.paginate_queryset(teams)
        if page is not None:
            serializer = TeamsSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TeamsSerializer(teams, many=True)
        return Response({"error": False, "teams": serializer.data})