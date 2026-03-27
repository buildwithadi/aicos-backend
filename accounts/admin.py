from django.contrib import admin
from .models import Permission, Role, UserRole

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename', 'module')
    search_fields = ('name', 'codename', 'module')
    list_filter = ('module',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'school')
    search_fields = ('name', 'school__name')
    list_filter = ('school',)
    filter_horizontal = ('permissions',) # Makes adding permissions in admin UI much easier

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'school')
    search_fields = ('user__email', 'role__name', 'school__name')
    list_filter = ('school', 'role')