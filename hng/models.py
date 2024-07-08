import uuid
from django.contrib.auth.models import AbstractBaseUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager


class User(AbstractBaseUser):
    userId = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True)
    email = models.EmailField(_("email address"), unique=True)
    firstName = models.CharField(_("first name"), max_length=150)
    lastName = models.CharField(_("last name"), max_length=150)
    phone = models.CharField(max_length=256, blank=True)
    last_login = None
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['firstName', 'lastName']

    objects = CustomUserManager()

    def __str__(self):
        return self.email
    



class Organisation(models.Model):
    orgId = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=255, blank=True)
    users = models.ManyToManyField(User)

    def __str__(self):
        return self.name
