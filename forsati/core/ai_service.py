
"""
طبقة الذكاء الاصطناعي لمنصة فرصتي:
1) إن وُجد مفتاح AI_API_KEY يتم استدعاء نموذج لغوي (OpenAI-compatible)
   لفهم طلب الطلب واستخراج: المجال، المدينة، الكلمات المفتاحية.
2) إن لم يوجد مفتاح يعمل fallback محلي: مطابقة TF-IDF بسيطة بين طلب الطلب
   ونصوص الفرص المتاحة.
"""
from django.conf import settings
from core.models import Opportunity
import requests, re


# ---------- 1) فهم طلب الطالب بالذكاء الاصطناعي ----------
def extract_intent(user_query: str) -> dict:
    """يفهم طلب الطالب ويستخرج (المجال، المدينة، كلمات مفتاحية)."""
    if settings.AI_API_KEY:
        return _llm_extract(user_query)
    return _local_extract(user_query)


def _llm_extract(user_query: str) -> dict:
    prompt = f"""
أنت مساعد منصة فرصتي لفرص التدريب التعاوني في منطقة القصيم.
حلل طلب الطالب التالي واستخرج JSON فقط بالمفاتيح:
field (المجال الوظيفي), city (المدينة أو null), keywords (قائمة كلمات مفتاحية).

طلب الطالب: {user_query}
"""
    try:
        r = requests.post(
            f"{settings.AI_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
            json={
                "model": settings.AI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0,
            },
            timeout=30,
        )
        data = r.json()["choices"][0]["message"]["content"]
        import json
        parsed = json.loads(data)
        return {
            "field": parsed.get("field") or "",
            "city": parsed.get("city") or "",
            "keywords": parsed.get("keywords") or [],
            "source": "llm",
        }
    except Exception:
        return _local_extract(user_query)


CITY_HINTS = ["بريدة", "عنيزة", "الرس", "المذنب", "البكيرية", "البدائع", "رياض الخبراء", "القصيم"]
FIELD_HINTS = {
    "أمن سيبراني": ["سيبراني", "امن سيبراني", "أمن معلومات", "حماية"],
    "برمجة وتطوير": ["برمجة", "مطور", "تطوير", "برمجيات", "سوفتوير", "coding", "developer"],
    "تصميم": ["تصميم", "جرافيك", "واجهات", "ui", "ux"],
    "إدارة أعمال": ["إدارة", "موارد بشرية", "محاسبة", "مالية", "تسويق"],
    "هندسة": ["هندسة", "مهندس", "هندسي"],
    "شبكات": ["شبكات", "network", "اتصالات"],
}

def _local_extract(user_query: str) -> dict:
    q = user_query.lower()
    city = next((c for c in CITY_HINTS if c in user_query), "")
    field = ""
    for f, words in FIELD_HINTS.items():
        if any(w.lower() in q for w in words):
            field = f
            break
    keywords = re.findall(r"[\wء-ي]+", user_query)
    return {"field": field, "city": city, "keywords": keywords, "source": "local"}


# ---------- 2) البحث الذكي في قاعدة البيانات ----------
def smart_search(intent: dict, limit: int = 10):
    """يبحث في الفرص حسب المجال والمدينة ثم يرتب بالتشابه النصي."""
    qs = Opportunity.objects.filter(is_active=True).select_related("organization")

    results = list(qs)
    if intent.get("field"):
        by_field = [o for o in results if intent["field"] in o.field]
        if by_field:
            results = by_field
    if intent.get("city"):
        by_city = [o for o in results if intent["city"] in o.city]
        if by_city:
            results = by_city

    scored = [(score(o, intent), o) for o in results]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [o for s, o in scored[:limit] if s > 0 or not intent.get("keywords")]


def score(opp, intent) -> float:
    text = f"{opp.title} {opp.description} {opp.field} {opp.organization.name}"
    text_l = text.lower()
    s = 0.0
    for kw in intent.get("keywords", []):
        if kw.lower() in text_l:
            s += 2.0
    if intent.get("field") and intent["field"] in opp.field:
        s += 5.0
    if intent.get("city") and intent["city"] in opp.city:
        s += 3.0
    return s


# ---------- 3) رد المحادثة (شات بوت) ----------
def chat_answer(user_query: str, opportunities) -> str:
    if settings.AI_API_KEY:
        try:
            listing = "\n".join(
                f"- {o.title} | {o.field} | {o.city} | {o.organization.name}" for o in opportunities[:10]
            )
            r = requests.post(
                f"{settings.AI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
                json={
                    "model": settings.AI_MODEL,
                    "messages": [
                        {"role": "system", "content":
                         "أنت مساعد منصة فرصتي للتدريب التعاوني في القصيم. أجب بالعربية بإيجاز "
                         "وقدّم الفرص المناسبة كنقاط."},
                        {"role": "user", "content":
                         f"سؤال الطالب: {user_query}\n\nالفرص المتاحة:\n{listing}"},
                    ],
                    "temperature": 0.3,
                },
                timeout=30,
            )
            return r.json()["choices"][0]["message"]["content"]
        except Exception:
            pass
    if not opportunities:
        return ("لم أجد فرصاً مطابقة حالياً. جرّب كلمات أخرى مثل: "
                "\"أبحث عن تدريب تعاوني في الأمن السيبراني في بريدة\".")
    items = "\n".join(f"• {o.title} — {o.organization.name} ({o.city})" for o in opportunities[:5])
    return f"وجدت لك هذه الفرص المناسبة:\n{items}"


# ============ 4) مدرب المسارات المهنية (AI Training Career Coach) ============

COACH_SYSTEM_PROMPT = (
    "أنت «مدرب المسارات المهنية» (AI Training Career Coach) داخل منصة فرصتي "
    "لفرص التدريب التعاوني في المملكة العربية السعودية. دورك مساعدة الطلبة الخريجين في:\n"
    "1) اقتراح فرص تدريب مناسبة لتخصصهم.\n"
    "2) التهيئة لمقابلات التدريب (أسئلة شائعة، نصائح، التصرفات المناسبة).\n"
    "3) مراجعة السيرة الذاتية واقتراح تحسينات عملية.\n"
    "4) كتابة خطابات التقديم.\n"
    "5) إرشادهم للمهارات المطلوبة والمسار الوظيفي المناسب.\n"
    "أجب بالعربية الفصحى المبسطة، بأسلوب مشجع ومحترم، بخطوات واضحة ومرقمة، "
    "وكن واقعياً ومحدداً. لا تختلق فرصاً غير موجودة."
)


def coach_answer(user_message: str, history=None, opportunities=None) -> str:
    """إجابة المدرب الذكي: LLM إن وُجد مفتاح، وإلا إرشاد محلي مبني على قواعد."""
    if settings.AI_API_KEY:
        try:
            listing = "\n".join(
                f"- {o.title} | {o.field} | {o.city} | {o.organization.name}"
                for o in (opportunities or [])[:8]
            )
            messages = [{"role": "system", "content": COACH_SYSTEM_PROMPT}]
            for h in (history or [])[-4:]:
                messages.append({"role": "user", "content": h["q"]})
                messages.append({"role": "assistant", "content": h["a"]})
            user_content = user_message
            if listing:
                user_content += f"\n\nالفرص المتاحة حالياً في المنصة:\n{listing}"
            messages.append({"role": "user", "content": user_content})
            r = requests.post(
                f"{settings.AI_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {settings.AI_API_KEY}"},
                json={"model": settings.AI_MODEL, "messages": messages,
                      "temperature": 0.5},
                timeout=30,
            )
            return r.json()["choices"][0]["message"]["content"]
        except Exception:
            pass
    return _local_coach(user_message, opportunities or [])


def _local_coach(msg: str, opportunities) -> str:
    """إرشاد محلي بدون إنترنت: يصنف سؤال الطالب ويقدم إجابة جاهزة."""
    q = msg.casefold()
    has = lambda *words: any(w in q for w in words)

    # 1) فرص مناسبة للتخصص
    if has("فرص", "فرصة", "تدريب", "تعاوني", "تخصصي", "مناسب") and \
       not has("مقابلة", "سيرة", "خطاب"):
        if opportunities:
            items = "\n".join(
                f"• {o.title} — {o.organization.name} ({o.city}) | المجال: {o.field}"
                for o in opportunities[:5])
            return (
                "بناءً على تخصصك، هذه أقرب الفرص المتاحة لك في المنصة حالياً:\n"
                f"{items}\n\n"
                "نصيحتي: قارن بينها حسب (المدينة – المجال – المتطلبات)، ثم قدّم على فرصتين "
                "أو ثلاث لتزيد فرص قبولك. اضغط على أي فرصة لعرض تفاصيلها والتقديم عليها."
            )
        return (
            "لم أجد فرصة مطابقة تماماً الآن، لكن إليك طريقتي المقترحة للبحث:\n"
            "1) حدّد مجالك بدقة (مثال: برمجة وتطوير، أمن سيبراني، تحليل بيانات).\n"
            "2) جرّب صفحة «الفرص» مع فلتر المدينة والمجال.\n"
            "3) استخدم البحث الذكي بجملة مثل: «أبحث عن تدريب تعاوني في بريدة».\n"
            "4) طور مهارة واحدة مطلوبة في مجالك كل شهر — هذا أسرع طريق لفرصة أقوى."
        )

    # 2) التهيئة للمقابلة التدريبية
    if has("مقابلة", "انترفيو", "مقابله", "interview"):
        return (
            "التهيئة للمقابلة التدريبية — خطوات عملية:\n"
            "1) ادرس الجهة جيداً: نشاطها، منتجاتها، وآخر أخبارها.\n"
            "2) جهّز إجابة قصيرة عن نفسك (دقيقة واحدة): من أنت، تخصصك، لماذا هذا التدريب.\n"
            "3) راجع أساسيات تخصصك — أسئلة المقابلات غالباً نظرية وتطبيقية بسيطة.\n"
            "4) جهّز 3 أسئلة تسألها أنت عنهم (طبيعة العمل، من سيكون مشرفك، ماذا سنتعلم).\n"
            "5) اليوم السابق: نوم كافٍ، ملابس رسمية نظيفة، وصل قبل الموعد بـ 15 دقيقة.\n"
            "6) أثناء المقابلة: اهتمام بصري، صوت هادئ، ولا تخف من قول «سأتعلمها بسرعة».\n"
            "أسئلة شائعة: عرّف بنفسك؟ ما نقاط قوتك وضعفك؟ لماذا اخترتنا؟ هل تعمل ضمن فريق؟"
        )

    # 3) السيرة الذاتية
    if has("سيرة", "cv", "resume", "ذاتية"):
        return (
            "تحسين السيرة الذاتية — أهم التعديلات:\n"
            "1) صفحة واحدة كافية لطالب، وأهم المعلومات في أعلى الثلث الأول.\n"
            "2) ابدأ بملخص مهني من سطرين: تخصصك + هدفك من التدريب + أبرز مهارة.\n"
            "3) المشاريع أقوى من المواد الدراسية: اذكر 2-3 مشاريع (المشكلة – ماذا فعلت – النتيجة).\n"
            "4) المهارات: اكتبها بمصطلحات سوق العمل (مثال: Python, SQL, Power BI, إدارة مشاريع).\n"
            "5) أرقام تثبت إنجازك: «حللت بيانات 5000 سجل» أقوى من «مهارات تحليل بيانات».\n"
            "6) راجع الإملاء، وثّق الملف PDF باسم احترافي: الاسم_CV.pdf.\n"
            "7) تجنب الصورة الشخصية غير الرسمية والألوان الكثيرة.\n"
            "أرسل لي نص سيرتك هنا وسأساعدك في تحسين كل قسم منها."
        )

    # 4) خطاب التقديم
    if has("خطاب", "تغطية", "cover letter", "تقديم لجهة"):
        return (
            "كتابة خطاب تقديم مقنع (4 فقرات قصيرة):\n"
            "1) المقدمة: من أنت (الاسم – الجامعة – التخصص – السنة) + الفرصة التي تتقدم لها.\n"
            "2) لماذا أنت مناسب: مهارة أو مشروع واحد مرتبط مباشرة بمتطلبات الفرصة.\n"
            "3) لماذا هذه الجهة بالذات: سبب حقيقي يدل أنك تعرفها (مشروعها، منتجها، رسالتها).\n"
            "4) الختام: حماس للانضمام + جاهزية للمقابلة + الشكر.\n"
            "قاعدة ذهبية: خطاب واحد لكل فرصة — لا ترسل نفس الخطاب لكل الجهات.\n"
            "مثال جملة افتتاحية: «أنا فلانة، طالبة علوم حاسب في جامعة القصيم، أتقدم لفرصة "
            "التدريب التعاوني في مجال تحليل البيانات لأن مشروعي الأخير في Power BI علّمني...»"
        )

    # 5) المهارات المطلوبة / المسار الوظيفي
    if has("مهارة", "مهارات", "مسار", "وظيف", "وظيفة", "مستقبل", "career", "سيبراني"):
        return (
            "بناء مسارك المهني — خارطة عملية:\n"
            "1) اختر هدفاً واحداً واضحاً (مثال: محلل بيانات / مهندس أمن سيبراني / مطور ويب).\n"
            "2) المسار التقليدي: تدريب تعاوني ← مشاريع تخرج ← وظيفة junior ← تخصص أعمق.\n"
            "3) مهارات أساسية لمعظم المجالات التقنية: Excel متقدم، أساسيات SQL، عرض وتقديم، إنجليزية مهنية.\n"
            "4) شهادات معترف بها تفتح الأبواب: (AWS Cloud Practitioner, Google Data Analytics, CompTIA Security+)\n"
            "5) التزم بخطة 90 يوماً: مهارة واحدة + مشروع واحد صغير + حساب LinkedIn محدّث.\n"
            "قول لي تخصصك بالضبط وسأقترح لك المسار والمهارات الأدق لك."
        )

    # 6) رد افتراضي
    return (
        "سؤال جميل! أنا مدربك المهني وأساعدك في خمسة محاور — اختر ما يناسبك أو اكتب سؤالك:\n"
        "• ما الفرص التدريبية المناسبة لتخصصي؟\n"
        "• كيف أجهز نفسي للمقابلة التدريبية؟\n"
        "• راجع لي سيرتي الذاتية واقترح تحسينات.\n"
        "• كيف أكتب خطاب تقديم لجهة تدريب؟\n"
        "• ما المهارات والمسار الوظيفي المناسب لي؟"
    )
