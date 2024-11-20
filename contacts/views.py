from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone

from .models import Contact
from .serializers import (
    ContactSerializer,
    ContactCreateSerializer,
    ContactDetailSerializer,
    TaskSerializer,
    ContactAttachmentSerializer,
    ContactCommentSerializer
)
from common.models import Comment, Attachments, Profile
from common.serializers import (
    CommentSerializer, 
    AttachmentSerializer,
    BillingAddressSerializer
)
from common.utils import COUNTRIES
from teams.models import Teams
from contacts.tasks import send_email_to_assigned_user

class ContactViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination
    
    def get_queryset(self):
        params = self.request.query_params
        queryset = Contact.objects.filter(org=self.request.profile.org).order_by('-id')
        
        # Filter based on user role
        if not self.request.profile.is_admin:
            queryset = queryset.filter(
                Q(created_by=self.request.profile.user) |  # Changed from self.request.profile
                Q(assigned_to=self.request.profile)
            ).distinct()

        # Apply filters
        if params.get('name'):
            queryset = queryset.filter(
                Q(first_name__icontains=params.get('name')) |
                Q(last_name__icontains=params.get('name'))
            )
        if params.get('email'):
            queryset = queryset.filter(primary_email__icontains=params.get('email'))
        if params.get('phone'):
            queryset = queryset.filter(mobile_number__icontains=params.get('phone'))
        if params.get('city'):
            queryset = queryset.filter(address__city__icontains=params.get('city'))
        if params.getlist('assigned_to'):
            queryset = queryset.filter(
                assigned_to__id__in=params.getlist('assigned_to')
            ).distinct()
            
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return ContactCreateSerializer
        elif self.action == 'retrieve':
            return ContactDetailSerializer
        return ContactSerializer

    def perform_create(self, serializer):
        # Create address first if provided
        address = None
        if self.request.data.get('address'):
            address_serializer = BillingAddressSerializer(data=self.request.data.get('address'))
            if address_serializer.is_valid():
                address = address_serializer.save()
            else:
                raise serializers.ValidationError(address_serializer.errors)

        contact = serializer.save(
            org=self.request.profile.org,
            created_by=self.request.user,  # Changed from self.request.profile
            address=address
        )
        
        # Add teams if provided
        if self.request.data.get('teams'):
            teams = Teams.objects.filter(
                id__in=self.request.data.get('teams'),
                org=self.request.profile.org
            )
            contact.teams.add(*teams)

        # Add assigned users if provided
        if self.request.data.get('assigned_to'):
            profiles = Profile.objects.filter(
                id__in=self.request.data.get('assigned_to'),
                org=self.request.profile.org
            )
            contact.assigned_to.add(*profiles)
            
            recipients = list(profiles.values_list('id', flat=True))
            send_email_to_assigned_user.delay(recipients, contact.id)

    def perform_update(self, serializer):
        contact = self.get_object()
        
        # Update address if provided
        if self.request.data.get('address'):
            if contact.address:
                address_serializer = BillingAddressSerializer(
                    contact.address,
                    data=self.request.data.get('address')
                )
            else:
                address_serializer = BillingAddressSerializer(
                    data=self.request.data.get('address')
                )
                
            if address_serializer.is_valid():
                address = address_serializer.save()
            else:
                raise serializers.ValidationError(address_serializer.errors)
        else:
            address = contact.address

        contact = serializer.save(address=address)

    def perform_destroy(self, instance):
        if not self.request.profile.role == "ADMIN":
            raise PermissionDenied("You don't have permission to delete this contact.")
        instance.delete()

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        contact = self.get_object()
        from contacts.serializers import ContactCommentSerializer
        serializer = ContactCommentSerializer(data=request.data)
        
        if serializer.is_valid():
            comment = Comment.objects.create(
                comment=serializer.validated_data['comment'],
                user=request.profile.user,
                contact=contact,
                org=request.profile.org,
                created_at=timezone.now()
            )
            return Response(
                CommentSerializer(comment).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        contact = self.get_object()
        tasks = contact.contacts_tasks.all()
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def attachments(self, request, pk=None):
        contact = self.get_object()
        
        if 'attachment' not in request.FILES:
            print("Files in request:", request.FILES)  # For debugging
            return Response(
                {'error': 'No attachment provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            file = request.FILES['attachment']
            attachment = Attachments.objects.create(
                attachment=file,
                created_by=request.profile.user,
                contact=contact,
                org=request.profile.org
            )
            return Response(
                AttachmentSerializer(attachment).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            print("Error creating attachment:", str(e))  # For debugging
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'])
    def remove_attachment(self, request, pk=None):
        attachment_id = request.query_params.get('attachment_id')
        if not attachment_id:
            return Response(
                {'error': 'attachment_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        attachment = get_object_or_404(
            Attachments,
            id=attachment_id,
            contact=self.get_object(),
            org=request.profile.org
        )
        
        if not request.profile.is_admin and request.profile != attachment.created_by:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        attachment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)