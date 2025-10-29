# websocket_client.py
import json
import threading
import time
import websocket
from main_1 import gypl  # 从 main_1.py 导入 gypl 类

# --- WebSocket 服务器配置 ---
SERVER_IP = "62.234.51.178"
WEBSOCKET_URL = f"ws://{SERVER_IP}/ws/test/gypl_station_1/"

class WebSocketClient:
    def __init__(self, url, station_controller):
        """
        初始化WebSocket客户端。
        :param url: WebSocket服务器的URL。
        :param station_controller: gypl类的实例，用于执行硬件操作。
        """
        self.station = station_controller
        self.ws = websocket.WebSocketApp(url,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws.on_open = self.on_open

    def on_message(self, ws, message):
        """处理从服务器收到的WebSocket消息。"""
        print(f"< 收到服务器指令: {message}")
        try:
            data = json.loads(message)
            command = data.get("command")
            payload = data.get("payload")

            if command == "gtcl_all":
                print("=== 收到 gtcl_all 实验指令 ===")
                if not payload:
                    print("错误：指令 'gtcl_all' 缺少 'payload'。")
                    return

                # 从 payload 中解析列表和参数
                solids_list = payload.get("solids_list")
                liquids_list = payload.get("liquids_list")
                bottle_15ml_pos = payload.get("bottle_15ml_pos")
                start_tip_pos = payload.get("start_tip_pos")

                # 验证所有必需的参数是否存在
                if not all([solids_list is not None, liquids_list is not None, bottle_15ml_pos, start_tip_pos]):
                    print("错误：'payload' 中缺少 'solids_list', 'liquids_list', 'bottle_15ml_pos' 或 'start_tip_pos'。")
                    return

                print(f"实验参数解析完成：\n"
                      f"  - 固体列表: {solids_list}\n"
                      f"  - 液体列表: {liquids_list}\n"
                      f"  - 试管位置: {bottle_15ml_pos}\n"
                      f"  - 起始枪头: {start_tip_pos}")

                # 在新线程中执行实验，避免阻塞WebSocket
                experiment_thread = threading.Thread(
                    target=self._run_experiment_with_feedback,
                    kwargs={
                        'solids_list': solids_list,
                        'liquids_list': liquids_list,
                        'bottle_15ml_pos': bottle_15ml_pos,
                        'start_tip_pos': start_tip_pos
                    }
                )
                experiment_thread.start()
                print("--- 实验线程已启动 ---")

        except json.JSONDecodeError:
            print(f"错误：收到的消息不是有效的JSON格式: {message}")
        except Exception as e:
            print(f"处理指令时发生未知错误: {e}")

    def _run_experiment_with_feedback(self, solids_list, liquids_list, bottle_15ml_pos, start_tip_pos):
        """运行实验并反馈结果"""
        try:
            # 执行实验并获取包含更新后列表的结果字典
            experiment_result = self.station.gtcl_all(
                solids_list=solids_list,
                liquids_list=liquids_list,
                bottle_15ml_pos=bottle_15ml_pos,
                start_tip_pos=start_tip_pos
            )

            # 这是要发送给前端页面的实际消息内容
            message_for_web_client = {
                "command": "gtcl_all_result",
                "status": "success",
                "payload": experiment_result
            }

            # 我们需要将此消息包装在服务器能理解的 "send_to_client" 指令中
            # 并指定目标为前端页面的客户端ID 'web_client'
            response_payload = {
                'command': 'send_to_client',
                'target_client_id': 'web_client',
                'message': message_for_web_client
            }

            self.ws.send(json.dumps(response_payload))
            print(f"> 实验成功，已打包结果并发送至 web_client: {experiment_result}")
            
        except Exception as e:
            print(f"实验执行或数据发送过程中发生错误: {e}")
            
            # 发送错误信息回服务器
            error_payload = {
                "command": "experiment_error",
                "payload": {
                    "error": str(e),
                    "solids_list": solids_list,
                    "liquids_list": liquids_list,
                    "bottle_15ml_pos": bottle_15ml_pos,
                    "start_tip_pos": start_tip_pos
                }
            }
            
            try:
                self.ws.send(json.dumps(error_payload))
            except:
                print("无法将错误信息发送到服务器")

    def on_error(self, ws, error):
        print(f"--- WebSocket 发生错误: {error} ---")

    def on_close(self, ws, close_status_code, close_msg):
        print("### WebSocket 连接已关闭 ###")

    def on_open(self, ws):
        print("### WebSocket 连接已建立 ###")
        # 启动状态报告线程
        threading.Thread(target=self._status_reporter, daemon=True).start()

    def _status_reporter(self):
        """在后台线程中运行，定期报告设备状态。"""
        while True:
            try:
                if not self.ws.sock or not self.ws.sock.connected:
                    print("状态报告器：连接已断开，停止报告。")
                    break
                status = self.station.get_device_status()
                payload = {
                    "command": "device_status_update",
                    "payload": status
                }
                self.ws.send(json.dumps(payload))
                print(f"> 已发送状态: {status}")
            except Exception as e:
                print(f"发送状态时出错: {e}")
                break
            time.sleep(1)

    def run(self):
        """启动WebSocket客户端并永久运行。"""
        print("正在启动 WebSocket 客户端...")
        self.ws.run_forever()

if __name__ == '__main__':
    # 1. 初始化设备控制器
    # 这里的参数可以根据实际情况修改
    station_controller = gypl(com_port='COM21', arm_ip='192.168.58.210')

    # 2. 创建并运行 WebSocket 客户端
    client = WebSocketClient(WEBSOCKET_URL, station_controller)
    client.run()

