from django.db import models


class PaymentQuerySet(models.QuerySet):
    def confirmed(self):
        return self.filter(status='confirmed')

    def pending(self):
        return self.filter(status='pending')

    def total_amount(self):
        from django.db.models import Sum
        result = self.aggregate(total=Sum('amount'))
        return result['total'] or 0
