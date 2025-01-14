from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.core.exceptions import ValidationError

class Stall(models.Model):
    store_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='stall_logos/')
    contact_number = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)  # Add is_active field with default value True

    def __str__(self):
        return self.name



class AdminProfile(models.Model):
    firstname = models.CharField(max_length=50)
    middle_initial = models.CharField(max_length=1, blank=True, null=True)
    lastname = models.CharField(max_length=50)
    age = models.IntegerField()
    birthdate = models.DateField()
    address = models.TextField()
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=100)  # Remember to hash passwords
    contact_number = models.CharField(max_length=15)
    stall = models.ForeignKey('Stall', on_delete=models.CASCADE, related_name="admins", to_field='store_id')

    def clean(self):
        # Check if this stall already has an admin
        if self.stall:
            existing_admin = AdminProfile.objects.filter(stall=self.stall).exclude(id=self.id).exists()
            if existing_admin:
                raise ValidationError(f'Stall {self.stall.name} already has an admin assigned.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.firstname} {self.lastname} - {self.stall.store_id}"

