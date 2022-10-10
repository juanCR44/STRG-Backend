from unittest.util import _MAX_LENGTH
from django.db import models

# Create your models here.
class User(models.Model):
    email = models.CharField(max_length = 100)
    password = models.CharField(max_length = 100)
    enterprise = models.CharField(max_length = 100)