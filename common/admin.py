from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from common.models import Address, Comment, User, Attachments

class AddressInline(admin.StackedInline):
    model = Address
    extra = 1

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'get_username', 'is_active', 'is_staff', 'get_date_joined')
    list_filter = ('is_active', 'is_staff', 'groups')
    search_fields = ('email', 'username')
    ordering = ('email',)

    def get_username(self, obj):
        return obj.username
    get_username.short_description = 'Username'

    def get_date_joined(self, obj):
        return obj.date_joined
    get_date_joined.short_description = 'Date Joined'

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )

class CommentAdmin(admin.ModelAdmin):
    list_display = ('comment', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('comment', 'created_by__email')

class AttachmentsAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('file_name', 'created_by__email')

admin.site.register(User, CustomUserAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Attachments, AttachmentsAdmin)
admin.site.register(Address)
