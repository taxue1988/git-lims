#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地WebSocket客户端程序
用于接收来自云服务器的指令并执行相应操作
"""

import asyncio
import websockets
import json
import logging
import sys
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('websocket_client.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class LocalWebSocketClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.websocket = None
        self.running = False
        
    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            logger.info(f"正在连接到服务器: {self.server_url}")
            self.websocket = await websockets.connect(
                self.server_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            logger.info("WebSocket连接成功建立！")
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
    
    async def listen_for_commands(self):
        """监听来自服务器的指令"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(data)
                except json.JSONDecodeError:
                    logger.error(f"收到无效的JSON消息: {message}")
                except Exception as e:
                    logger.error(f"处理消息时发生错误: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket连接已关闭")
        except Exception as e:
            logger.error(f"监听消息时发生错误: {e}")
    
    async def handle_message(self, data):
        """处理收到的消息"""
        message_type = data.get('type')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if message_type == 'command':
            command = data.get('command')
            sender = data.get('sender', '未知')
            
            logger.info(f"[{timestamp}] 收到来自 {sender} 的指令: {command}")
            
            # 执行指令
            if command == 'hello':
                print("hello")  # 这里打印hello，满足您的需求
                logger.info("已执行hello指令")
            else:
                logger.info(f"收到未知指令: {command}")
                
        elif message_type == 'connection_established':
            logger.info(f"[{timestamp}] 服务器确认连接建立")
            
        elif message_type == 'error':
            error_message = data.get('message', '未知错误')
            logger.error(f"[{timestamp}] 服务器错误: {error_message}")
            
        else:
            logger.info(f"[{timestamp}] 收到消息: {data}")
    
    async def send_heartbeat(self):
        """发送心跳包保持连接"""
        while self.running and self.websocket:
            try:
                if self.websocket.closed:
                    break
                    
                heartbeat_data = {
                    'type': 'heartbeat',
                    'timestamp': datetime.now().isoformat(),
                    'client_type': 'local_python_client'
                }
                await self.websocket.send(json.dumps(heartbeat_data))
                logger.debug("心跳包已发送")
                await asyncio.sleep(30)  # 每30秒发送一次心跳
                
            except Exception as e:
                logger.error(f"发送心跳包失败: {e}")
                break
    
    async def run(self):
        """运行客户端"""
        self.running = True
        
        while self.running:
            try:
                # 尝试连接
                if await self.connect():
                    # 启动心跳任务
                    heartbeat_task = asyncio.create_task(self.send_heartbeat())
                    
                    # 监听消息
                    await self.listen_for_commands()
                    
                    # 取消心跳任务
                    heartbeat_task.cancel()
                    
                else:
                    logger.error("连接失败，5秒后重试...")
                    await asyncio.sleep(5)
                    
            except KeyboardInterrupt:
                logger.info("收到中断信号，正在关闭客户端...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"运行时发生错误: {e}")
                logger.info("5秒后重试...")
                await asyncio.sleep(5)
        
        # 清理资源
        if self.websocket:
            await self.websocket.close()
        logger.info("客户端已关闭")

def main():
    """主函数"""
    # 配置服务器地址 - 请根据您的实际情况修改
    # 如果您的云服务器IP是62.234.51.178，请修改下面的地址
    SERVER_IP = "62.234.51.178"  # 替换为您的云服务器IP
    SERVER_PORT = "8000"  # Django开发服务器默认端口，生产环境可能是80或443
    
    # 根据是否使用HTTPS确定协议
    USE_SSL = False  # 如果您的服务器使用HTTPS，请设置为True
    protocol = "wss" if USE_SSL else "ws"
    
    server_url = f"{protocol}://{SERVER_IP}:{SERVER_PORT}/ws/command/"
    
    print(f"本地WebSocket客户端启动中...")
    print(f"服务器地址: {server_url}")
    print(f"日志文件: websocket_client.log")
    print(f"按 Ctrl+C 退出程序")
    print("-" * 50)
    
    # 创建并运行客户端
    client = LocalWebSocketClient(server_url)
    
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print("\n程序已退出")

if __name__ == "__main__":
    main()
