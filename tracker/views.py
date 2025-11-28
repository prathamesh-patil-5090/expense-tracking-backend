from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from tracker.models import Expenses
from tracker.serializers import ExpenseSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ExpenseSerializer

    def get_queryset(self):
        return Expenses.objects.filter(user=self.request.user)


    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
