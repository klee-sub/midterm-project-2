from channels.generic.websocket import AsyncJsonWebsocketConsumer

class PostConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add('posts', self.channel_name)
        await self.accept()
    async def disconnect(self, code):
        await self.channel_layer.group_discard('posts', self.channel_name)
    async def post_changed(self, event):
        await self.send_json({'type': event.get('change', 'updated'), 'post_id': event.get('post_id')})
