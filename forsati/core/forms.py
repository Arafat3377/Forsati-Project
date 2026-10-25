
"""نماذج الواجهة: تسجيل الجهات ونشر فرص التدريب."""
from django import forms
from .models import Organization, Opportunity

INPUT_CLASS = {"class": "form-input"}


class OrganizationRegisterForm(forms.ModelForm):
    """تسجيل شركة / مؤسسة / جامعة سعودية جديدة في المنصة."""

    class Meta:
        model = Organization
        fields = ["name", "org_type", "city", "website", "contact_email", "description"]
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "مثال: شركة التقنية المتقدمة للاتصالات"}),
            "city": forms.TextInput(attrs={"placeholder": "مثال: بريدة، الرياض، جدة"}),
            "website": forms.URLInput(attrs={"placeholder": "https://example.sa (اختياري)"}),
            "contact_email": forms.EmailInput(attrs={"placeholder": "hr@example.sa (اختياري)"}),
            "description": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "نبذة قصيرة عن الجهة ومجال عملها..."}),
        }

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if Organization.objects.filter(name=name).exists():
            raise forms.ValidationError("هذه الجهة مسجلة مسبقاً في المنصة.")
        return name


class OpportunityForm(forms.ModelForm):
    """نشر فرصة تدريب جديدة من جهة مسجلة."""

    class Meta:
        model = Opportunity
        fields = ["title", "field", "city", "description", "requirements"]
        widgets = {
            "title": forms.TextInput(attrs={
                "placeholder": "مثال: تدريب تعاوني - تحليل بيانات"}),
            "field": forms.TextInput(attrs={
                "placeholder": "مثال: برمجة وتطوير، أمن سيبراني، إدارة أعمال"}),
            "city": forms.TextInput(attrs={"placeholder": "مثال: بريدة"}),
            "description": forms.Textarea(attrs={
                "rows": 4,
                "placeholder": "وصف الفرصة والمهام التي سينفذها المتدرب..."}),
            "requirements": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "المتطلبات والمهارات المطلوبة..."}),
        }
