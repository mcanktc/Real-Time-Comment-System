from rest_framework import serializers
from .models import Comment
import bleach

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"
        read_only_fields = ["user", "created_at", "updated_at", "is_deleted"]

    def validate_text(self, value):
        clean_text = bleach.clean(value)
        return clean_text