from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import LimitOffsetPagination

from common.models import Attachments, Comment, Profile
from common.serializer import (
    AttachmentsSerializer,
    BillingAddressSerializer,
    CommentSerializer,
)
from common.utils import COUNTRIES
from contacts.models import Contact
from contacts.serializer import (
    ContactSerializer,
    CreateContactSerializer,
    TaskSerializer
)
from contacts.tasks import send_email_to_assigned_user
from teams.models import Teams


class ContactsListView(APIView, LimitOffsetPagination):
    permission_classes = (IsAuthenticated,)
    model = Contact

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(org=self.request.profile.org).order_by("-id")
        
        # Filter based on user role
        if not self.request.profile.is_admin:
            queryset = queryset.filter(
                Q(assigned_to__in=[self.request.profile]) |
                Q(created_by=self.request.profile.user)
            ).distinct()

        # Apply filters
        if params:
            if params.get("name"):
                queryset = queryset.filter(first_name__icontains=params.get("name"))
            if params.get("city"):
                queryset = queryset.filter(address__city__icontains=params.get("city"))
            if params.get("phone"):
                queryset = queryset.filter(mobile_number__icontains=params.get("phone"))
            if params.get("email"):
                queryset = queryset.filter(primary_email__icontains=params.get("email"))
            if params.getlist("assigned_to"):
                queryset = queryset.filter(
                    assigned_to__id__in=params.get("assigned_to")
                ).distinct()

        # Pagination
        results = self.paginate_queryset(queryset.distinct(), self.request, view=self)
        contacts = ContactSerializer(results, many=True).data

        return {
            "contacts": contacts,
            "count": self.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "countries": COUNTRIES,
            "users": Profile.objects.filter(
                is_active=True, 
                org=self.request.profile.org
            ).values("id", "user__email")
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    def post(self, request, *args, **kwargs):
        contact_serializer = CreateContactSerializer(
            data=request.data, 
            request_obj=request
        )
        address_serializer = BillingAddressSerializer(data=request.data)

        if not all([contact_serializer.is_valid(), address_serializer.is_valid()]):
            return Response(
                {
                    "contact_errors": contact_serializer.errors,
                    "address_errors": address_serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save information
        address = address_serializer.save()
        contact = contact_serializer.save(
            date_of_birth=request.data.get("date_of_birth"),
            address=address,
            org=request.profile.org
        )

        # Add teams
        if request.data.get("teams"):
            teams = Teams.objects.filter(
                id__in=request.data.get("teams"),
                org=request.profile.org
            )
            contact.teams.add(*teams)

        # Add users
        if request.data.get("assigned_to"):
            profiles = Profile.objects.filter(
                id__in=request.data.get("assigned_to"),
                org=request.profile.org
            )
            contact.assigned_to.add(*profiles)
            
            # Send email
            recipients = list(profiles.values_list("id", flat=True))
            send_email_to_assigned_user.delay(recipients, contact.id)

        # Upload file
        if request.FILES.get("contact_attachment"):
            attachment = Attachments.objects.create(
                created_by=request.profile.user,
                file_name=request.FILES.get("contact_attachment").name,
                contact=contact,
                attachment=request.FILES.get("contact_attachment")
            )

        return Response(
            {"message": "Contact created successfully"},
            status=status.HTTP_201_CREATED
        )


class ContactDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return get_object_or_404(Contact, pk=pk)

    def get(self, request, pk):
        contact = self.get_object(pk)
        
        # Check access
        if contact.org != request.profile.org:
            return Response(
                {"error": "Organization mismatch"},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.profile.is_admin:
            if not (
                request.profile == contact.created_by or
                request.profile in contact.assigned_to.all()
            ):
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN
                )

        return Response({
            "contact": ContactSerializer(contact).data,
            "address": BillingAddressSerializer(contact.address).data,
            "attachments": AttachmentsSerializer(
                contact.contact_attachment.all(), 
                many=True
            ).data,
            "comments": CommentSerializer(
                contact.contact_comments.all(),
                many=True
            ).data,
            "tasks": TaskSerializer(
                contact.contacts_tasks.all(),
                many=True
            ).data,
            "countries": COUNTRIES
        })

    def put(self, request, pk):
        contact = self.get_object(pk)
        
        # Check access
        if contact.org != request.profile.org:
            return Response(
                {"error": "Organization mismatch"},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.profile.is_admin:
            if not (
                request.profile == contact.created_by or
                request.profile in contact.assigned_to.all()
            ):
                return Response(
                    {"error": "Permission denied"},
                    status=status.HTTP_403_FORBIDDEN
                )

        contact_serializer = CreateContactSerializer(
            instance=contact,
            data=request.data,
            request_obj=request
        )
        address_serializer = BillingAddressSerializer(
            instance=contact.address,
            data=request.data
        )

        if not all([contact_serializer.is_valid(), address_serializer.is_valid()]):
            return Response(
                {
                    "contact_errors": contact_serializer.errors,
                    "address_errors": address_serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update information
        address = address_serializer.save()
        contact = contact_serializer.save(
            date_of_birth=request.data.get("date_of_birth"),
            address=address
        )

        # Update teams
        if request.data.get("teams"):
            contact.teams.clear()
            teams = Teams.objects.filter(
                id__in=request.data.get("teams"),
                org=request.profile.org
            )
            contact.teams.add(*teams)

        # Update users
        if request.data.get("assigned_to"):
            old_assigned = set(contact.assigned_to.values_list("id", flat=True))
            contact.assigned_to.clear()
            
            profiles = Profile.objects.filter(
                id__in=request.data.get("assigned_to"),
                org=request.profile.org
            )
            contact.assigned_to.add(*profiles)
            
            # Send email to new users
            new_assigned = set(profiles.values_list("id", flat=True))
            recipients = list(new_assigned - old_assigned)
            if recipients:
                send_email_to_assigned_user.delay(recipients, contact.id)

        return Response(
            {"message": "Contact updated successfully"},
            status=status.HTTP_200_OK
        )

    def delete(self, request, pk):
        contact = self.get_object(pk)
        
        # Check access
        if contact.org != request.profile.org:
            return Response(
                {"error": "Organization mismatch"},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.profile.is_admin and request.profile != contact.created_by:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        if contact.address:
            contact.address.delete()
        contact.delete()

        return Response(
            {"message": "Contact deleted successfully"},
            status=status.HTTP_200_OK
        )


class ContactCommentView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        contact = get_object_or_404(Contact, pk=pk)
        
        # Check access
        if contact.org != request.profile.org:
            return Response(
                {"error": "Organization mismatch"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(
                contact=contact,
                commented_by=request.profile,
                org=request.profile.org
            )
            return Response(
                {"message": "Comment added successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class ContactAttachmentView(APIView):
    permission_classes = (IsAuthenticated,)

    def delete(self, request, pk):
        attachment = get_object_or_404(Attachments, pk=pk)
        
        # Check access
        if not request.profile.is_admin and request.profile != attachment.created_by:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        attachment.delete()
        return Response(
            {"message": "Attachment deleted successfully"},
            status=status.HTTP_200_OK
        )
