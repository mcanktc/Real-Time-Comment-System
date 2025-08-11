from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .serializers import CommentSerializer
from .models import Comment
from rest_framework.permissions import IsAuthenticated
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

def broadcast_comment(event_type: str, data: dict, post_id: int):
    group = f"post_{post_id}_comments"
    payload = {"type": event_type, "data": data}

    def _send():
        async_to_sync(get_channel_layer().group_send)(
            group, {"type": "comment_event", "payload": payload}
        )

    transaction.on_commit(_send)

class CommentListView(ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Comment.objects.filter(is_deleted=False)
        post_id = self.request.query_params.get("post")
        return qs.filter(post_id=post_id) if post_id else qs
    
    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        broadcast_comment(
            "comment.created",
            CommentSerializer(instance).data,
            post_id=instance.post_id,
        )

class CommentDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"  

    def get_queryset(self):
        return Comment.objects.filter(is_deleted=False)

    def perform_update(self, serializer):
        instance = serializer.save()
        broadcast_comment(
            "comment.updated",
            CommentSerializer(instance).data,
            post_id=instance.post_id,
        )

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
        broadcast_comment(
            "comment.deleted",
            {"id": instance.pk, "post_id": instance.post_id},
            post_id=instance.post_id,
        )