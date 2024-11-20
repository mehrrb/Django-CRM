from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_spectacular.utils import extend_schema

from common.models import Document, Profile, User, APISettings
from common.serializers import (
    CreateUserSerializer,
    ProfileSerializer,
    DocumentCreateSerializer,
    APISettingsSerializer, 
    APISettingsListSerializer,
    BillingAddressSerializer,
    CreateProfileSerializer,
    DocumentSerializer,
    UserCreateSwaggerSerializer,
    UserUpdateStatusSwaggerSerializer,
    OrgProfileCreateSerializer,
    ShowOrganizationListSerializer
)
from teams.models import Teams
from accounts.models import Tags

class CommonViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        return Response({
            "message": "Welcome to API Dashboard"
        })

    @action(detail=False, methods=['post', 'get'])
    def org(self, request):
        if request.method == 'POST':
            serializer = OrgProfileCreateSerializer(data=request.data)
            if serializer.is_valid():
                org = serializer.save()
                return Response({
                    "message": "Organization profile created successfully",
                    "org": ShowOrganizationListSerializer(org).data
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        # GET method
        return Response({
            "message": "Organization profile details",
            "org": ShowOrganizationListSerializer(request.profile.org).data
        })

class ProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    pagination_class = LimitOffsetPagination
    
    def get_queryset(self):
        queryset = Profile.objects.filter(org=self.request.profile.org)
        
        # Add filters
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
            
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
            
        return queryset
    
    @extend_schema(request=UserCreateSwaggerSerializer)
    def create(self, request):
        serializer = CreateProfileSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save(org=request.profile.org)
            return Response(
                ProfileSerializer(profile).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @extend_schema(request=UserCreateSwaggerSerializer)
    def update(self, request, pk=None):
        profile = self.get_object()
        address_obj = profile.address

        # Check permissions
        if (
            request.profile.role != "ADMIN"
            and not request.user.is_superuser
            and request.profile.id != profile.id
        ):
            return Response(
                {"error": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        if profile.org != request.profile.org:
            return Response(
                {"error": "User organization mismatch"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate and save
        serializers_data = {
            'user': CreateUserSerializer(
                data=request.data,
                instance=profile.user,
                org=request.profile.org
            ),
            'address': BillingAddressSerializer(
                data=request.data,
                instance=address_obj
            ),
            'profile': CreateProfileSerializer(
                data=request.data,
                instance=profile
            )
        }

        if not all(s.is_valid() for s in serializers_data.values()):
            return Response(
                {k: s.errors for k, s in serializers_data.items()},
                status=status.HTTP_400_BAD_REQUEST
            )

        for serializer in serializers_data.values():
            serializer.save()

        return Response(
            {"message": "User Updated Successfully"},
            status=status.HTTP_200_OK
        )

    def destroy(self, request, pk=None):
        profile = self.get_object()
        
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        profile.delete()
        return Response(
            {"message": "Profile deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=['post'])
    @extend_schema(request=UserUpdateStatusSwaggerSerializer)
    def status(self, request, pk=None):
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        profile = self.get_object()
        status_map = {
            "Active": True,
            "Inactive": False
        }
        
        new_status = request.data.get("status")
        if new_status not in status_map:
            return Response(
                {"error": "Invalid status value"},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile.is_active = status_map[new_status]
        profile.save()

        profiles = self.get_queryset()
        return Response({
            "active_profiles": ProfileSerializer(
                profiles.filter(is_active=True),
                many=True
            ).data,
            "inactive_profiles": ProfileSerializer(
                profiles.filter(is_active=False),
                many=True
            ).data
        })

class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentSerializer
    queryset = Document.objects.all()
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        queryset = Document.objects.filter(org=self.request.profile.org)
        
        # Add filters
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        shared_to = self.request.query_params.get('shared_to')
        if shared_to:
            queryset = queryset.filter(shared_to=shared_to)
            
        return queryset

    def perform_create(self, serializer):
        doc = serializer.save(
            created_by=self.request.profile,
            org=self.request.profile.org,
            document_file=self.request.FILES.get("document_file")
        )
        self._handle_m2m(doc, self.request.data)
        
    def perform_update(self, serializer):
        doc = serializer.save(
            document_file=self.request.FILES.get("document_file")
        )
        self._handle_m2m(doc, self.request.data)

    def _handle_m2m(self, doc, data):
        if "shared_to" in data:
            doc.shared_to.clear()
            profiles = Profile.objects.filter(
                id__in=data["shared_to"],
                org=self.request.profile.org,
                is_active=True
            )
            doc.shared_to.add(*profiles)

        if "teams" in data:
            doc.teams.clear()
            teams = Teams.objects.filter(
                id__in=data["teams"],
                org=self.request.profile.org
            )
            doc.teams.add(*teams)

    def destroy(self, request, pk=None):
        document = self.get_object()
        
        if (
            request.profile.role != "ADMIN"
            and not request.user.is_superuser
            and request.profile != document.created_by
        ):
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        document.delete()
        return Response(
            {"message": "Document deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )

class APISettingsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = APISettingsSerializer
    queryset = APISettings.objects.all()
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        queryset = APISettings.objects.filter(org=self.request.profile.org)
        
        # Add filters
        title = self.request.query_params.get('title')
        if title:
            queryset = queryset.filter(title__icontains=title)
            
        website = self.request.query_params.get('website')
        if website:
            queryset = queryset.filter(website__icontains=website)
            
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return APISettingsListSerializer
        return APISettingsSerializer

    def perform_create(self, serializer):
        api_setting = serializer.save(
            created_by=self.request.profile,
            org=self.request.profile.org
        )
        self._handle_m2m(api_setting, self.request.data)

    def perform_update(self, serializer):
        api_setting = serializer.save()
        self._handle_m2m(api_setting, self.request.data)

    def _handle_m2m(self, api_setting, data):
        if "tags" in data:
            api_setting.tags.clear()
            for tag_name in data["tags"]:
                tag, _ = Tags.objects.get_or_create(name=tag_name)
                api_setting.tags.add(tag)

        if "lead_assigned_to" in data:
            api_setting.lead_assigned_to.clear()
            api_setting.lead_assigned_to.add(*data["lead_assigned_to"])

    def destroy(self, request, pk=None):
        api_setting = self.get_object()
        api_setting.delete()
        return Response(
            {"message": "API Settings deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )