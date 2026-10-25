
from django.db import models
from django.contrib.auth.models import User

class Organization(models.Model):
    """الجهات والشركات التي توفر التدريب (الشريحة 7)"""
    TYPE_CHOICES = [
        ("university", "جامعة / مؤسسة تعليمية"),
        ("company", "شركة"),
        ("bank", "بنك / مصرف"),
        ("gov", "جهة حكومية"),
        ("other", "أخرى"),
    ]
    name = models.CharField("الاسم", max_length=200)
    org_type = models.CharField("النوع", max_length=20, choices=TYPE_CHOICES)
    city = models.CharField("المدينة", max_length=100, default="القصيم")
    website = models.URLField("الموقع", blank=True)
    contact_email = models.EmailField("البريد الإلكتروني للتواصل", blank=True)
    description = models.TextField("الوصف", blank=True)
    # المستخدم المسؤول عن الجهة (يسجل ويضيف الفرص ويراجع المتقدمين)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name="owned_organizations", verbose_name="مسؤول الجهة")
    logo = models.CharField("رمز الشعار", max_length=20, blank=True,
                            help_text="اسم ملف SVG في static/images/partners بدون الامتداد")
    created_at = models.DateTimeField("تاريخ التسجيل", auto_now_add=True, null=True)

    def __str__(self):
        return self.name

class Opportunity(models.Model):
    """فرص التدريب التعاوني"""
    title = models.CharField("عنوان الفرصة", max_length=200)
    description = models.TextField("الوصف")
    field = models.CharField("المجال", max_length=100)          # هندسة، أمن سيبراني...
    city = models.CharField("المدينة", max_length=100, default="بريدة")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE,
                                     related_name="opportunities", verbose_name="الجهة")
    requirements = models.TextField("المتطلبات", blank=True)
    is_active = models.BooleanField("متاحة", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "فرصة تدريب"
        verbose_name_plural = "فرص التدريب"

    def __str__(self):
        return self.title

class Application(models.Model):
    """طلبات التقديم للطلاب"""
    STATUS = [
        ("pending", "قيد المراجعة"),
        ("accepted", "مقبول"),
        ("rejected", "مرفوض"),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="الطالب")
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE,
                                    related_name="applications", verbose_name="الفرصة")
    cover_letter = models.TextField("رسالة التقديم", blank=True)
    status = models.CharField("الحالة", max_length=20, choices=STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "opportunity")

    def __str__(self):
        return f"{self.student.username} -> {self.opportunity.title}"
