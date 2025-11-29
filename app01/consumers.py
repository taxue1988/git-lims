import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from .models import AIModelConfig, AIChatSession, AIChatMessage
import requests
import asyncio

# 定义一个常量来区分客户端类型
WEB_CLIENT_PREFIX = "web_"
DEVICE_CLIENT_PREFIX = "gypl_station_"

class AIChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            command = data.get('command')
            
            if command == 'start_chat':
                await self.start_chat(data)
        except Exception as e:
            await self.send(text_data=json.dumps({'error': str(e)}))

    async def start_chat(self, data):
        provider = data.get("provider")
        messages = data.get("messages", [])
        session_id = data.get("session_id")
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.send(text_data=json.dumps({'error': 'Unauthorized'}))
            return

        # Get Config
        config = await sync_to_async(AIModelConfig.objects.filter(user=user, provider=provider, is_active=True).first)()
        if not config:
            await self.send(text_data=json.dumps({'error': f"未配置 {provider} 的API Key"}))
            return

        # Get or Create Session
        session = None
        if session_id:
            try:
                session = await sync_to_async(AIChatSession.objects.get)(id=session_id, user=user)
            except AIChatSession.DoesNotExist:
                pass
        
        if not session:
            title = messages[0]['content'][:20] if messages else "新对话"
            session = await sync_to_async(AIChatSession.objects.create)(user=user, title=title)
            # Send session ID back to client
            await self.send(text_data=json.dumps({'type': 'session_info', 'session_id': session.id}))

        # Save User Message
        last_user_msg = messages[-1]
        if last_user_msg['role'] == 'user':
            await sync_to_async(AIChatMessage.objects.create)(
                session=session,
                role='user',
                content=last_user_msg['content'],
                model_name=config.model_name
            )

        # Prepare Request
        api_key = config.api_key
        base_url = config.base_url
        model = config.model_name
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": messages,
            "stream": True,
            "model": model
        }
        
        url = ""
        if provider == "deepseek":
            url = "https://api.deepseek.com/chat/completions"
            if not model: payload["model"] = "deepseek-chat"
        elif provider == "kimi":
            url = "https://api.moonshot.cn/v1/chat/completions"
            if not model: payload["model"] = "moonshot-v1-8k"
        else:
             if base_url:
                 url = base_url if base_url.endswith("/chat/completions") else f"{base_url.rstrip('/')}/chat/completions"
             else:
                 await self.send(text_data=json.dumps({'error': "Unknown provider and no Base URL"}))
                 return

        # Streaming Request
        try:
            # Run requests in a thread executor
            loop = asyncio.get_running_loop()
            
            def make_request_and_stream():
                try:
                    with requests.post(url, json=payload, headers=headers, stream=True, timeout=60, proxies={"http": None, "https": None}) as response:
                        if response.status_code != 200:
                            return f"API Error {response.status_code}: {response.text}", None

                        full_content = ""
                        full_reasoning = ""
                        
                        for line in response.iter_lines():
                            if line:
                                line_decoded = line.decode('utf-8')
                                if line_decoded.startswith("data: "):
                                    data_str = line_decoded[6:]
                                    if data_str == "[DONE]":
                                        continue
                                    try:
                                        chunk = json.loads(data_str)
                                        delta = chunk['choices'][0]['delta']
                                        
                                        # Prepare message to send
                                        msg_payload = {}
                                        
                                        content = delta.get('content', '')
                                        reasoning = delta.get('reasoning_content', '')
                                        
                                        if content:
                                            msg_payload['content'] = content
                                            full_content += content
                                        if reasoning:
                                            msg_payload['reasoning_content'] = reasoning
                                            full_reasoning += reasoning
                                            
                                        if msg_payload:
                                            # Send immediately back to async loop
                                            future = asyncio.run_coroutine_threadsafe(self.send(text_data=json.dumps(msg_payload)), loop)
                                            future.result() # Wait for send to complete to ensure order
                                            
                                    except Exception:
                                        pass
                        return full_content, full_reasoning
                except Exception as e:
                    return f"Request Error: {str(e)}", None

            # Execute the blocking streaming function in a thread
            result = await loop.run_in_executor(None, make_request_and_stream)
            
            # Check if result is a tuple (success) or error string
            if isinstance(result, tuple):
                full_content, full_reasoning = result
                
                # Save Assistant Message
                if full_content or full_reasoning:
                    await sync_to_async(AIChatMessage.objects.create)(
                        session=session,
                        role='assistant',
                        content=full_content,
                        reasoning_content=full_reasoning,
                        model_name=payload["model"]
                    )
                    session.updated_at = timezone.now()
                    await sync_to_async(session.save)()
            else:
                 await self.send(text_data=json.dumps({'error': result}))

        except Exception as e:
            await self.send(text_data=json.dumps({'error': str(e)}))

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
        # 解析入站文本，透传 JSON 对象；若非 JSON，则包裹为 {"message": 原始文本}
        try:
            payload = json.loads(text_data)
        except Exception:
            payload = {"message": text_data}

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': payload
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        # 直接发送组内的 JSON 对象，避免再次包裹导致客户端收到转义字符串
        await self.send(text_data=json.dumps(event['message']))

class HplcConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'hplc_group'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            payload = json.loads(text_data)
        except Exception:
            payload = {"message": text_data}

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': payload
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))