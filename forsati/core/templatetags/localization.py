from django import template

register = template.Library()

TRANSLATIONS = {
    "تدريب تعاوني - أمن سيبراني": "Cooperative Training - Cybersecurity",
    "تدريب تعاوني - تطوير برمجيات": "Cooperative Training - Software Development",
    "تدريب تعاوني - تحليل بيانات": "Cooperative Training - Data Analysis",
    "تدريب تعاوني - إدارة مشاريع": "Cooperative Training - Project Management",
    "تدريب تعاوني - هندسة شبكات": "Cooperative Training - Network Engineering",
    "تدريب تعاوني - تصميم واجهات UI/UX": "Cooperative Training - UI/UX Design",
    "تدريب تعاوني - دعم فني للأجهزة": "Cooperative Training - Hardware Technical Support",
    "تدريب تعاوني - دعم فني للشبكات": "Cooperative Training - Network Technical Support",
    "تدريب تعاوني - مركز خدمة تقنية المعلومات": "Cooperative Training - IT Service Desk",
    "تدريب تعاوني - دعم المستخدمين": "Cooperative Training - User Support",
    "تدريب تعاوني - إدارة مكتب المساعدة": "Cooperative Training - Help Desk Administration",
    "تدريب تعاوني - تحليل النظم": "Cooperative Training - Systems Analysis",
    "تدريب تعاوني - تحليل متطلبات الأعمال": "Cooperative Training - Business Requirements Analysis",
    "تدريب تعاوني - توثيق الأنظمة": "Cooperative Training - Systems Documentation",
    "تدريب تعاوني - تحليل قواعد البيانات": "Cooperative Training - Database Analysis",
    "تدريب تعاوني - تحليل إجراءات العمل": "Cooperative Training - Business Process Analysis",
    "تدريب تعاوني - تطوير تطبيقات ويب": "Cooperative Training - Web Application Development",
    "تدريب تعاوني - اختبار وضمان الجودة": "Cooperative Training - Quality Assurance and Testing",
    "تدريب تعاوني - تحليل البيانات": "Cooperative Training - Data Analysis",
    "تدريب تعاوني - أمن المعلومات": "Cooperative Training - Information Security",
    "تدريب تعاوني - إدارة مشاريع تقنية": "Cooperative Training - IT Project Management",
    "أمن سيبراني": "Cybersecurity",
    "برمجة وتطوير": "Programming and Development",
    "إدارة أعمال": "Business Administration",
    "شبكات": "Networking",
    "تصميم": "Design",
    "دعم فني": "Technical Support",
    "تحليل نظم": "Systems Analysis",
    "تحليل بيانات": "Data Analysis",
    "إدارة مشاريع": "Project Management",
    "بريدة": "Buraidah",
    "عنيزة": "Unaizah",
    "الرس": "Ar Rass",
    "المذنب": "Al Mithnab",
    "البكيرية": "Al Bukayriyah",
    "رياض الخبراء": "Riyadh Al Khabra",
    "القصيم": "Al-Qassim",
    "أبها": "Abha",
    "الرياض": "Riyadh",
    "جامعة القصيم": "Qassim University",
    "جامعة الملك خالد - منصة التدريب والشراكات": "King Khalid University - Training and Partnerships Platform",
    "صندوق التنمية الصناعية SIDF": "Saudi Industrial Development Fund (SIDF)",
    "منصة التدريب والتطوير": "Training and Development Platform",
    "معرفة أساسية بالشبكات والحماية": "Basic knowledge of networking and security",
    "Python أو JavaScript": "Python or JavaScript",
    "Excel وأساسيات الإحصاء": "Excel and basic statistics",
    "مهارات تواصل وتنظيم": "Communication and organizational skills",
    "CCNA ميزة إضافية": "CCNA certification is an advantage",
    "Figma أو Adobe XD": "Figma or Adobe XD",
    "أساسيات أنظمة Windows وصيانة الحاسب": "Windows fundamentals and computer maintenance",
    "أساسيات الشبكات واستكشاف الأعطال": "Networking fundamentals and troubleshooting",
    "مهارات التواصل وإدارة بلاغات الدعم": "Communication skills and support ticket management",
    "تثبيت البرامج وتهيئة أجهزة المستخدمين": "Software installation and user device setup",
    "إدارة التذاكر وتوثيق الحلول التقنية": "Ticket management and technical solution documentation",
    "جمع المتطلبات وإعداد مخططات حالات الاستخدام": "Requirements gathering and use case diagram preparation",
    "تحليل العمليات وكتابة وثائق المتطلبات": "Process analysis and requirements documentation",
    "كتابة مواصفات الأنظمة وإعداد أدلة المستخدم": "Writing system specifications and user guides",
    "SQL ومبادئ نمذجة قواعد البيانات": "SQL and database modeling fundamentals",
    "نمذجة إجراءات العمل باستخدام BPMN": "Business process modeling using BPMN",
    "أساسيات HTML وCSS وJavaScript": "HTML, CSS, and JavaScript fundamentals",
    "كتابة حالات الاختبار والانتباه للتفاصيل": "Writing test cases and attention to detail",
    "Excel وPower BI وأساسيات SQL": "Excel, Power BI, and SQL fundamentals",
    "مبادئ أمن المعلومات وإدارة المخاطر": "Information security and risk management fundamentals",
    "إعداد الجداول الزمنية ومتابعة المهام": "Creating schedules and tracking tasks",
}


@register.filter
def localize(value, language):
    """Translate known Arabic opportunity data when the site is viewed in English."""
    if language != "en" or not isinstance(value, str):
        return value

    translated = TRANSLATIONS.get(value)
    if translated is not None:
        return translated

    if value.startswith("فرصة ") and value.endswith(" لطلبة الجامعات في منطقة القصيم."):
        title = value[len("فرصة "):-len(" لطلبة الجامعات في منطقة القصيم.")]
        return (
            f"Cooperative training opportunity: "
            f"{TRANSLATIONS.get(title, title)} for university students in Al-Qassim."
        )

    return value
