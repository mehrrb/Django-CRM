from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Account, Tags
from emails.models import Email
from .serializers import (
    AccountSerializer,
    AccountCreateSerializer,
    AccountDetailSerializer, 
    TagsSerializer,
    EmailSerializer,
    AccountBulkActionSerializer,
    AccountSwaggerSerializer
)
from common.models import Comment, Attachments, Profile
from common.serializers import CommentSerializer, AttachmentSerializer
from teams.models import Teams
from teams.serializers import TeamsSerializer
from accounts.tasks import send_account_assigned_emails
from common.utils import COUNTRIES, INDCHOICES

class AccountViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination
    
    def get_queryset(self):
        params = self.request.query_params
        queryset = Account.objects.filter(org=self.request.profile.org).order_by('-created_at')
        
        # Filter based on user role
        if not self.request.profile.is_admin and self.request.profile.role != "ADMIN":
            queryset = queryset.filter(
                Q(created_by=self.request.profile) | 
                Q(assigned_to=self.request.profile)
            ).distinct()

        # Apply filters
        if params.get('name'):
            queryset = queryset.filter(name__icontains=params.get('name'))
        if params.get('city'):
            queryset = queryset.filter(billing_city__contains=params.get('city'))
        if params.get('industry'):
            queryset = queryset.filter(industry__icontains=params.get('industry'))
        if params.get('tags'):
            queryset = queryset.filter(tags__in=params.get('tags')).distinct()
        if params.getlist('assigned_to'):
            queryset = queryset.filter(
                assigned_to__id__in=params.getlist('assigned_to')
            ).distinct()
        if params.get('teams'):
            queryset = queryset.filter(teams__id__in=params.getlist('teams')).distinct()
            
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return AccountCreateSerializer
        elif self.action == 'retrieve':
            return AccountDetailSerializer
        return AccountSerializer

    @extend_schema(
        tags=["Accounts"],
        request=AccountSwaggerSerializer
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, request_obj=request)
        if serializer.is_valid():
            account = serializer.save(
                created_by=request.profile,
                org=request.profile.org
            )
            
            # Handle assigned users
            if request.data.get('assigned_to'):
                profiles = Profile.objects.filter(
                    id__in=request.data.get('assigned_to'),
                    org=request.profile.org,
                    is_active=True
                )
                account.assigned_to.add(*profiles)
                
                # Send email notifications
                recipients = list(profiles.values_list('id', flat=True))
                send_account_assigned_emails.delay(recipients, account.id)

            # Handle teams
            if request.data.get('teams'):
                teams = Teams.objects.filter(
                    id__in=request.data.get('teams'),
                    org=request.profile.org
                )
                account.teams.add(*teams)

            # Handle tags
            if request.data.get('tags'):
                for tag_name in request.data.get('tags'):
                    tag, _ = Tags.objects.get_or_create(name=tag_name)
                    account.tags.add(tag)

            # Handle attachments
            if request.FILES.getlist('attachments'):
                for attachment in request.FILES.getlist('attachments'):
                    Attachments.objects.create(
                        created_by=request.profile,
                        file_name=attachment.name,
                        account=account,
                        attachment=attachment,
                        org=request.profile.org
                    )

            return Response(
                {"error": False, "message": "Account Created Successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        tags=["Accounts"],
        request=AccountSwaggerSerializer
    )
    def update(self, request, *args, **kwargs):
        account = self.get_object()
        old_assigned = set(account.assigned_to.values_list('id', flat=True))
        
        serializer = self.get_serializer(account, data=request.data, partial=True)
        if serializer.is_valid():
            account = serializer.save()
            
            # Update assigned users
            if 'assigned_to' in request.data:
                account.assigned_to.clear()
                if request.data.get('assigned_to'):
                    profiles = Profile.objects.filter(
                        id__in=request.data.get('assigned_to'),
                        org=request.profile.org,
                        is_active=True
                    )
                    account.assigned_to.add(*profiles)
                    
                    # Send email to new assignees
                    new_assigned = set(profiles.values_list('id', flat=True))
                    recipients = list(new_assigned - old_assigned)
                    if recipients:
                        send_account_assigned_emails.delay(recipients, account.id)

            # Update teams
            if 'teams' in request.data:
                account.teams.clear()
                if request.data.get('teams'):
                    teams = Teams.objects.filter(
                        id__in=request.data.get('teams'),
                        org=request.profile.org
                    )
                    account.teams.add(*teams)

            # Update tags
            if 'tags' in request.data:
                account.tags.clear()
                if request.data.get('tags'):
                    for tag_name in request.data.get('tags'):
                        tag, _ = Tags.objects.get_or_create(name=tag_name)
                        account.tags.add(tag)

            return Response(
                {"error": False, "message": "Account Updated Successfully"},
                status=status.HTTP_200_OK
            )
        return Response(
            {"error": True, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(tags=["Accounts"])
    def destroy(self, request, *args, **kwargs):
        account = self.get_object()
        
        if not request.profile.is_admin and request.profile != account.created_by:
            return Response(
                {'error': True, 'errors': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        account.delete()
        return Response(
            {'error': False, 'message': 'Account deleted successfully'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        account = self.get_object()
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(
                commented_by=request.profile,
                account=account,
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

    @action(detail=True, methods=['post'])
    def add_attachment(self, request, pk=None):
        account = self.get_object()
        serializer = AttachmentSerializer(data=request.data)
        if serializer.is_valid():
            attachment = serializer.save(
                created_by=request.profile,
                account=account,
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
                {'error': True, 'errors': 'attachment_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        attachment = get_object_or_404(
            Attachments,
            id=attachment_id,
            account=self.get_object(),
            org=request.profile.org
        )
        
        if not request.profile.is_admin and request.profile != attachment.created_by:
            return Response(
                {'error': True, 'errors': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        attachment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on accounts"""
        serializer = AccountBulkActionSerializer(data=request.data)
        if serializer.is_valid():
            accounts = Account.objects.filter(
                id__in=serializer.validated_data['account_ids'],
                org=request.profile.org
            )
            
            if serializer.validated_data.get('assigned_to'):
                profiles = Profile.objects.filter(
                    id__in=serializer.validated_data['assigned_to'],
                    org=request.profile.org,
                    is_active=True
                )
                for account in accounts:
                    account.assigned_to.set(profiles)
                    
            if serializer.validated_data.get('teams'):
                teams = Teams.objects.filter(
                    id__in=serializer.validated_data['teams'],
                    org=request.profile.org
                )
                for account in accounts:
                    account.teams.set(teams)
                    
            if serializer.validated_data.get('status'):
                accounts.update(status=serializer.validated_data['status'])
                    
            return Response(
                {'error': False, 'message': 'Accounts updated successfully'},
                status=status.HTTP_200_OK
            )
        return Response(
            {'error': True, 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def update_tags(self, request, pk=None):
        account = self.get_object()
        tags = request.data.get('tags', [])
        
        account.tags.clear()
        for tag_name in tags:
            tag, _ = Tags.objects.get_or_create(name=tag_name)
            account.tags.add(tag)
            
        return Response(
            {'error': False, 'message': 'Tags updated successfully'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post', 'get'])
    def email(self, request, pk=None):
        account = self.get_object()
        
        if request.method == 'GET':
            return Response({
                'error': False,
                'data': {
                    'account': account.name,
                    'email_templates': [],  # Add your email templates here
                    'available_configurations': []  # Add your configurations here
                }
            })
            
        # POST method - create and send email
        serializer = EmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.save(
                created_by=request.profile,
                account=account,
                org=request.profile.org
            )
            return Response(
                {'error': False, 'message': 'Email sent successfully'},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'error': True, 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

class TagsViewSet(viewsets.ModelViewSet):
    queryset = Tags.objects.all()
    serializer_class = TagsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Tags.objects.filter(org=self.request.profile.org)

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.profile,
            org=self.request.profile.org
        )