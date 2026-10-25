
from django.contrib import admin
from .models import Organization, Opportunity, Application

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "org_type", "city")
    search_fields = ("name",)

@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ("title", "field", "city", "organization", "is_active")
    list_filter = ("field", "city", "is_active")
    search_fields = ("title", "description")

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("student", "opportunity", "status", "created_at")
    list_filter = ("status",)
