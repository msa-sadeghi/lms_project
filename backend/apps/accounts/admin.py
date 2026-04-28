from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # فیلدهایی که در لیست اصلی نمایش داده می‌شوند
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff', 'created_at')
    
    # فیلترها در ستون سمت راست
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    
    # فیلدهایی که قابل جستجو هستند
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    
    # ترتیب نمایش
    ordering = ('-created_at',)
    
    # پیکربندی فرم ویرایش کاربر (اضافه کردن فیلدهای جدید به گروه‌بندی‌های ادمین)
    fieldsets = UserAdmin.fieldsets + (
        ('اطلاعات تکمیلی پروفایل', {
            'fields': ('role', 'phone', 'bio', 'avatar'),
        }),
    )
    
    # فیلدهایی که هنگام ساخت کاربر جدید نمایش داده می‌شوند
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('اطلاعات تکمیلی پروفایل', {
            'fields': ('role', 'phone', 'email', 'first_name', 'last_name'),
        }),
    )

    # برای اینکه نقش‌ها در لیست ادمین با رنگ یا فرمت خاصی متمایز شوند (اختیاری اما حرفه‌ای)
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # اینجا می‌توان محدودیت‌هایی برای تغییر نقش توسط افراد غیر ادمین گذاشت
        return form
