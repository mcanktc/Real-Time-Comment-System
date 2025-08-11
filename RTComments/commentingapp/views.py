from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .serializers import CommentSerializer
from .models import Comment
from rest_framework.permissions import IsAuthenticateds

class CommentListView(ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Comment.objects.filter(is_deleted=False)
        post_id = self.request.query_params.get("post")
        return qs.filter(post_id=post_id) if post_id else qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CommentDetail(RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticateds]
    lookup_field = "pk"  

    def get_queryset(self):
        return Comment.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save(update_fields=["is_deleted"])
