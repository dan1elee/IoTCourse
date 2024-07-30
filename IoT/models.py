from django.db import models


# Create your models here.
class Pwd(models.Model):
    user = models.CharField(max_length=32, unique=True)
    password = models.CharField(max_length=32)
