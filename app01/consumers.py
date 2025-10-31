import json
from channels.generic.websocket import AsyncWebsocketConsumer

# 定义一个常量来区分客户端类型
WEB_CLIENT_PREFIX = "web_"
DEVICE_CLIENT_PREFIX = "gypl_station_"

class TestConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 兼容带与不带 client_id 的两种路由
        self.client_id = self.scope['url_route']['kwargs'].get('client_id')
        if not self.client_id:
            # 无 client_id 视为网页端，使用通道名生成临时ID
            self.client_id = f"{WEB_CLIENT_PREFIX}{self.channel_name}"
        self.client_group_name = f"client_{self.client_id}"

        # 1. 每个客户端都加入自己的私有组
        await self.channel_layer.group_add(
            self.client_group_name,
            self.channel_name
        )

        # 2. 如果是网页客户端，则额外加入“工站观察者”组
        if self.client_id.startswith(WEB_CLIENT_PREFIX):
            await self.channel_layer.group_add(
                "station_observers",
                self.channel_name
            )
            print(f"网页客户端 {self.client_id} 已连接，并加入观察者组")
        else:
            print(f"设备客户端 {self.client_id} 已连接")

        await self.accept()

    async def disconnect(self, close_code):
        # 离开所有相关组
        if self.client_id.startswith(WEB_CLIENT_PREFIX):
            await self.channel_layer.group_discard("station_observers", self.channel_name)
        
        await self.channel_layer.group_discard(self.client_group_name, self.channel_name)
        print(f"客户端 {self.client_id} 已断开")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            command = data.get('command')

            if command == 'device_status_update':
                # --- A. 处理来自设备的【状态更新】 ---
                # 将状态广播给所有观察者（网页）
                await self.channel_layer.group_send(
                    "station_observers",
                    {
                        'type': 'station_status_broadcast',
                        'payload': data.get('payload'),
                        'sender': self.client_id
                    }
                )
            
            elif command == 'send_to_client':
                # --- B. 处理来自网页的【定向指令】 ---
                target_client_id = data.get('target_client_id')
                message_to_send = data.get('message', '无消息内容')
                target_group_name = f"client_{target_client_id}"

                # 1. 转发消息给目标设备
                await self.channel_layer.group_send(
                    target_group_name,
                    {
                        'type': 'targeted_message',
                        'message': message_to_send,
                        'sender': self.client_id
                    }
                )
                # 2. 给网页发送回执
                response = {'status': 'success', 'message': f"指令已成功转发给客户端 {target_client_id}"}
                await self.send(text_data=json.dumps(response))
            
            else:
                # --- C. 处理其他未知消息 ---
                response = {'status': 'info', 'message': f"收到未知指令: {command}"}
                await self.send(text_data=json.dumps(response))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'status': 'error', 'message': '无效的JSON格式。'}))

    # --- 消息处理函数 ---
    async def targeted_message(self, event):
        """处理发送给特定客户端的定向消息"""
        message_to_send = event['message']
        await self.send(text_data=json.dumps(message_to_send))

    async def station_status_broadcast(self, event):
        """处理广播给所有网页观察者的设备状态更新"""
        await self.send(text_data=json.dumps({
            'type': 'device_status',
            'station_id': event['sender'],
            'status': event['payload']
        }))

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
        # 不解析消息，直接转发入组
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': text_data
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message_to_send = {
            'message': event['message'],
        }
        await self.send(text_data=json.dumps(message_to_send))
