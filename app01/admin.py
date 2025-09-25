from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import (
    User,
    Task,
    TaskStatusLog,
    Station,
    ContainerSpec,
    Container,
    ContainerSlot,
    TestTube15,
    LaiyuPowder,
    JingtaiPowder,
    ReagentBottle150,
)

# 自定义用户创建表单
class CustomUserCreationForm(UserCreationForm):
    """自定义用户创建表单，支持备料员角色"""
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role', 'department', 'phone')

# 自定义用户修改表单
class CustomUserChangeForm(UserChangeForm):
    """自定义用户修改表单，支持备料员角色"""
    class Meta(UserChangeForm.Meta):
        model = User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """自定义用户管理"""
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    
    list_display = ('username', 'email', 'role', 'department', 'is_active', 'date_joined', 'last_login')
    list_filter = ('role', 'is_active', 'department', 'date_joined')
    search_fields = ('username', 'email', 'department')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('first_name', 'last_name', 'email')}),
        ('权限', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('其他信息', {'fields': ('department', 'phone', 'date_joined', 'last_login')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'department', 'phone'),
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """确保使用正确的表单"""
        if obj is None:  # 添加用户
            return self.add_form
        return self.form
    
    def add_view(self, request, form_url='', extra_context=None):
        """重写添加用户视图，确保使用自定义表单"""
        self.add_form = CustomUserCreationForm
        return super().add_view(request, form_url, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """重写修改用户视图，确保使用自定义表单"""
        self.form = CustomUserChangeForm
        return super().change_view(request, object_id, form_url, extra_context)
    
    def get_fieldsets(self, request, obj=None):
        """动态获取字段集"""
        if obj is None:  # 添加用户
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)
    
    def get_fields(self, request, obj=None):
        """动态获取字段"""
        if obj is None:  # 添加用户
            return self.add_fieldsets[0][1]['fields']
        return super().get_fields(request, obj)
    
    def save_model(self, request, obj, form, change):
        """保存模型时确保角色字段被正确处理"""
        if not change:  # 新用户
            if hasattr(form, 'cleaned_data') and 'role' in form.cleaned_data:
                obj.role = form.cleaned_data['role']
        super().save_model(request, obj, form, change)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """任务管理"""
    list_display = ('name', 'created_by', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'created_by')
    search_fields = ('name', 'created_by__username')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('基本信息', {'fields': ('name', 'created_by', 'status')}),
        ('详细信息', {'fields': ('date', 'remark', 'stations')}),
        ('时间信息', {'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(TaskStatusLog)
class TaskStatusLogAdmin(admin.ModelAdmin):
    """任务状态日志管理"""
    list_display = ('task', 'from_status', 'to_status', 'changed_by', 'changed_at')
    list_filter = ('from_status', 'to_status', 'changed_at', 'changed_by')
    search_fields = ('task__name', 'changed_by__username')
    ordering = ('-changed_at',)
    
    fieldsets = (
        ('任务信息', {'fields': ('task', 'from_status', 'to_status')}),
        ('变更信息', {'fields': ('changed_by', 'changed_at', 'reason')}),
    )
    
    readonly_fields = ('changed_at',)


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ("name", "desc", "created_at", "updated_at")
    search_fields = ("name",)
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(ContainerSpec)
class ContainerSpecAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "capacity", "allowed_material_kind")
    search_fields = ("name", "code")
    list_filter = ("allowed_material_kind",)


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = ("name", "spec", "state", "current_station", "created_at")
    list_filter = ("state", "spec", "current_station")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(ContainerSlot)
class ContainerSlotAdmin(admin.ModelAdmin):
    list_display = ("container", "index", "occupied")
    list_filter = ("occupied", "container")
    search_fields = ("container__name",)


@admin.register(TestTube15)
class TestTube15Admin(admin.ModelAdmin):
    list_display = ("name", "task", "state", "current_container", "updated_at")
    list_filter = ("state",)
    search_fields = ("name", "task__name")


@admin.register(LaiyuPowder)
class LaiyuPowderAdmin(admin.ModelAdmin):
    list_display = ("name", "material_name", "mass_mg", "state", "current_container")
    list_filter = ("state", "material_name")
    search_fields = ("name", "material_name")


@admin.register(JingtaiPowder)
class JingtaiPowderAdmin(admin.ModelAdmin):
    list_display = ("name", "material_name", "mass_mg", "state", "current_container")
    list_filter = ("state", "material_name")
    search_fields = ("name", "material_name")


@admin.register(ReagentBottle150)
class ReagentBottle150Admin(admin.ModelAdmin):
    list_display = ("name", "reagent_name", "volume_ml", "state", "current_container")
    list_filter = ("state", "reagent_name")
    search_fields = ("name", "reagent_name")
