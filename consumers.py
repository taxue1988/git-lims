import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import logging

logger = logging.getLogger(__name__)

class CommandConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 加入命令组
        self.group_name = 'command_group'
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"WebSocket连接已建立: {self.channel_name}")
        
        # 发送连接成功消息
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': '连接已建立'
        }))

    async def disconnect(self, close_code):
        # 离开命令组
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"WebSocket连接已断开: {self.channel_name}, 代码: {close_code}")

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'send_command':
                command = text_data_json.get('command', 'hello')
                
                # 广播命令到所有连接的客户端
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'command_message',
                        'command': command,
                        'sender': 'web_admin'
                    }
                )
                
                logger.info(f"命令已发送: {command}")
                
        except json.JSONDecodeError:
            logger.error("接收到无效的JSON数据")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': '无效的JSON数据'
            }))

    async def command_message(self, event):
        command = event['command']
        sender = event['sender']
        
        # 发送命令到WebSocket
        await self.send(text_data=json.dumps({
            'type': 'command',
            'command': command,
            'sender': sender,
            'timestamp': str(timezone.now()) if 'timezone' in globals() else None
        }))

from django.utils import timezone
