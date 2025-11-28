
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from tracker.views import ExpenseViewSet

router = DefaultRouter()
router.register(r"expenses", ExpenseViewSet, basename="expenses")

urlpatterns = [
    path("", include(router.urls)),
]
