from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import LimitOffsetPagination

from common.models import Document, Profile, User, APISettings
from common.serializer import (
    CreateUserSerializer,
    ProfileSerializer,
    DocumentCreateSerializer,
    APISettingsSerializer,
    APISettingsListSerializer,
    BillingAddressSerializer,
    CreateProfileSerializer
)
from teams.models import Teams
from accounts.models import Tags

class ApiHomeView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def get(self, request, *args, **kwargs):
        return Response({
            "message": "Welcome to API Dashboard"
        })

class OrgProfileCreateView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        return Response({
            "message": "Organization profile created successfully"
        })

    def get(self, request, *args, **kwargs):
        return Response({
            "message": "Organization profile details"
        })

class UserDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return get_object_or_404(Profile, pk=pk)

    def put(self, request, pk):
        profile = self.get_object(pk)
        address_obj = profile.address

        # Check access
        if (
            request.profile.role != "ADMIN"
            and not request.user.is_superuser
            and request.profile.id != profile.id
        ):
            return Response(
                {"error": "Permission Denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if profile.org != request.profile.org:
            return Response(
                {"error": "User organization mismatch"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Validate and save
        serializer = CreateUserSerializer(
            data=request.data, 
            instance=profile.user, 
            org=request.profile.org
        )
        address_serializer = BillingAddressSerializer(
            data=request.data, 
            instance=address_obj
        )
        profile_serializer = CreateProfileSerializer(
            data=request.data, 
            instance=profile
        )

        if not all([
            serializer.is_valid(),
            address_serializer.is_valid(),
            profile_serializer.is_valid()
        ]):
            return Response(
                {
                    "user_errors": serializer.errors,
                    "address_errors": address_serializer.errors,
                    "profile_errors": profile_serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        address_obj = address_serializer.save()
        user = serializer.save()
        profile = profile_serializer.save()

        return Response(
            {"message": "User Updated Successfully"},
            status=status.HTTP_200_OK,
        )


class DocumentDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return get_object_or_404(Document, pk=pk)

    def put(self, request, pk):
        document = self.get_object(pk)

        # Check access
        if document.org != request.profile.org:
            return Response(
                {"error": "Document organization mismatch"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            request.profile.role != "ADMIN" 
            and not request.user.is_superuser
            and request.profile != document.created_by
            and request.profile not in document.shared_to.all()
        ):
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DocumentCreateSerializer(
            data=request.data,
            instance=document,
            request_obj=request
        )

        if serializer.is_valid():
            doc = serializer.save(
                document_file=request.FILES.get("document_file"),
                status=request.data.get("status"),
                org=request.profile.org,
            )

            # Update shared_to
            if request.data.get("shared_to"):
                doc.shared_to.clear()
                profiles = Profile.objects.filter(
                    id__in=request.data.get("shared_to"),
                    org=request.profile.org,
                    is_active=True
                )
                doc.shared_to.add(*profiles)

            # Update teams
            if request.data.get("teams"):
                doc.teams.clear()
                teams = Teams.objects.filter(
                    id__in=request.data.get("teams"),
                    org=request.profile.org
                )
                doc.teams.add(*teams)

            return Response(
                {"message": "Document Updated Successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        document = self.get_object(pk)

        # Check access
        if document.org != request.profile.org:
            return Response(
                {"error": "Document organization mismatch"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if (
            request.profile.role != "ADMIN"
            and not request.user.is_superuser
            and request.profile != document.created_by
        ):
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        document.delete()
        return Response(
            {"message": "Document deleted Successfully"},
            status=status.HTTP_200_OK,
        )


class UserStatusView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        if request.profile.role != "ADMIN" and not request.user.is_superuser:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN,
            )

        profile = get_object_or_404(
            Profile, 
            id=pk,
            org=request.profile.org
        )

        # Change user status
        status_map = {
            "Active": True,
            "Inactive": False
        }
        
        new_status = request.data.get("status")
        if new_status not in status_map:
            return Response(
                {"error": "Invalid status value"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile.is_active = status_map[new_status]
        profile.save()

        # Return users list
        profiles = Profile.objects.filter(org=request.profile.org)
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


class DomainDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return get_object_or_404(APISettings, pk=pk)

    def get(self, request, pk):
        api_setting = self.get_object(pk)
        return Response({
            "domain": APISettingsListSerializer(api_setting).data
        })

    def put(self, request, pk):
        api_setting = self.get_object(pk)
        serializer = APISettingsSerializer(
            data=request.data,
            instance=api_setting
        )

        if serializer.is_valid():
            api_setting = serializer.save()

            # Update tags
            if request.data.get("tags"):
                api_setting.tags.clear()
                for tag_name in request.data.get("tags"):
                    tag, _ = Tags.objects.get_or_create(name=tag_name)
                    api_setting.tags.add(tag)

            # Update lead_assigned_to
            if request.data.get("lead_assigned_to"):
                api_setting.lead_assigned_to.clear()
                api_setting.lead_assigned_to.add(
                    *request.data.get("lead_assigned_to")
                )

            return Response(
                {"message": "API Settings Updated Successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, pk):
        api_setting = self.get_object(pk)
        api_setting.delete()
        return Response(
            {"message": "API Settings Deleted Successfully"},
            status=status.HTTP_200_OK,
        )
