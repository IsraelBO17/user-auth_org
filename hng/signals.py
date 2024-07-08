from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import Organisation

User  = get_user_model()

@receiver(post_save, sender=User)
def new_user_created(sender, instance, created, **kwargs):
    if created:
        org = Organisation.objects.create(
            name=f"{instance.firstName}'s Organisation",
        )
        org.users.add(instance)