from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Comment(models.Model):
    post_id = models.IntegerField(max_length=10)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=750)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_At = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.user