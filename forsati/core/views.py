
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import Opportunity, Organization, Application
from .forms import OrganizationRegisterForm, OpportunityForm
from . import ai_service


def home(request):
    """الصفحة الرئيسية: الأقسام والإحصائيات والشركاء."""
    active = Opportunity.objects.filter(is_active=True)
    return render(request, "core/home.html", {
        "latest": active.order_by("-pk")[:6],
        "count": active.count(),
        "orgs": Organization.objects.count(),
        "applicants": Application.objects.values("student").distinct().count(),
        "universities": Organization.objects.filter(org_type="university"),
        "banks": Organization.objects.filter(org_type="bank"),
        "companies": Organization.objects.filter(org_type="company"),
        "govs": Organization.objects.filter(org_type="gov"),
        "fields": active.values_list("field", flat=True).distinct(),
        "cities": active.values_list("city", flat=True).distinct(),
    })


def about(request):
    return render(request, "core/about.html")


def opportunity_list(request):
    """صفحة الفرص مع بحث/فلترة عادية"""
    qs = Opportunity.objects.filter(is_active=True).select_related("organization")
    q = request.GET.get("q", "")
    city = request.GET.get("city", "")
    field = request.GET.get("field", "")
    if q:
        qs = qs.filter(title__icontains=q) | qs.filter(description__icontains=q)                | qs.filter(organization__name__icontains=q)
    if city:
        qs = qs.filter(city__icontains=city)
    if field:
        qs = qs.filter(field__icontains=field)
    return render(request, "core/opportunity_list.html", {
        "opportunities": qs,
        "cities": Opportunity.objects.values_list("city", flat=True).distinct(),
        "fields": Opportunity.objects.values_list("field", flat=True).distinct(),
        "q": q, "city": city, "field": field,
    })


def opportunity_detail(request, pk):
    opp = get_object_or_404(Opportunity, pk=pk, is_active=True)
    applied = request.user.is_authenticated and         Application.objects.filter(student=request.user, opportunity=opp).exists()
    return render(request, "core/opportunity_detail.html",
                  {"opp": opp, "applied": applied})


@login_required
def apply(request, pk):
    opp = get_object_or_404(Opportunity, pk=pk, is_active=True)
    if request.method == "POST":
        Application.objects.get_or_create(
            student=request.user, opportunity=opp,
            defaults={"cover_letter": request.POST.get("cover_letter", "")},
        )
        if request.LANGUAGE_CODE == "en":
            messages.success(request, "Your application was submitted successfully!")
        else:
            messages.success(request, "تم إرسال طلب التقديم بنجاح!")
        return redirect("opportunity_detail", pk=pk)
    return render(request, "core/apply.html", {"opp": opp})


@login_required
def my_applications(request):
    apps = Application.objects.filter(student=request.user).select_related("opportunity")
    return render(request, "core/my_applications.html", {"apps": apps})


def ai_search(request):
    """البحث الذكي: يفهم طلب الطالب بالذكاء الاصطناعي (شريحة 4 و 9)"""
    results, answer, intent = [], "", None
    query = request.GET.get("q", "").strip()
    if query:
        intent = ai_service.extract_intent(query)
        results = ai_service.smart_search(intent)
        answer = ai_service.chat_answer(query, results)
    return render(request, "core/ai_search.html", {
        "query": query, "results": results, "answer": answer, "intent": intent,
    })


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})


# ============ بوابة الجهات: التسجيل ونشر الفرص ============

@login_required
def org_register(request):
    """تسجيل شركة / مؤسسة / جامعة سعودية جديدة في المنصة."""
    if Organization.objects.filter(owner=request.user).exists():
        messages.info(request, "لديك جهة مسجلة مسبقاً — يمكنك إدارتها من لوحة التحكم.")
        return redirect("org_dashboard")
    if request.method == "POST":
        form = OrganizationRegisterForm(request.POST)
        if form.is_valid():
            org = form.save(commit=False)
            org.owner = request.user
            org.save()
            messages.success(request, f"تم تسجيل «{org.name}» بنجاح! يمكنك الآن نشر فرص التدريب.")
            return redirect("org_dashboard")
    else:
        form = OrganizationRegisterForm()
    return render(request, "core/org_register.html", {"form": form})


@login_required
def post_opportunity(request):
    """نشر فرصة تدريب جديدة من جهة مسجلة."""
    orgs = Organization.objects.filter(owner=request.user)
    if not orgs:
        messages.info(request, "سجّل جهتك أولاً ثم انشر الفرص التدريبية.")
        return redirect("org_register")
    if request.method == "POST":
        form = OpportunityForm(request.POST)
        org = orgs.filter(pk=request.POST.get("organization")).first() or orgs.first()
        if form.is_valid():
            opp = form.save(commit=False)
            opp.organization = org
            opp.save()
            messages.success(request, f"تم نشر «{opp.title}» بنجاح وأصبحت ظاهرة للطلاب.")
            return redirect("org_dashboard")
    else:
        form = OpportunityForm()
    return render(request, "core/post_opportunity.html",
                  {"form": form, "orgs": orgs})


@login_required
def org_dashboard(request):
    """لوحة تحكم الجهة: فرصها وطلبات المتقدمين."""
    orgs = Organization.objects.filter(owner=request.user)
    opportunities = Opportunity.objects.filter(organization__in=orgs)
    applications = (Application.objects
                    .filter(opportunity__in=opportunities)
                    .select_related("student", "opportunity")
                    .order_by("-pk"))
    return render(request, "core/org_dashboard.html", {
        "orgs": orgs,
        "opportunities": opportunities,
        "applications": applications,
        "pending": applications.filter(status="pending").count(),
    })


@login_required
def application_status(request, pk, status):
    """قبول/رفض طلب متقدم (لصاحب الجهة فقط)."""
    app = get_object_or_404(Application, pk=pk,
                            opportunity__organization__owner=request.user)
    if status in dict(Application.STATUS):
        app.status = status
        app.save()
        label = "قبول" if status == "accepted" else "رفض"
        messages.success(request, f"تم {label} طلب {app.student.username}.")
    return redirect("org_dashboard")


# ============ مدرب المسارات المهنية (AI Career Coach) ============

def coach(request):
    """مساعد ذكي يرشد الطالب: الفرص المناسبة، المقابلات، السيرة الذاتية..."""
    if request.GET.get("clear"):
        request.session.pop("coach_history", None)
        return redirect("coach")
    history = request.session.get("coach_history", [])
    answer, opportunities, asked = "", [], ""
    if request.method == "POST":
        asked = request.POST.get("message", "").strip()
        if asked:
            intent = ai_service.extract_intent(asked)
            opportunities = ai_service.smart_search(intent)
            answer = ai_service.coach_answer(asked, history=history[-6:],
                                             opportunities=opportunities)
            history.append({"q": asked, "a": answer})
            request.session["coach_history"] = history[-12:]
            request.session.modified = True
    return render(request, "core/coach.html", {
        "history": history,
        "answer": answer,
        "opportunities": opportunities,
        "asked": asked,
    })
