import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'test_group'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        # Parse the message from the WebSocket
        try:
            data = json.loads(text_data)
            message_content = data.get('message', {})
            sender = data.get('sender', 'unknown')

            # Create a new message structure for broadcasting
            broadcast_message = {
                'type': 'chat_message',
                'message': message_content,
                'sender': sender
            }

            # Send the parsed message to the group
            await self.channel_layer.group_send(
                self.room_group_name,
                broadcast_message
            )
        except json.JSONDecodeError:
            # If the message is not valid JSON, handle it gracefully
            # For example, you could log the error or send an error message back
            pass

    # Receive message from room group
    async def chat_message(self, event):
        # The event contains the parsed message and sender
        message_to_send = {
            'message': event['message'],
            'sender': event.get('sender', 'unknown')
        }

        # Send the structured message to the WebSocket
        await self.send(text_data=json.dumps(message_to_send))

class GcmsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'gcms_group'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        # Don't parse the message, just pass it on to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': text_data
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=message)
