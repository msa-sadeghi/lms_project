from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Course, Section, Lesson, Enrollment, LessonProgress, Review
from django.utils.html import format_html

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']



class SectionInline(admin.TabularInline):
    model = Section
    extra = 1
    show_change_link = True # لینکی برای رفتن به صفحه اختصاصی مدیریت بخش

class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ['student', 'rating', 'created_at']
    can_delete = False
    max_num = 5


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    @admin.display(description="Thumbnail")
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                '<img src="{}" width="60" height="40" style="object-fit:cover;border-radius:4px;" />',
                obj.thumbnail.url
            )
        return "—"
    
    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "draft": "gray",
            "review": "orange",
            "published": "green",
            "archived": "red"
        }

        color = colors.get(obj.status, "black")

        return format_html(
            '<span style="color:white;background:{};padding:4px 8px;border-radius:6px;font-size:12px;">{}</span>',
            color,
            obj.status.upper()
        )

    @admin.display(description="Students")
    def student_count(self, obj):
        return obj.enrollments.count()

    @admin.display(description="Sections")
    def section_count(self, obj):
        return obj.sections.count()

    @admin.display(description="Lessons")
    def lesson_count(self, obj):
        return Lesson.objects.filter(section__course=obj).count()

    @admin.display(description="Rating")
    def rating_stars(self, obj):
        rating = obj.average_rating
        stars = "★" * int(round(rating))
        empty = "☆" * (5 - int(round(rating)))

        return format_html(
            '<span style="color:gold;font-size:14px;">{}{}</span>',
            stars,
            empty
        )
    def enrollment_students(self, obj):
        return ", ".join([e.student.username for e in obj.enrollments.all()])
    list_display = [
        'thumbnail_preview',
        'title',
        'instructor',
        'category',
        'price',
        'status_badge',
        'student_count',
        'section_count',
        'lesson_count',
        'created_at',
        'enrollment_students',
        'rating_stars',
        # 'is_approved',
    ]
    list_filter = ['status', 'difficulty', 'is_featured', 'category', 'created_at']
    search_fields = ['title', 'description', 'instructor__email']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'enrolled_count', 'rating_display']
    inlines = [SectionInline, ReviewInline]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('title', 'slug', 'instructor', 'category', 'status')
        }),
        ('توضیحات', {
            'fields': ('description', 'detailed_description')
        }),
        ('رسانه', {
            'fields': ('thumbnail', 'preview_video')
        }),
        ('قیمت‌گذاری', {
            'fields': ('price', 'discount_price', 'is_free')
        }),
        ('اطلاعات دوره', {
            'fields': ('difficulty', 'duration_hours', 'language', 'max_students')
        }),
        ('محتوای آموزشی', {
            'fields': ('requirements', 'learning_outcomes'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('تنظیمات', {
            'fields': ('is_featured', 'published_at')
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_at', 'updated_at', 'enrolled_count', 'rating_display'),
            'classes': ('collapse',)
        }),
    )


    def price_display(self, obj):
        if obj.is_free:
            return format_html('<span style="color: green; font-weight: bold;">رایگان</span>')
        if obj.discount_price:
            return format_html(
                '<span style="text-decoration: line-through;">{}</span> <span style="color: red; font-weight: bold;">{}</span>',
                f'{obj.price:,}',
                f'{obj.discount_price:,}'
            )
        return f'{obj.price:,} تومان'
    price_display.short_description = 'قیمت'

    def enrolled_count(self, obj):
        return obj.enrolled_students_count
    enrolled_count.short_description = 'تعداد دانشجو'

    def rating_display(self, obj):
        avg = obj.average_rating
        total = obj.total_reviews
        if avg > 0:
            stars = '⭐' * int(avg)
            return format_html('{} ({} نظر)', f'{stars} {avg}', total)
        return 'بدون نظر'
    rating_display.short_description = 'امتیاز'



class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 1 # تعداد فرم‌های خالی برای اضافه کردن درس جدید
    prepopulated_fields = {'slug': ('title',)}
    classes = ('collapse',) # به صورت پیش‌فرض جمع شده باشد تا صفحه شلوغ نشود

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'lesson_count', 'is_published']
    list_filter = ['is_published', 'course']
    search_fields = ['title', 'course__title']
    inlines = [LessonInline]

    def lesson_count(self, obj):
        return obj.lessons.count()
    lesson_count.short_description = 'تعداد درس'


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'section',
        'lesson_type',
        'order',
        'duration_display',
        'is_preview',
        'is_published'
    ]
    list_filter = ['lesson_type', 'is_preview', 'is_published', 'section__course']
    search_fields = ['title', 'section__title', 'section__course__title']
    prepopulated_fields = {'slug': ('title',)}

    def duration_display(self, obj):
        if obj.video_duration > 0:
            minutes = obj.video_duration // 60
            seconds = obj.video_duration % 60
            return f'{minutes}:{seconds:02d}'
        return '-'
    duration_display.short_description = 'مدت زمان'


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student_name',
        'course',
        'status',
        'progress_bar',
        'progress_display',
        'payment_display',
        'enrolled_at'
    ]
    list_filter = ['status', 'enrolled_at', 'course']
    search_fields = ['student__email', 'student__first_name', 'student__last_name', 'course__title']
    readonly_fields = ['enrolled_at', 'completed_at', 'progress_percentage']
    date_hierarchy = 'enrolled_at'

    @admin.display(description="Progress")
    def progress_bar(self, obj):

        percent = obj.progress_percentage

        return format_html(
            '''
            <div style="width:100px;background:#eee;border-radius:5px;">
                <div style="width:{}%;background:#28a745;height:10px;border-radius:5px;"></div>
            </div>
            <small>{}%</small>
            ''',
            percent,
            percent
        )


    def student_name(self, obj):
        if obj.enrollment:
            return obj.enrollment.student.get_full_name()
        return "-"
    student_name.short_description = 'دانشجو'

    def progress_display(self, obj):
        percentage = float(obj.progress_percentage)
        color = 'green' if percentage == 100 else 'orange' if percentage >= 50 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            percentage
        )
    progress_display.short_description = 'پیشرفت'

    def payment_display(self, obj):
        if obj.payment_amount > 0:
            return f'{obj.payment_amount:,} تومان'
        return 'رایگان'
    payment_display.short_description = 'مبلغ پرداختی'


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = [
        'student_name',
        'lesson',
        'is_completed',
        'watch_progress',
        'updated_at'
    ]
    list_filter = ['is_completed', 'enrollment__course']
    search_fields = [
        'enrollment__student__email',
        'lesson__title',
        'enrollment__course__title'
    ]
    readonly_fields = ['started_at', 'updated_at', 'completed_at']

    def student_name(self, obj):
        if obj.enrollment:
            return obj.enrollment.student.get_full_name()
        return "-"
    student_name.short_description = 'دانشجو'

    def watch_progress(self, obj):
        if obj.lesson.video_duration > 0:
            percentage = (obj.watch_time_seconds / obj.lesson.video_duration) * 100
            return f'{percentage:.1f}%'
        return '-'
    watch_progress.short_description = 'درصد تماشا'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'course',
        'student_name',
        'rating_display',
        'is_approved',
        'is_featured',
        'created_at'
    ]
    list_filter = ['rating', 'is_approved', 'is_featured', 'created_at']
    search_fields = ['course__title', 'student__email', 'title', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['approve_reviews', 'feature_reviews']

    def student_name(self, obj):
        return obj.student.get_full_name()
    student_name.short_description = 'دانشجو'

    def rating_display(self, obj):
        stars = '⭐' * obj.rating
        return format_html('<span style="font-size: 16px;">{}</span>', stars)
    rating_display.short_description = 'امتیاز'

    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
