from channels.routing import URLRouter
from commentingapp.routing import websocket_urlpatterns

URLRouter(websocket_urlpatterns)