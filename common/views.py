from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.core.cache import cache
from django.conf import settings
from rest_framework.exceptions import ValidationError
import logging
from rest_framework.viewsets import GenericViewSet

from common.models import Document, Profile, APISettings, Comment,Org
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
    ShowOrganizationListSerializer,
    OrgSerializer
)
from teams.models import Teams
from accounts.models import Tags
from common.throttling import OrgRateThrottle
from users.models import Users as User

logger = logging.getLogger(__name__)

class CommonViewSet(mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin,
                   mixins.UpdateModelMixin,
                   mixins.DestroyModelMixin,
                   GenericViewSet):
    """
    Use DRF generic mixins instead of custom ViewSet
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [OrgRateThrottle]
    
    @extend_schema(
        tags=['Dashboard'],
        description='Get dashboard welcome message',
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        logger.debug("Dashboard endpoint accessed")
        return Response({
            "message": "Welcome to API Dashboard"
        })

    @extend_schema(
        tags=['Organizations'],
        description='Create or retrieve organization details',
        parameters=[
            OpenApiParameter(
                name='org',
                type=str,
                location=OpenApiParameter.HEADER,
                description='Organization ID'
            ),
        ],
        request=OrgProfileCreateSerializer,
        responses={
            200: ShowOrganizationListSerializer,
            201: {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string'},
                    'org': {'type': 'object'}
                }
            },
            400: {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'},
                    'details': {'type': 'object'}
                }
            }
        }
    )
    @action(detail=False, methods=['post', 'get'])
    def org(self, request):
        cache_key = f'org_{request.profile.org.id}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.debug(f"Returning cached org data for {request.profile.org.id}")
            return Response(cached_data)
            
        logger.info(f"Org endpoint accessed by user {request.user.id} for org {request.profile.org.id}")
        try:
            if request.method == 'POST':
                serializer = OrgProfileCreateSerializer(data=request.data)
                if serializer.is_valid(raise_exception=True):
                    org = serializer.save()
                    response_data = {
                        "message": "Organization profile created successfully",
                        "org": ShowOrganizationListSerializer(org).data
                    }
                    cache.set(cache_key, response_data, timeout=settings.CACHE_TIMEOUT)
                    return Response(response_data, status=status.HTTP_201_CREATED)
            return Response({
                "message": "Organization profile details",
                "org": ShowOrganizationListSerializer(request.profile.org).data
            })
                    
        except ValidationError as e:
            logger.error(f"Validation error in org endpoint: {str(e)}")
            return Response({
                "error": "Validation Error",
                "details": e.detail
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in org endpoint: {str(e)}")
            return Response({
                "error": "Internal Server Error",
                "details": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    pagination_class = LimitOffsetPagination
    throttle_classes = [OrgRateThrottle]
    
    def get_queryset(self):
        queryset = Profile.objects.filter(org=self.request.profile.org)
        
        # Add filters
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
            
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)
            
        logger.debug(f"Filtered profile queryset: {queryset.query}")
        return queryset
    
    @extend_schema(request=UserCreateSwaggerSerializer)
    def create(self, request):
        logger.info(f"Creating new profile for org {request.profile.org.id}")
        serializer = CreateProfileSerializer(data=request.data)
        if serializer.is_valid():
            profile = serializer.save(org=request.profile.org)
            return Response(
                ProfileSerializer(profile).data,
                status=status.HTTP_201_CREATED
            )
        logger.error(f"Profile creation failed: {serializer.errors}")
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
            logger.warning(f"Permission denied for profile update: {request.user.id}")
            return Response(
                {"error": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        if profile.org != request.profile.org:
            logger.warning(f"Organization mismatch for profile update: {profile.id}")
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
            logger.error(f"Profile update validation failed: {serializers_data}")
            return Response(
                {k: s.errors for k, s in serializers_data.items()},
                status=status.HTTP_400_BAD_REQUEST
            )

        for serializer in serializers_data.values():
            serializer.save()

        logger.info(f"Profile updated successfully: {profile.id}")
        return Response(
            {"message": "User Updated Successfully"},
            status=status.HTTP_200_OK
        )

    def destroy(self, request, pk=None):
        profile = self.get_object()
        
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            logger.warning(f"Permission denied for profile deletion: {request.user.id}")
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        profile.delete()
        logger.info(f"Profile deleted: {pk}")
        return Response(
            {"message": "Profile deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=True, methods=['post'])
    @extend_schema(request=UserUpdateStatusSwaggerSerializer)
    def status(self, request, pk=None):
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            logger.warning(f"Permission denied for status update: {request.user.id}")
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
            logger.error(f"Invalid status value: {new_status}")
            return Response(
                {"error": "Invalid status value"},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile.is_active = status_map[new_status]
        profile.save()
        logger.info(f"Profile status updated: {pk} -> {new_status}")

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
    throttle_classes = [OrgRateThrottle]

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
    @action(detail=True, methods=['post'])
    @extend_schema(
        tags=['Documents'],
        description='Share document with users',
        request={
            'type': 'object',
            'properties': {
                'shared_to': {'type': 'array', 'items': {'type': 'string'}},
                'comment': {'type': 'string'}
            }
        },
        responses={
            200: {'type': 'object', 'properties': {'status': {'type': 'string'}}},
            400: {'type': 'object', 'properties': {'error': {'type': 'string'}}},
            403: {'type': 'object', 'properties': {'error': {'type': 'string'}}},
            404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}
        }
    )
    def share(self, request, pk=None):
        document = self.get_object()
        shared_to = request.data.get("shared_to", [])
        comment_text = request.data.get("comment", "")

        document.shared_to.add(*shared_to)

        if comment_text:
            Comment.objects.create(
                comment=comment_text,
                created_by=request.profile,
                document=document
            )
        return Response({"status": "Document shared successfully"})
    
    
class APISettingsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = APISettingsSerializer
    pagination_class = LimitOffsetPagination
    throttle_classes = [OrgRateThrottle]

    def get_queryset(self):
        if not hasattr(self.request, 'profile') or not self.request.profile:
            return APISettings.objects.none()
            
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

    @action(detail=True, methods=['post'])
    def update_tags(self, request, pk=None):
        api_setting = self.get_object()
        api_setting.tags = request.data["tags"]
        api_setting.save()
        return Response({"status": "tags updated successfully"})

class OrgViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OrgSerializer
    throttle_classes = [OrgRateThrottle]
    pagination_class = LimitOffsetPagination
    
    def get_queryset(self):
        if not hasattr(self.request, 'profile') or not self.request.profile:
            logger.warning("No profile found in request")
            return Org.objects.none()
        
        try:
            org_id = self.request.profile.org_id
            if not org_id:
                logger.error(f"No org found for profile {self.request.profile.id}")
                return Org.objects.none()
            
            return Org.objects.filter(id=org_id)
        
        except AttributeError as e:
            logger.error(f"Error accessing org: {str(e)}")
            return Org.objects.none()

    def perform_create(self, serializer):
        if self.request.profile.role != "ADMIN":
            raise ValidationError({"error": "Only admin can create organizations"})
        org = serializer.save(
            created_by=self.request.profile
        )
        return org

    def perform_update(self, serializer):
        if self.request.profile.role != "ADMIN":
            raise ValidationError({"error": "Only admin can update organizations"})
        org = serializer.save()
        return org

    def destroy(self, request, *args, **kwargs):
        if request.profile.role != "ADMIN":
            return Response(
                {"error": "Only admin can delete organizations"},
                status=status.HTTP_403_FORBIDDEN
            )
        org = self.get_object()
        org.delete()
        return Response(
            {"message": "Organization deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )