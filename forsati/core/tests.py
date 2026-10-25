from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from core.models import Opportunity, Organization


class AuthAndI18nTests(TestCase):
    def test_home_hides_opportunity_summary_and_shows_footer(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "opportunities available")
        self.assertNotContains(response, "participating organizations")
        self.assertContains(response, "جميع الحقوق محفوظة © فرصتي 2026")

    def test_opportunity_content_follows_selected_language(self):
        organization = Organization.objects.create(
            name="جامعة القصيم",
            org_type="university",
        )
        opportunity = Opportunity.objects.create(
            title="تدريب تعاوني - أمن سيبراني",
            description="فرصة تدريب تعاوني - أمن سيبراني لطلبة الجامعات في منطقة القصيم.",
            field="أمن سيبراني",
            city="بريدة",
            organization=organization,
            requirements="معرفة أساسية بالشبكات والحماية",
        )

        response = self.client.get(reverse("opportunity_list"))
        self.assertContains(response, "تدريب تعاوني - أمن سيبراني")

        response = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": reverse("opportunity_list")},
            follow=True,
        )
        self.assertContains(response, "Cooperative Training - Cybersecurity")
        self.assertContains(response, "Cybersecurity")
        self.assertNotContains(response, "تدريب تعاوني - أمن سيبراني")

        response = self.client.get(reverse("opportunity_detail", args=[opportunity.pk]))
        self.assertContains(response, "Cooperative Training - Cybersecurity")
        self.assertContains(response, "Qassim University")
        self.assertContains(response, "Buraidah")

        response = self.client.post(
            reverse("set_language"),
            {"language": "ar", "next": reverse("opportunity_detail", args=[opportunity.pk])},
            follow=True,
        )
        self.assertContains(response, "تدريب تعاوني - أمن سيبراني")
        self.assertContains(response, "جامعة القصيم")

    def test_register_creates_user_with_username(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "testuser",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(get_user_model().objects.filter(username="testuser").exists())

    def test_login_keeps_username_visible_after_login(self):
        user = get_user_model().objects.create_user(username="ali", password="StrongPass123!")

        response = self.client.post(
            reverse("login"),
            {"username": user.username, "password": "StrongPass123!"},
            follow=True,
        )

        self.assertRedirects(response, reverse("home"))
        self.assertContains(response, user.username)

    def test_language_switch_url_is_available(self):
        response = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": reverse("home")},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Explore opportunities")
        self.assertContains(response, 'dir="ltr"')

        response = self.client.post(
            reverse("set_language"),
            {"language": "ar", "next": reverse("home")},
            follow=True,
        )

        self.assertContains(response, "استكشف الفرص")
        self.assertContains(response, 'dir="rtl"')

    def test_about_page_shows_platform_explanation_and_team(self):
        response = self.client.get(reverse("about"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "كيف يعمل موقع فرصتي؟")
        self.assertContains(response, "Jana Al-Hussein")
        self.assertContains(response, "Reem Al-Rashidi")
        self.assertContains(response, "من نحن")

        response = self.client.post(
            reverse("set_language"),
            {"language": "en", "next": reverse("about")},
            follow=True,
        )

        self.assertContains(response, "How Forsati works")
        self.assertContains(response, "About Us")
        self.assertContains(response, "Maria Al-Mutairi")
        self.assertNotContains(response, ">Contact Us<")

    def test_partner_cards_link_to_official_sites_and_use_local_logos(self):
        Organization.objects.create(
            name="جامعة القصيم",
            org_type="university",
            website="https://www.qu.edu.sa/",
            logo="qu",
        )
        Organization.objects.create(
            name="مصرف الراجحي",
            org_type="bank",
            website="https://www.alrajhibank.com.sa/",
            logo="raj",
        )
        Organization.objects.create(
            name="وزارة التعليم",
            org_type="gov",
            website="https://www.moe.gov.sa/",
            logo="moe",
        )

        response = self.client.get(reverse("home"))

        self.assertContains(response, 'href="https://www.qu.edu.sa/"')
        self.assertContains(response, 'href="https://www.alrajhibank.com.sa/"')
        self.assertContains(response, 'href="https://www.moe.gov.sa/"')
        self.assertContains(response, "images/partners/qu.png")
        self.assertContains(response, "images/partners/raj.png")
        self.assertContains(response, "images/partners/moe.png")

    def test_seed_demo_adds_opportunities_idempotently(self):
        call_command("seed_demo", verbosity=0)

        self.assertEqual(Opportunity.objects.count(), 26)
        self.assertTrue(Opportunity.objects.filter(field="دعم فني").exists())
        self.assertTrue(Opportunity.objects.filter(field="تحليل نظم").exists())

        call_command("seed_demo", verbosity=0)
        self.assertEqual(Opportunity.objects.count(), 26)
