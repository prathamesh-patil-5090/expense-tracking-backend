from django.urls import include, path
from rest_framework.routers import DefaultRouter

from authentication.views import (
    LoginViewSet,
    LogoutView,
    ProfileViewSet,
    RefreshViewSet,
    RegisterViewSet,
)

router = DefaultRouter()
router.register(r"login", LoginViewSet, basename="login")
router.register(r"register", RegisterViewSet, basename="register")
router.register(r"profile", ProfileViewSet, basename="profile")
router.register(r"refresh", RefreshViewSet, basename="refresh")

urlpatterns = [
    path("", include(router.urls)),
    path("logout/", LogoutView.as_view()),
]
