
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("opportunities/", views.opportunity_list, name="opportunity_list"),
    path("opportunities/<int:pk>/", views.opportunity_detail, name="opportunity_detail"),
    path("opportunities/<int:pk>/apply/", views.apply, name="apply"),
    path("my-applications/", views.my_applications, name="my_applications"),
    path("ai-search/", views.ai_search, name="ai_search"),
    path("coach/", views.coach, name="coach"),
    path("org/register/", views.org_register, name="org_register"),
    path("org/dashboard/", views.org_dashboard, name="org_dashboard"),
    path("org/post/", views.post_opportunity, name="post_opportunity"),
    path("applications/<int:pk>/<str:status>/", views.application_status,
         name="application_status"),
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
