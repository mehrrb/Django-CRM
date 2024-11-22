from django.contrib import admin
from .models import Address, Document, Org, Profile, Comment, Attachments, APISettings

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('city', 'state', 'country', 'created_at', 'updated_at')
    list_filter = ('country', 'state', 'created_at')
    search_fields = ('city', 'state', 'country', 'address_line')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'org', 'status', 'created_at')
    list_filter = ('status', 'org', 'created_at')
    search_fields = ('title', 'created_by__email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Org)
class OrgAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name',)
    readonly_fields = ('created_at',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'org', 'role', 'created_at')
    list_filter = ('role', 'org', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment', 'created_by', 'created_at')
    search_fields = ('comment', 'created_by__email')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Attachments)
class AttachmentsAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'created_by', 'created_at')
    search_fields = ('file_name', 'created_by__email')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(APISettings)
class APISettingsAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'org', 'created_at')
    list_filter = ('org', 'created_at')
    search_fields = ('title', 'created_by__email', 'org__name', 'website')
    readonly_fields = ('created_at', 'updated_at')
