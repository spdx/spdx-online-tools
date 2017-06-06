from django.db import models
import os
from datetime import datetime
from django import forms
from django.contrib.auth.models import User


class UserID(models.Model):
	user = models.OneToOneField(User)
	#password = models.CharField("Password",max_length=32, null=False, blank=False)
	organisation = models.CharField("Organisation",max_length=64, null=False, blank=False)
	lastlogin = models.DateField("Last Login",default=datetime.now,blank=True)
	def __str__(self):
		return self.user.username
# Create your models here.
