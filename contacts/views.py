from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import Contact
from .serializers import (
    ContactSerializer,
    ContactCreateSerializer,
    ContactDetailSerializer,
    TaskSerializer
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
                Q(created_by=self.request.profile) | 
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
        # Create address first
        address_serializer = BillingAddressSerializer(data=self.request.data)
        if address_serializer.is_valid():
            address = address_serializer.save()
        else:
            raise serializers.ValidationError(address_serializer.errors)

        contact = serializer.save(
            org=self.request.profile.org,
            created_by=self.request.profile,
            address=address
        )
        
        # Add teams
        if self.request.data.get('teams'):
            teams = Teams.objects.filter(
                id__in=self.request.data.get('teams'),
                org=self.request.profile.org
            )
            contact.teams.add(*teams)

        # Add assigned users and send emails
        if self.request.data.get('assigned_to'):
            profiles = Profile.objects.filter(
                id__in=self.request.data.get('assigned_to'),
                org=self.request.profile.org
            )
            contact.assigned_to.add(*profiles)
            
            recipients = list(profiles.values_list('id', flat=True))
            send_email_to_assigned_user.delay(recipients, contact.id)

        # Handle attachments
        if self.request.FILES.get('contact_attachment'):
            Attachments.objects.create(
                created_by=self.request.profile.user,
                file_name=self.request.FILES.get('contact_attachment').name,
                contact=contact,
                attachment=self.request.FILES.get('contact_attachment'),
                org=self.request.profile.org
            )

    def perform_update(self, serializer):
        contact = self.get_object()
        
        # Update address
        address_serializer = BillingAddressSerializer(
            instance=contact.address,
            data=self.request.data
        )
        if address_serializer.is_valid():
            address = address_serializer.save()
        else:
            raise serializers.ValidationError(address_serializer.errors)

        contact = serializer.save(address=address)
        
        # Update teams
        if self.request.data.get('teams'):
            contact.teams.clear()
            teams = Teams.objects.filter(
                id__in=self.request.data.get('teams'),
                org=self.request.profile.org
            )
            contact.teams.add(*teams)

        # Update assigned users
        if self.request.data.get('assigned_to'):
            old_assigned = set(contact.assigned_to.values_list('id', flat=True))
            contact.assigned_to.clear()
            
            profiles = Profile.objects.filter(
                id__in=self.request.data.get('assigned_to'),
                org=self.request.profile.org
            )
            contact.assigned_to.add(*profiles)
            
            # Send email to new users
            new_assigned = set(profiles.values_list('id', flat=True))
            recipients = list(new_assigned - old_assigned)
            if recipients:
                send_email_to_assigned_user.delay(recipients, contact.id)

    def destroy(self, request, *args, **kwargs):
        contact = self.get_object()
        
        if not request.profile.is_admin and request.profile != contact.created_by:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        if contact.address:
            contact.address.delete()
        contact.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        contact = self.get_object()
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(
                commented_by=request.profile,
                contact=contact,
                org=request.profile.org
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
    def add_attachment(self, request, pk=None):
        contact = self.get_object()
        serializer = AttachmentSerializer(data=request.data)
        if serializer.is_valid():
            attachment = serializer.save(
                created_by=request.profile,
                contact=contact,
                org=request.profile.org
            )
            return Response(
                AttachmentSerializer(attachment).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
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