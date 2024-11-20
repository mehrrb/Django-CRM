from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.mail import EmailMessage
from django.conf import settings
from django.shortcuts import get_object_or_404
from .models import Email
from .serializers import EmailSerializer

class EmailViewSet(viewsets.ModelViewSet):
    serializer_class = EmailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Email.objects.filter(user=self.request.user)
        if self.action == 'sent':
            return queryset.filter(is_sent=True)
        elif self.action == 'trash':
            return queryset.filter(is_trash=True)
        elif self.action == 'draft':
            return queryset.filter(is_draft=True)
        elif self.action == 'important':
            return queryset.filter(is_important=True)
        return queryset
    
    def perform_create(self, serializer):
        email = serializer.save(user=self.request.user)
        if not email.is_draft:
            # Send actual email
            email_message = EmailMessage(
                subject=email.subject,
                body=email.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email.to_email]
            )
            email_message.send()
            email.is_sent = True
            email.save()
    
    @action(detail=False, methods=['get'])
    def sent(self, request):
        return self.list(request)
    
    @action(detail=False, methods=['get'])
    def trash(self, request):
        return self.list(request)
    
    @action(detail=False, methods=['get'])
    def draft(self, request):
        return self.list(request)
    
    @action(detail=False, methods=['get'])
    def important(self, request):
        return self.list(request)
    
    @action(detail=True, methods=['post'])
    def move_to_trash(self, request, pk=None):
        email = self.get_object()
        email.is_trash = True
        email.save()
        return Response({'status': 'success'})
    
    @action(detail=True, methods=['post'])
    def mark_as_important(self, request, pk=None):
        email = self.get_object()
        email.is_important = True
        email.save()
        return Response({'status': 'success'})
    
    @action(detail=True, methods=['post'])
    def mark_as_not_important(self, request, pk=None):
        email = self.get_object()
        email.is_important = False
        email.save()
        return Response({'status': 'success'})
    
    @action(detail=True, methods=['post'])
    def send_draft(self, request, pk=None):
        email = self.get_object()
        if email.is_draft:
            email_message = EmailMessage(
                subject=email.subject,
                body=email.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email.to_email]
            )
            email_message.send()
            email.is_draft = False
            email.is_sent = True
            email.save()
            return Response({'status': 'success'})
        return Response(
            {'status': 'error', 'message': 'This email is not a draft'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['delete'])
    def permanent_delete(self, request, pk=None):
        """Permanently delete an email (from trash)"""
        email = self.get_object()
        if email.is_trash:
            email.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'status': 'error', 'message': 'Email must be in trash to delete permanently'},
            status=status.HTTP_400_BAD_REQUEST
        )
