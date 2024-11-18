from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import LimitOffsetPagination

from accounts.models import Account, Tags
from accounts.serializer import (
    AccountCreateSerializer,
    AccountSerializer,
    TagsSerailizer,
)
from common.models import Attachments, Comment, Profile
from common.serializer import (
    AttachmentsSerializer,
    CommentSerializer,
)
from common.utils import COUNTRIES, INDCHOICES
from contacts.models import Contact
from teams.models import Teams
from teams.serializer import TeamsSerializer


class AccountsListView(APIView, LimitOffsetPagination):
    permission_classes = (IsAuthenticated,)
    model = Account

    def get_context_data(self, **kwargs):
        params = self.request.query_params
        queryset = self.model.objects.filter(org=self.request.profile.org).order_by("-id")
        
        # فیلتر براساس نقش کاربر
        if not self.request.profile.is_admin:
            queryset = queryset.filter(
                Q(created_by=self.request.profile.user) | 
                Q(assigned_to=self.request.profile)
            ).distinct()

        # اعمال فیلترها
        if params.get("name"):
            queryset = queryset.filter(name__icontains=params.get("name"))
        if params.get("city"):
            queryset = queryset.filter(billing_city__contains=params.get("city"))
        if params.get("industry"):
            queryset = queryset.filter(industry__icontains=params.get("industry"))
        if params.get("tags"):
            queryset = queryset.filter(tags__in=params.get("tags")).distinct()

        context = {
            "accounts": AccountSerializer(queryset, many=True).data,
            "teams": TeamsSerializer(Teams.objects.filter(org=self.request.profile.org), many=True).data,
            "countries": COUNTRIES,
            "industries": INDCHOICES,
            "tags": TagsSerailizer(Tags.objects.all(), many=True).data,
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return Response(context)

    def post(self, request, *args, **kwargs):
        serializer = AccountCreateSerializer(data=request.data, request_obj=request)
        
        if serializer.is_valid():
            account = serializer.save(org=request.profile.org)
            
            # اضافه کردن تیم‌ها
            if request.data.get("teams"):
                teams = Teams.objects.filter(
                    id__in=request.data.get("teams"),
                    org=request.profile.org
                )
                account.teams.add(*teams)

            # اضافه کردن تگ‌ها
            if request.data.get("tags"):
                for tag_name in request.data.get("tags"):
                    tag, _ = Tags.objects.get_or_create(name=tag_name)
                    account.tags.add(tag)

            return Response(
                {"message": "Account created successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class AccountDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self, pk):
        return get_object_or_404(Account, id=pk)

    def get(self, request, pk):
        account = self.get_object(pk)
        
        # بررسی دسترسی
        if account.org != request.profile.org:
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        # بررسی مجوز کامنت
        can_comment = (
            request.profile == account.created_by or 
            request.profile.is_admin
        )

        context = {
            "account": AccountSerializer(account).data,
            "attachments": AttachmentsSerializer(account.account_attachment.all(), many=True).data,
            "comments": CommentSerializer(account.accounts_comments.all(), many=True).data,
            "can_comment": can_comment,
            "teams": TeamsSerializer(Teams.objects.filter(org=request.profile.org), many=True).data,
            "countries": COUNTRIES,
            "industries": INDCHOICES,
        }
        return Response(context)

    def put(self, request, pk):
        account = self.get_object(pk)

        # بررسی دسترسی
        if account.org != request.profile.org:
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AccountCreateSerializer(
            account,
            data=request.data,
            request_obj=request
        )

        if serializer.is_valid():
            account = serializer.save()
            
            # بروزرسانی تیم‌ها
            if request.data.get("teams"):
                account.teams.clear()
                teams = Teams.objects.filter(
                    id__in=request.data.get("teams"),
                    org=request.profile.org
                )
                account.teams.add(*teams)

            # بروزرسانی تگ‌ها
            if request.data.get("tags"):
                account.tags.clear()
                for tag_name in request.data.get("tags"):
                    tag, _ = Tags.objects.get_or_create(name=tag_name)
                    account.tags.add(tag)

            return Response(
                {"message": "Account updated successfully"},
                status=status.HTTP_200_OK
            )
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        account = self.get_object(pk)

        # بررسی دسترسی
        if account.org != request.profile.org:
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        if not request.profile.is_admin and request.profile != account.created_by:
            return Response(
                {"error": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        account.delete()
        return Response(
            {"message": "Account deleted successfully"},
            status=status.HTTP_200_OK
        )


class AccountCommentView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        account = get_object_or_404(Account, pk=pk)
        
        if account.org != request.profile.org:
            return Response(
                {"error": "Access denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                account=account,
                commented_by=request.profile
            )
            return Response(
                {"message": "Comment added successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )


class AccountCreateMailView(APIView):
    permission_classes = (IsAuthenticated,)
    model = Account

    def get_object(self, pk):
        return get_object_or_404(Account, pk=pk)

    def post(self, request, pk, *args, **kwargs):
        account = self.get_object(pk)
        
        # Check permissions
        if account.org != request.profile.org:
            return Response(
                {"error": "You don't have permission to create mail for this account"},
                status=403
            )

        # Here you would typically create and send the email
        # This is just a placeholder response
        return Response({
            "message": "Email creation initiated for account",
            "account": account.name
        })

    def get(self, request, pk, *args, **kwargs):
        account = self.get_object(pk)
        
        # Check permissions
        if account.org != request.profile.org:
            return Response(
                {"error": "You don't have permission to view this account's mail"},
                status=403
            )

        # Return email templates or configuration
        return Response({
            "account": account.name,
            "email_templates": [],  # Add your email templates here
            "available_configurations": []  # Add your configurations here
        })


class AccountAttachmentView(APIView):
    permission_classes = (IsAuthenticated,)
    
    def get_object(self, pk):
        return get_object_or_404(Attachments, pk=pk)

    def get(self, request, pk):
        attachment = self.get_object(pk)
        
        # Check permissions
        if attachment.org != request.profile.org:
            return Response(
                {"error": "You don't have permission to view this attachment"},
                status=403
            )
            
        serializer = AttachmentsSerializer(attachment)
        return Response(serializer.data)

    def delete(self, request, pk):
        attachment = self.get_object(pk)
        
        # Check permissions
        if attachment.org != request.profile.org:
            return Response(
                {"error": "You don't have permission to delete this attachment"},
                status=403
            )
            
        attachment.delete()
        return Response({"message": "Attachment deleted successfully"})

    def put(self, request, pk):
        attachment = self.get_object(pk)
        
        # Check permissions
        if attachment.org != request.profile.org:
            return Response(
                {"error": "You don't have permission to update this attachment"},
                status=403
            )
            
        serializer = AttachmentsSerializer(attachment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
