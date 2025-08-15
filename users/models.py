from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone

from common.utils import years_since


class CustomUserQuerySet(models.QuerySet):
    def verified_phone(self):
        return self.filter(is_verified_phone=True)

    def not_verified_phone(self):
        return self.filter(is_verified_phone=False)

    def not_deleted(self):
        return self.filter(deleted_at__isnull=True)


class CustomUserManager(BaseUserManager.from_queryset(CustomUserQuerySet)):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("The Phone number must be set")
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault(
            "birth_date", timezone.now().date()
        )  # or use a placeholder
        extra_fields.setdefault("gender", "male")  # or another default

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(phone, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"

    class Role(models.TextChoices):
        PATIENT = "patient", "Patient"
        ASSISTANT = "assistant", "Assistant"
        DOCTOR = "doctor", "Doctor"
        ADMIN = "admin", "Admin"

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    image = models.ImageField(upload_to="images/users/%Y/%m/%d/", null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender, null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    # for Now ALL Users Are verified by Default:
    is_verified_phone = models.BooleanField(default=False)

    is_verified_email = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    role = models.CharField(max_length=10, choices=Role, default=Role.PATIENT)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = CustomUserManager()

    @property
    def age(self):
        return years_since(self.birth_date)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    class Meta:
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-updated_at"]),
            models.Index(fields=["-birth_date"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone})"

    @property
    def full_name(self):
        "Returns the person's full name."
        return f"{self.first_name} {self.last_name}"

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()
