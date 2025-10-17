import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "test_group",
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "test_group",
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        # Send message to the group
        await self.channel_layer.group_send(
            "test_group",
            {
                'type': 'test_message',
                'message': text_data
            }
        )

    # Receive message from group
    async def test_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))

