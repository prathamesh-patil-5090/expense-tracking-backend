from rest_framework import serializers

from tracker.models import ExpenseItem, Expenses


class ExpenseItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseItem
        fields = [
            "id",
            "expense_item_name",
            "expense_item_quantity",
            "expense_price_per_item",
            "created_at",
            "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

class ExpenseSerializer(serializers.ModelSerializer):
    expense_items = ExpenseItemSerializer(many=True)

    class Meta:
        model = Expenses
        fields = [
            "id",
            "user",
            "expense_items",
            "expense_total_price",
            "expense_paid",
            "created_at",
            "updated_at"
        ]

        read_only_fields = ["id" , "user", "created_at", "expense_total_price","updated_at"]


    def create(self, validated_data):
        expense_items = validated_data.pop('expense_items', [])

        expense = Expenses.objects.create(**validated_data)

        for item_data in expense_items:
            item = ExpenseItem.objects.create(**item_data)
            expense.expense_items.add(item)

        expense.save()
        return expense

    def update(self, instance, validated_data):
        expense_items = validated_data.pop('expense_items', [])

        for attr, val in validated_data.items():
            setattr(instance, attr, val)


        for item_data in expense_items:
            item = ExpenseItem.objects.create(**item_data)
            instance.expense_items.add(item)

        instance.save()
        return instance

    def delete(self, instance):
        instance.delete()
