import websocket
import json
import threading
import time
import sys
import os

# 添加项目根目录到 Python 路径，以便导入 GCMS 模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '模块开发运行代码', 'GCMS模块'))

try:
    from GCMS监测 import GCMS_module
except ImportError:
    print("警告: 无法导入 GCMS_module，将使用模拟模式")
    GCMS_module = None

class GcmsWorker:
    def __init__(self, server_url="ws://127.0.0.1:8000/ws/gcms/"):
        self.server_url = server_url
        self.ws = None
        self.gcms_module = None
        self.is_connected = False
        self.current_status = "离线"
        
        # 初始化 GCMS 模块
        self.init_gcms_module()
        
    def init_gcms_module(self):
        """初始化 GCMS 模块"""
        try:
            if GCMS_module:
                self.gcms_module = GCMS_module()
                self.current_status = "就绪"
                print("GCMS 模块初始化成功")
            else:
                print("GCMS 模块未找到，使用模拟模式")
                self.current_status = "模拟模式"
        except Exception as e:
            print(f"GCMS 模块初始化失败: {e}")
            self.current_status = "初始化失败"
    
    def on_message(self, ws, message):
        """处理从服务器接收到的消息"""
        try:
            data = json.loads(message)
            
            # 如果消息是 worker 自己发送的，则忽略
            if data.get('sender') == 'worker':
                return
                
            command = data.get('message', '')
            print(f"收到指令: {command}")
            
            # 根据不同的指令执行不同的操作
            if command == "get_status":
                self.handle_get_status()
            elif command == "get_arm_status":
                self.handle_get_arm_status()
            elif command.startswith("start_analysis_"):
                bottle_num = int(command.split("_")[-1])
                self.handle_start_analysis(bottle_num)
            elif command == "move_tower":
                self.handle_move_tower()
            elif command == "get_instrument_info":
                self.handle_get_instrument_info()
            else:
                self.send_response({'type': 'error', 'message': f"未知指令: {command}"})
                
        except json.JSONDecodeError:
            print(f"无法解析消息: {message}")
        except Exception as e:
            print(f"处理消息时出错: {e}")
            self.send_response({'type': 'error', 'message': f"处理指令时出错: {str(e)}"})
    
    def handle_get_status(self):
        """获取 GCMS 整体状态"""
        try:
            if self.gcms_module:
                # 获取实际状态
                try:
                    run_status = self.gcms_module.instrument_control.get_run_status()
                    run_mode = self.gcms_module.instrument_control.get_run_mode()
                    
                    status_info = {
                        "type": "status_update",
                        "status": "运行中" if run_mode != '"NotRun"' else "就绪",
                        "run_status": run_status,
                        "run_mode": run_mode,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                except Exception as e:
                    status_info = {
                        "type": "status_update",
                        "status": "连接失败",
                        "error": str(e),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
            else:
                # 模拟模式
                status_info = {
                    "type": "status_update",
                    "status": self.current_status,
                    "run_status": "模拟状态",
                    "run_mode": "模拟模式",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            self.send_response(status_info)
            
        except Exception as e:
            error_info = {
                "type": "error",
                "message": f"获取状态失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)
    
    def handle_get_arm_status(self):
        """获取机械臂状态"""
        try:
            if self.gcms_module:
                try:
                    b_value = self.gcms_module.get_b_status()
                    arm_info = {
                        "type": "arm_status",
                        "b_value": b_value,
                        "status": "正常",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                except Exception as e:
                    arm_info = {
                        "type": "arm_status",
                        "status": "连接失败",
                        "error": str(e),
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
            else:
                # 模拟模式
                arm_info = {
                    "type": "arm_status",
                    "b_value": 0,
                    "status": "模拟模式",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            self.send_response(arm_info)
            
        except Exception as e:
            error_info = {
                "type": "error",
                "message": f"获取机械臂状态失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)
    
    def handle_start_analysis(self, bottle_num):
        """开始分析指定瓶号的样品"""
        try:
            if self.gcms_module:
                # 在新线程中执行分析，避免阻塞 WebSocket 连接
                analysis_thread = threading.Thread(
                    target=self.run_analysis,
                    args=(bottle_num,)
                )
                analysis_thread.daemon = True
                analysis_thread.start()
                
                start_info = {
                    "type": "analysis_started",
                    "bottle_num": bottle_num,
                    "message": f"开始分析瓶号 {bottle_num} 的样品",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                # 模拟模式
                start_info = {
                    "type": "analysis_started",
                    "bottle_num": bottle_num,
                    "message": f"模拟模式：开始分析瓶号 {bottle_num} 的样品",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            self.send_response(start_info)
            
        except Exception as e:
            error_info = {
                "type": "error",
                "message": f"启动分析失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)
    
    def run_analysis(self, bottle_num):
        """在后台线程中运行分析"""
        try:
            self.current_status = "分析中"
            
            # 发送分析开始通知
            progress_info = {
                "type": "analysis_progress",
                "bottle_num": bottle_num,
                "stage": "开始分析",
                "message": f"正在分析瓶号 {bottle_num}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(progress_info)
            
            # 执行实际的分析流程
            self.gcms_module.start(bottle_num)
            
            # 发送分析完成通知
            complete_info = {
                "type": "analysis_complete",
                "bottle_num": bottle_num,
                "message": f"瓶号 {bottle_num} 分析完成",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(complete_info)
            
            self.current_status = "就绪"
            
        except Exception as e:
            error_info = {
                "type": "analysis_error",
                "bottle_num": bottle_num,
                "message": f"分析过程中出错: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)
            self.current_status = "错误"
    
    def handle_move_tower(self):
        """移动塔位置"""
        try:
            if self.gcms_module:
                try:
                    self.gcms_module.gc_move_to_tower()
                    tower_info = {
                        "type": "tower_moved",
                        "message": "塔位置移动完成",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                except Exception as e:
                    tower_info = {
                        "type": "error",
                        "message": f"塔位置移动失败: {str(e)}",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
            else:
                # 模拟模式
                tower_info = {
                    "type": "tower_moved",
                    "message": "模拟模式：塔位置移动完成",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            self.send_response(tower_info)
            
        except Exception as e:
            error_info = {
                "type": "error",
                "message": f"移动塔位置失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)
    
    def handle_get_instrument_info(self):
        """获取仪器信息"""
        try:
            if self.gcms_module:
                try:
                    model = self.gcms_module.instrument_control.get_model()
                    laboratory = self.gcms_module.instrument_control.get_laboratory()
                    
                    instrument_info = {
                        "type": "instrument_info",
                        "model": model,
                        "laboratory": laboratory,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                except Exception as e:
                    instrument_info = {
                        "type": "error",
                        "message": f"获取仪器信息失败: {str(e)}",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
            else:
                # 模拟模式
                instrument_info = {
                    "type": "instrument_info",
                    "model": "模拟 GCMS 设备",
                    "laboratory": "模拟实验室",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            
            self.send_response(instrument_info)
            
        except Exception as e:
            error_info = {
                "type": "error",
                "message": f"获取仪器信息失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)
    
    def send_response(self, message):
        """发送响应消息到服务器"""
        if self.ws and self.is_connected:
            try:
                # 直接发送消息，不再进行二次打包
                response_data = {
                    "message": message,
                    "sender": "worker"  # 添加发送者标识
                }
                self.ws.send(json.dumps(response_data))
            except Exception as e:
                print(f"发送消息失败: {e}")
    
    def on_error(self, ws, error):
        """处理 WebSocket 错误"""
        print(f"WebSocket 错误: {error}")
        self.is_connected = False
    
    def on_close(self, ws, close_status_code, close_msg):
        """处理 WebSocket 连接关闭"""
        print("WebSocket 连接已关闭")
        self.is_connected = False
    
    def on_open(self, ws):
        """处理 WebSocket 连接建立"""
        print("GCMS Worker 已连接到服务器")
        self.is_connected = True
        
        # 发送初始状态
        initial_status = {
            "type": "worker_connected",
            "message": "GCMS Worker 已连接",
            "status": self.current_status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.send_response(initial_status)
    
    def start(self):
        """启动 Worker"""
        print(f"正在连接到 {self.server_url}")
        

        self.ws = websocket.WebSocketApp(
            self.server_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.on_open = self.on_open
        
        # 启动 WebSocket 连接（这会阻塞当前线程）
        self.ws.run_forever()

if __name__ == "__main__":
    # 创建并启动 GCMS Worker
    worker = GcmsWorker()
    
    try:
        worker.start()
    except KeyboardInterrupt:
        print("\n正在关闭 GCMS Worker...")
    except Exception as e:
        print(f"Worker 运行出错: {e}")
