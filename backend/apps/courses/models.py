from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
import uuid


class Category(models.Model):
    """دسته‌بندی دوره‌ها (مثل Programming, Design, Business)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, verbose_name='نام دسته‌بندی')
    slug = models.SlugField(max_length=120, unique=True, blank=True, allow_unicode=True)
    description = models.TextField(blank=True, verbose_name='توضیحات')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name='دسته‌بندی والد'
    )
    icon = models.CharField(max_length=50, blank=True, help_text='نام آیکون (مثل: fa-code)')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'دسته‌بندی'
        verbose_name_plural = 'دسته‌بندی‌ها'
        ordering = ['name']

    def __str__(self):
        full_path = [self.name]
        parent = self.parent
        while parent is not None:
            full_path.append(parent.name)
            parent = parent.parent
        return " → ".join(full_path[::-1])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class Course(models.Model):
    """مدل اصلی دوره"""
    
    DIFFICULTY_CHOICES = [
        ('BEGINNER', 'مبتدی'),
        ('INTERMEDIATE', 'متوسط'),
        ('ADVANCED', 'پیشرفته'),
        ('EXPERT', 'حرفه‌ای'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'پیش‌نویس'),
        ('PUBLISHED', 'منتشر شده'),
        ('ARCHIVED', 'بایگانی شده'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name='عنوان دوره')
    slug = models.SlugField(max_length=300, unique=True, blank=True,allow_unicode=True)
    description = models.TextField(verbose_name='توضیحات کوتاه')
    detailed_description = models.TextField(blank=True, verbose_name='توضیحات کامل')
    
    # روابط
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='taught_courses',
        limit_choices_to={'role': 'INSTRUCTOR'},
        verbose_name='مدرس'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='courses',
        verbose_name='دسته‌بندی'
    )
    
    # تصاویر و فایل‌ها
    thumbnail = models.ImageField(
        upload_to='courses/thumbnails/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='تصویر شاخص'
    )
    preview_video = models.FileField(upload_to='course_previews/', null=True, blank=True)
    
    # قیمت‌گذاری
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name='قیمت (تومان)'
    )
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='قیمت با تخفیف'
    )
    is_free = models.BooleanField(default=False, verbose_name='دوره رایگان')
    
    # اطلاعات دوره
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='BEGINNER',
        verbose_name='سطح دشواری'
    )
    duration_hours = models.PositiveIntegerField(
        default=0,
        help_text='مدت زمان کل دوره به ساعت',
        verbose_name='مدت زمان (ساعت)'
    )
    language = models.CharField(max_length=50, default='فارسی', verbose_name='زبان')
    
    # وضعیت و تنظیمات
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        verbose_name='وضعیت'
    )
    is_featured = models.BooleanField(default=False, verbose_name='دوره ویژه')
    max_students = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='حداکثر دانشجو'
    )
    
    # Requirements & Outcomes
    requirements = models.JSONField(
        default=list,
        blank=True,
        help_text='پیش‌نیازهای دوره (لیست)',
        verbose_name='پیش‌نیازها'
    )
    learning_outcomes = models.JSONField(
        default=list,
        blank=True,
        help_text='نتایج یادگیری (لیست)',
        verbose_name='نتایج یادگیری'
    )
    
    # SEO
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'دوره'
        verbose_name_plural = 'دوره‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['instructor', 'status']),
            models.Index(fields=['category', 'status']),
        ]

    def __str__(self):
        return f"{self.title} – {self.instructor.username}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    @property
    def enrolled_students_count(self):
        """تعداد دانشجویان ثبت‌نام شده"""
        return self.enrollments.filter(status='ACTIVE').count()

    @property
    def average_rating(self):
        """میانگین امتیاز دوره"""
        ratings = self.reviews.aggregate(models.Avg('rating'))
        return round(ratings['rating__avg'] or 0, 1)

    @property
    def total_reviews(self):
        """تعداد کل نظرات"""
        return self.reviews.count()


class Section(models.Model):
    """بخش‌های دوره (هر دوره چند Section دارد)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name='دوره'
    )
    title = models.CharField(max_length=255, verbose_name='عنوان بخش')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب')
    is_published = models.BooleanField(default=True, verbose_name='منتشر شده')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'بخش'
        verbose_name_plural = 'بخش‌ها'
        ordering = ['course', 'order']
        unique_together = [['course', 'order']]

    def __str__(self):
        return f"{self.course.title} / فصل {self.order}: {self.title}"


class Lesson(models.Model):
    """درس‌های هر بخش"""
    
    LESSON_TYPE_CHOICES = [
        ('VIDEO', 'ویدیو'),
        ('TEXT', 'متن'),
        ('QUIZ', 'آزمون'),
        ('ASSIGNMENT', 'تکلیف'),
        ('LIVE', 'جلسه زنده'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='بخش'
    )
    title = models.CharField(max_length=255, verbose_name='عنوان درس')
    slug = models.SlugField(max_length=300, blank=True, allow_unicode=True)
    lesson_type = models.CharField(
        max_length=20,
        choices=LESSON_TYPE_CHOICES,
        default='VIDEO',
        verbose_name='نوع درس'
    )
    
    # محتوا
    content = models.TextField(blank=True, verbose_name='محتوای متنی')
    video_url = models.URLField(blank=True, verbose_name='لینک ویدیو')
    video_duration = models.PositiveIntegerField(
        default=0,
        help_text='مدت زمان ویدیو به ثانیه',
        verbose_name='مدت ویدیو (ثانیه)'
    )
    
    # فایل‌های ضمیمه
    attachments = models.JSONField(
        default=list,
        blank=True,
        help_text='لیست فایل‌های ضمیمه',
        verbose_name='فایل‌های ضمیمه'
    )
    
    # تنظیمات
    order = models.PositiveIntegerField(default=0, verbose_name='ترتیب')
    is_preview = models.BooleanField(
        default=False,
        help_text='آیا این درس برای پیش‌نمایش رایگان است؟',
        verbose_name='پیش‌نمایش رایگان'
    )
    is_published = models.BooleanField(default=True, verbose_name='منتشر شده')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'درس'
        verbose_name_plural = 'درس‌ها'
        ordering = ['section', 'order']
        unique_together = [['section', 'order']]

    def __str__(self):
        return f"{self.section.course.title} / {self.section.title} / درس {self.order}: {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)


class Enrollment(models.Model):
    """ثبت‌نام دانشجو در دوره"""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'فعال'),
        ('COMPLETED', 'تکمیل شده'),
        ('EXPIRED', 'منقضی شده'),
        ('CANCELLED', 'لغو شده'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'role': 'STUDENT'},
        verbose_name='دانشجو'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='دوره'
    )
    
    # وضعیت و پیشرفت
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        verbose_name='وضعیت'
    )
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='درصد پیشرفت'
    )
    
    # تاریخ‌ها
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت‌نام')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تکمیل')
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='تاریخ انقضای دسترسی (برای دوره‌های محدود)',
        verbose_name='تاریخ انقضا'
    )
    last_accessed = models.DateTimeField(null=True, blank=True, verbose_name='آخرین دسترسی')
    
    # اطلاعات پرداخت
    payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name='مبلغ پرداختی'
    )
    payment_method = models.CharField(max_length=50, blank=True, verbose_name='روش پرداخت')
    transaction_id = models.CharField(max_length=100, blank=True, verbose_name='شناسه تراکنش')

    class Meta:
        verbose_name = 'ثبت‌نام'
        verbose_name_plural = 'ثبت‌نام‌ها'
        ordering = ['-enrolled_at']
        unique_together = [['student', 'course']]
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['course', 'status']),
        ]

    def __str__(self):
        return f"{self.student.username} → {self.course.title} ({self.status})"



class LessonProgress(models.Model):
    """پیشرفت دانشجو در هر درس"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        verbose_name='ثبت‌نام'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='student_progress',
        verbose_name='درس'
    )
    
    # وضعیت
    is_completed = models.BooleanField(default=False, verbose_name='تکمیل شده')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ تکمیل')
    
    # برای ویدیوها
    watch_time_seconds = models.PositiveIntegerField(
        default=0,
        help_text='زمان تماشای ویدیو به ثانیه',
        verbose_name='زمان تماشا (ثانیه)'
    )
    last_position_seconds = models.PositiveIntegerField(
        default=0,
        help_text='آخرین موقعیت پخش ویدیو',
        verbose_name='موقعیت آخر (ثانیه)'
    )
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='شروع')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        verbose_name = 'پیشرفت درس'
        verbose_name_plural = 'پیشرفت درس‌ها'
        unique_together = [['enrollment', 'lesson']]
        indexes = [
            models.Index(fields=['enrollment', 'is_completed']),
        ]

    def __str__(self):
        status = "تمام شده" if self.is_completed else f"{self.progress_percentage}%"
        return f"{self.enrollment.student.username} – {self.lesson.title} ({status})"


class Review(models.Model):
    """نظرات و امتیازات دانشجویان"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='دوره'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_reviews',
        verbose_name='دانشجو'
    )
    
    # امتیاز و نظر
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='امتیاز'
    )
    title = models.CharField(max_length=255, blank=True, verbose_name='عنوان نظر')
    comment = models.TextField(verbose_name='نظر')
    
    # وضعیت
    is_approved = models.BooleanField(default=False, verbose_name='تأیید شده')
    is_featured = models.BooleanField(default=False, verbose_name='نظر ویژه')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'نظر'
        verbose_name_plural = 'نظرات'
        ordering = ['-created_at']
        unique_together = [['course', 'student']]
        indexes = [
            models.Index(fields=['course', 'is_approved']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.title} ({self.rating}⭐)"
