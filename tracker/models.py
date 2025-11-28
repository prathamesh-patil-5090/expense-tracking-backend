from django.conf import settings
from django.db import models


class ExpenseItem(models.Model):
    expense_item_name = models.CharField(max_length=255)
    expense_item_quantity = models.IntegerField(default=1)
    expense_price_per_item = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at" , "updated_at"]

    def __str__(self):
        return str(self.expense_item_name)

class Expenses(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="expenses")
    expense_items = models.ManyToManyField(ExpenseItem, related_name="expense_items")
    expense_total_price = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    expense_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
        ]
        ordering = ["-created_at" , "-updated_at"]

    def calculate_total_price(self):
        total = sum(
            item.expense_item_quantity * item.expense_price_per_item
            for item in self.expense_items.all()
        )
        return total

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if not is_new:
            self.expense_total_price = self.calculate_total_price()
            super().save(update_fields=['expense_total_price'])

    def __str__(self):
        return f"Expense #{self.pk} - {self.user.username} - ${self.expense_total_price}"
