from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MANAGER = "manager", "Manager"
        CASHIER = "cashier", "Cashier"
        CAPTAIN = "captain", "Captain"
        KITCHEN = "kitchen", "Kitchen"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CASHIER)
    phone_number = models.CharField(max_length=20, blank=True)
    pin_code = models.CharField(max_length=6, blank=True)
    is_shift_active = models.BooleanField(default=False)

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_cashier(self):
        return self.role in {self.Role.ADMIN, self.Role.MANAGER, self.Role.CASHIER}

# Create your models here.
