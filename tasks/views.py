from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from .models import Task
from .serializers import (
    TaskSerializer,
    TaskCreateSerializer,
    TaskDetailSerializer,
    TaskCommentSerializer,
    TaskAttachmentSerializer,
    TaskBulkActionSerializer
)
from common.models import Comment, Attachments, Profile
from common.serializers import CommentSerializer, AttachmentSerializer
from contacts.models import Contact
from contacts.serializers import ContactSerializer
from accounts.models import Account
from accounts.serializers import AccountSerializer
from teams.models import Teams
from teams.serializers import TeamsSerializer
from tasks.utils import PRIORITY_CHOICES, STATUS_CHOICES
from tasks.tasks import send_task_assigned_emails

class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination
    
    def get_queryset(self):
        params = self.request.query_params
        queryset = Task.objects.filter(org=self.request.profile.org).order_by('-created_at')
        
        # Filter based on user role
        if not self.request.profile.is_admin:
            queryset = queryset.filter(
                Q(created_by=self.request.profile) | 
                Q(assigned_to=self.request.profile)
            ).distinct()

        # Apply filters
        if params.get('title'):
            queryset = queryset.filter(title__icontains=params.get('title'))
        if params.get('status'):
            queryset = queryset.filter(status=params.get('status'))
        if params.get('priority'):
            queryset = queryset.filter(priority=params.get('priority'))
        if params.getlist('assigned_to'):
            queryset = queryset.filter(
                assigned_to__id__in=params.getlist('assigned_to')
            ).distinct()
        if params.get('due_date'):
            queryset = queryset.filter(due_date=params.get('due_date'))
            
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return TaskCreateSerializer
        elif self.action == 'retrieve':
            return TaskDetailSerializer
        return TaskSerializer

    @extend_schema(
        tags=["Tasks"],
        description="Create a new task",
        request=TaskCreateSerializer
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            task = serializer.save(
                created_by=request.profile,
                org=request.profile.org
            )
            
            # Handle contacts
            if request.data.get('contacts'):
                contacts = Contact.objects.filter(
                    id__in=request.data.get('contacts'),
                    org=request.profile.org
                )
                task.contacts.add(*contacts)

            # Handle teams
            if request.data.get('teams'):
                teams = Teams.objects.filter(
                    id__in=request.data.get('teams'),
                    org=request.profile.org
                )
                task.teams.add(*teams)

            # Handle assigned users
            if request.data.get('assigned_to'):
                profiles = Profile.objects.filter(
                    id__in=request.data.get('assigned_to'),
                    org=request.profile.org,
                    is_active=True
                )
                task.assigned_to.add(*profiles)
                
                recipients = list(profiles.values_list('id', flat=True))
                send_task_assigned_emails.delay(recipients, task.id)

            return Response(
                TaskDetailSerializer(task).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @extend_schema(
        tags=["Tasks"],
        description="Update a task",
        request=TaskCreateSerializer
    )
    def update(self, request, *args, **kwargs):
        task = self.get_object()
        serializer = self.get_serializer(task, data=request.data, partial=True)
        
        if serializer.is_valid():
            # Save old assigned users for email notification
            old_assigned = set(task.assigned_to.values_list('id', flat=True))
            
            task = serializer.save()
            
            # Update contacts
            if 'contacts' in request.data:
                task.contacts.clear()
                if request.data.get('contacts'):
                    contacts = Contact.objects.filter(
                        id__in=request.data.get('contacts'),
                        org=request.profile.org
                    )
                    task.contacts.add(*contacts)

            # Update teams
            if 'teams' in request.data:
                task.teams.clear()
                if request.data.get('teams'):
                    teams = Teams.objects.filter(
                        id__in=request.data.get('teams'),
                        org=request.profile.org
                    )
                    task.teams.add(*teams)

            # Update assigned users
            if 'assigned_to' in request.data:
                task.assigned_to.clear()
                if request.data.get('assigned_to'):
                    profiles = Profile.objects.filter(
                        id__in=request.data.get('assigned_to'),
                        org=request.profile.org,
                        is_active=True
                    )
                    task.assigned_to.add(*profiles)
                    
                    # Send email to new assignees
                    new_assigned = set(profiles.values_list('id', flat=True))
                    recipients = list(new_assigned - old_assigned)
                    if recipients:
                        send_task_assigned_emails.delay(recipients, task.id)

            return Response(TaskDetailSerializer(task).data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        task = self.get_object()
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(
                commented_by=request.profile,
                task=task,
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
        task = self.get_object()
        serializer = AttachmentSerializer(data=request.data)
        if serializer.is_valid():
            attachment = serializer.save(
                created_by=request.profile,
                task=task,
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
            task=self.get_object(),
            org=request.profile.org
        )
        
        if not request.profile.is_admin and request.profile != attachment.created_by:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        attachment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        task.status = 'completed'
        task.completed_by = request.profile
        task.completed_at = timezone.now()
        task.save()
        
        return Response(TaskDetailSerializer(task).data)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get task statistics for dashboard"""
        tasks = self.get_queryset()
        return Response({
            'total': tasks.count(),
            'completed': tasks.filter(status='completed').count(),
            'pending': tasks.filter(status='pending').count(),
            'in_progress': tasks.filter(status='in_progress').count(),
            'overdue': tasks.filter(
                due_date__lt=timezone.now().date(),
                status__in=['pending', 'in_progress']
            ).count()
        })

    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on tasks"""
        serializer = TaskBulkActionSerializer(data=request.data)
        if serializer.is_valid():
            tasks = Task.objects.filter(
                id__in=serializer.validated_data['task_ids'],
                org=request.profile.org
            )
            
            if serializer.validated_data.get('status'):
                tasks.update(status=serializer.validated_data['status'])
                
            if serializer.validated_data.get('assigned_to'):
                profiles = Profile.objects.filter(
                    id__in=serializer.validated_data['assigned_to'],
                    org=request.profile.org
                )
                for task in tasks:
                    task.assigned_to.set(profiles)
                    
            return Response({'status': 'Tasks updated successfully'})
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
