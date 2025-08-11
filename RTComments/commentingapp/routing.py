from django.urls import re_path
from .consumers import CommentStream

websocket_urlpatterns = [
    re_path(r"ws/posts/(?P<post_id>\d+)/comments/$", CommentStream.as_asgi()),
]
