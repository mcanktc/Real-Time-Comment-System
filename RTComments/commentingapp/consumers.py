from channels.generic.websocket import AsyncJsonWebsocketConsumer

class CommentStream(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.post_id = self.scope["url_route"]["kwargs"]["post_id"]
        self.group = f"post_{self.post_id}_comments"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)

    async def comment_event(self, event):
        await self.send_json(event["payload"])
