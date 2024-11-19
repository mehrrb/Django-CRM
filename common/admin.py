from django.contrib import admin
from .models import Address, Document, Org, Profile, Comment, Attachments, APISettings

admin.site.register(Address)
admin.site.register(Document)
admin.site.register(Org)
admin.site.register(Profile)
admin.site.register(Comment)
admin.site.register(Attachments)
admin.site.register(APISettings)
