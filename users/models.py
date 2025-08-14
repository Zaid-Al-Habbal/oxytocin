from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib import admin

from simple_history.models import HistoricalRecords

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
        MALE = "male", _("Male")
        FEMALE = "female", _("Female")

    class Role(models.TextChoices):
        PATIENT = "patient", _("Patient")
        ASSISTANT = "assistant", _("Assistant")
        DOCTOR = "doctor", _("Doctor")
        ADMIN = "admin", _("Admin")

    first_name = models.CharField(max_length=50, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=50, verbose_name=_("Last Name"))
    phone = models.CharField(max_length=20, unique=True, verbose_name=_("Phone"))
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True, verbose_name=_("Email"))
    image = models.ImageField(upload_to="images/users/%Y/%m/%d/", null=True, blank=True, verbose_name=_("Image"))
    gender = models.CharField(max_length=10, choices=Gender, null=True, blank=True, verbose_name=_("Gender"))
    birth_date = models.DateField(null=True, blank=True, verbose_name=_("Birth Date"))

    # for Now ALL Users Are verified by Default:
    is_verified_phone = models.BooleanField(default=False, verbose_name=_("Phone Verified"))
    is_verified_email = models.BooleanField(default=False, verbose_name=_("Email Verified"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    is_staff = models.BooleanField(default=False, verbose_name=_("Staff Status"))
    last_login = models.DateTimeField(null=True, blank=True, verbose_name=_("Last Login"))
    role = models.CharField(max_length=10, choices=Role, default=Role.PATIENT, verbose_name=_("Role"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Deleted At"))

    history = HistoricalRecords(cascade_delete_history=True)

    objects = CustomUserManager()

    @property
    @admin.display(description=_("Age"))
    def age(self):
        return years_since(self.birth_date)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-updated_at"]),
            models.Index(fields=["-birth_date"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.phone})"

    @property
    @admin.display(description=_("Full Name"))
    def full_name(self):
        "Returns the person's full name."
        return f"{self.first_name} {self.last_name}"

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save()
