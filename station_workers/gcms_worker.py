import websocket
import json
import threading
import time
import sys
import os
import shutil
from datetime import datetime

# 添加项目根目录到 Python 路径，以便导入 GCMS 模块
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '模块开发运行代码', 'GCMS模块'))

try:
    from GCMS监测 import GCMS_module
except ImportError:
    print("警告: 无法导入 GCMS_module，将使用模拟模式")
    GCMS_module = None

# 导入序列管理器
try:
    from .sequence_manager import get_sequence_file
    from .sequence_manager import get_result_csv_path
except Exception:
    # 兼容直接运行
    from sequence_manager import get_sequence_file
    from sequence_manager import get_result_csv_path
import csv

class GcmsWorker:
    def __init__(self, server_url="ws://192.168.58.8:8000/ws/gcms/"):
        self.server_url = server_url
        self.ws = None
        self.gcms_module = None
        self.is_connected = False
        self.arm_is_connected = False
        self.instrument_is_connected = False
        self.current_status = "离线"

        # 初始化 GCMS 模块
        self.init_gcms_module()

    def init_gcms_module(self):
        """初始化 GCMS 模块并独立检查其组件"""
        try:
            if GCMS_module:
                self.gcms_module = GCMS_module()

                # 独立检查机械臂连接
                if self.gcms_module.check_arm_connection():
                    self.arm_is_connected = True
                    print("机械臂连接成功")
                else:
                    self.arm_is_connected = False
                    print("错误：机械臂连接失败")

                # 独立检查GCMS仪器连接
                if self.gcms_module.check_instrument_connection():
                    self.instrument_is_connected = True
                    print("GCMS仪器连接成功")
                else:
                    self.instrument_is_connected = False
                    print("错误：GCMS仪器连接失败")

                self.current_status = "就绪"  # Worker本身是就绪的
                print("GCMS 模块初始化完成")

            else:
                print("GCMS 模块未找到，无法进行操作")
                self.current_status = "模块未找到"
        except Exception as e:
            print(f"GCMS 模块初始化失败: {e}")
            self.gcms_module = None
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
                parts = command.split("_")
                # 兼容旧格式: start_analysis_{bottle}
                if len(parts) == 3:
                    bottle_num = int(parts[-1])
                    sequence_index = None
                elif len(parts) >= 4:
                    bottle_num = int(parts[-2])
                    sequence_index = int(parts[-1])
                else:
                    self.send_response({'type': 'error', 'message': f"指令格式错误: {command}"})
                    return
                self.handle_start_analysis(bottle_num, sequence_index)
            elif command == "move_tower":
                self.handle_move_tower()
            elif command == "get_instrument_info":
                self.handle_get_instrument_info()
            elif command == "get_sequence_list":
                self.handle_get_sequence_list()
            elif command.startswith("get_result_"):
                # 兼容 archive_id 中包含下划线：格式 get_result_{bottle}_{sequence}_{archiveId...}
                payload = command[len("get_result_"):]
                bottle_num = None
                sequence_index = None
                archive_id = None
                try:
                    parts = payload.split("_")
                    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                        bottle_num = int(parts[0])
                        sequence_index = int(parts[1])
                        archive_id = "_".join(parts[2:]) if len(parts) > 2 else None
                    elif len(parts) >= 1 and parts[0].isdigit():
                        # 仅提供了 sequence（兼容旧格式 get_result_{sequence}）
                        sequence_index = int(parts[0])
                        archive_id = "_".join(parts[1:]) if len(parts) > 1 else None
                    else:
                        raise ValueError("格式不匹配")
                except Exception:
                    self.send_response({'type': 'error', 'message': f"指令格式错误: {command}"})
                    return
                self.handle_get_result(bottle_num, sequence_index, archive_id)
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
            # 检查模块是否加载，以及仪器在初始化时是否连接成功
            if self.gcms_module and self.instrument_is_connected:
                # 实时检查仪器连接
                if self.gcms_module.check_instrument_connection():
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
                            "error": f"获取仪器状态时出错: {str(e)}",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                else:
                    self.instrument_is_connected = False # 更新状态标志
                    status_info = {
                        "type": "status_update",
                        "status": "连接失败",
                        "error": "GCMS仪器通信中断",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
            else:
                status_info = {
                    "type": "status_update",
                    "status": "连接失败",
                    "error": "GCMS仪器未连接或模块初始化失败",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            self.send_response(status_info)
        except Exception as e:
            error_info = {
                "type": "error",
                "message": f"获取GCMS状态失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)
            
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
            # 检查模块是否加载，以及机械臂在初始化时是否连接成功
            if self.gcms_module and self.arm_is_connected:
                # 实时检查机械臂连接
                if self.gcms_module.check_arm_connection():
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
                            "error": f"获取机械臂状态时出错: {str(e)}",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                else:
                    self.arm_is_connected = False # 更新状态标志
                    arm_info = {
                        "type": "arm_status",
                        "status": "连接失败",
                        "error": "机械臂通信中断",
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
            else:
                arm_info = {
                    "type": "arm_status",
                    "status": "连接失败",
                    "error": "机械臂未连接或模块初始化失败",
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
        except Exception as e:
            error_info = {
                "type": "error",
                "message": f"获取机械臂状态失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)
    
    def handle_start_analysis(self, bottle_num, sequence_index=None):
        """开始分析指定瓶号的样品，可选指定序列号"""
        try:
            if self.gcms_module:
                # 在新线程中执行分析，避免阻塞 WebSocket 连接
                analysis_thread = threading.Thread(
                    target=self.run_analysis,
                    args=(bottle_num, sequence_index)
                )
                analysis_thread.daemon = True
                analysis_thread.start()
                
                start_info = {
                    "type": "analysis_started",
                    "bottle_num": bottle_num,
                    "sequence_index": sequence_index,
                    "message": f"开始分析瓶号 {bottle_num} 的样品",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.send_response(start_info)
            else:
                error_info = {
                    "type": "analysis_error",
                    "bottle_num": bottle_num,
                    "sequence_index": sequence_index,
                    "message": "GCMS模块未就绪，无法开始分析。",
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.send_response(error_info)
            
        except Exception as e:
            error_info = {
                "type": "error",
                "message": f"启动分析失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)
    
    def run_analysis(self, bottle_num, sequence_index=None):
        """在后台线程中运行分析，并发送详细进度。若提供序列号则按映射运行对应序列文件。"""
        def send_progress(stage, message):
            progress_info = {
                "type": "analysis_progress",
                "bottle_num": bottle_num,
                "sequence_index": sequence_index,
                "stage": stage,
                "message": message,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(progress_info)
 
        try:
            self.current_status = "分析中"
            send_progress("任务开始", f"开始分析瓶号 {bottle_num}")
 
            # 实际的分析流程，分解自 self.gcms_module.start(bottle_num)
            send_progress("设备准备", "移动GCMS塔...")
            self.gcms_module.gc_move_to_tower()
            time.sleep(1) # 模拟操作耗时
 
            send_progress("机械臂操作", f"机械臂夹取 {bottle_num} 号瓶至GCMS")
            self.gcms_module.kb_to_gcms(bottle_num)
            time.sleep(1)
 
            send_progress("仪器分析", "GCMS开始执行分析序列...")
            if sequence_index is not None:
                seq_file = get_sequence_file(int(sequence_index))
                if not seq_file:
                    raise RuntimeError(f"未找到序列号 {sequence_index} 对应的序列文件")
                # 调用底层仪器方法直接按文件启动
                self.gcms_module.instrument_control.start_data_acquisition(seq_file, 0, True)
            else:
                # 兼容旧逻辑：调用预设序列
                self.gcms_module.gc_action_conb()
            time.sleep(5)
 
            send_progress("等待分析完成", "GCMS运行中，请稍候...")
            while self.gcms_module.instrument_control.get_run_mode() != '"NotRun"':
                time.sleep(10)
             
            send_progress("设备复位", "分析完成，准备复位设备")
            time.sleep(5)
            self.gcms_module.gc_move_to_tower()
            time.sleep(2)
 
            send_progress("机械臂操作", f"机械臂取回 {bottle_num} 号瓶")
            self.gcms_module.gc_drop(bottle_num)
             
            # 等待结果文件生成并归档（最多等待 ~60s）
            archive_id = None
            try:
                from .sequence_manager import get_result_csv_path as _find_result
            except Exception:
                from sequence_manager import get_result_csv_path as _find_result

            max_waits = 30
            for _ in range(max_waits):
                path_try = _find_result(int(sequence_index)) if sequence_index is not None else None
                if path_try and os.path.isfile(path_try):
                    try:
                        archive_id = self.archive_result(sequence_index)
                    except Exception:
                        archive_id = None
                    break
                time.sleep(2)

            # 发送分析完成通知
            complete_info = {
                "type": "analysis_complete",
                "bottle_num": bottle_num,
                "sequence_index": sequence_index,
                "archive_id": archive_id,
                "message": f"瓶号 {bottle_num} 分析完成",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(complete_info)
            self.current_status = "就绪"
 
        except Exception as e:
            error_info = {
                "type": "analysis_error",
                "bottle_num": bottle_num,
                "sequence_index": sequence_index,
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

            
            self.send_response(instrument_info)
            
        except Exception as e:
            error_info = {
                "type": "error",
                "message": f"获取仪器信息失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(error_info)

    def handle_get_sequence_list(self):
        """获取序列清单"""
        try:
            # 构造 items 数组 [{index, name}, ...]
            items = []
            # 读取映射
            mapping = {}
            try:
                # 内部加载，若失败则为空
                from .sequence_manager import load_sequence_map  # 再次局部导入以避免循环
            except Exception:
                from sequence_manager import load_sequence_map
            mapping = load_sequence_map() or {}
            for k in sorted(mapping.keys()):
                items.append({"index": k, "name": mapping[k]})

            payload = {
                "type": "sequence_list",
                "items": items,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.send_response(payload)
        except Exception as e:
            self.send_response({
                "type": "error",
                "message": f"获取序列清单失败: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })

    def handle_get_result(self, bottle_num, sequence_index, archive_id=None):
        """读取对应序列的 tic_front.csv（或归档文件），返回裁剪后的 x/y 数据。"""
        try:
            path = None
            if archive_id:
                path = self.get_archive_file_path(archive_id)
            if not path:
                path = get_result_csv_path(int(sequence_index))
            if not path:
                # 返回详细提示，便于排查：包含用于解析的参数与基础路径（不含敏感数据名）
                self.send_response({
                    'type': 'analysis_result',
                    'bottle_num': bottle_num,
                    'sequence_index': sequence_index,
                    'available': False,
                    'message': '未找到结果文件 tic_front.csv',
                    'debug': {
                        'archive_id': archive_id,
                        'note': '按参数表解析 data_path + data_name(.D)/tic_front.csv 与前缀匹配回退均未命中'
                    }
                })
                return

            x_vals = []
            y_vals = []
            try:
                with open(path, 'r', newline='') as f:
                    reader = csv.reader(f)
                    # 跳过表头（若有）
                    first = next(reader, None)
                    # 如果首行两列均为数字，则视为数据行，否则跳过
                    if first is not None:
                        try:
                            _x0 = float(first[0])
                            _y0 = float(first[1])
                            x_vals.append(_x0)
                            y_vals.append(_y0)
                        except Exception:
                            pass
                    for row in reader:
                        if len(row) < 2:
                            continue
                        try:
                            x = float(row[0])
                            y = float(row[1])
                            x_vals.append(x)
                            y_vals.append(y)
                        except Exception:
                            continue
            except Exception as e:
                self.send_response({
                    'type': 'analysis_result',
                    'bottle_num': bottle_num,
                    'sequence_index': sequence_index,
                    'available': False,
                    'message': f'读取CSV失败: {str(e)}'
                })
                return

            # 限制数据量，简单抽样（如超过 8000 点则等距采样至 2000 点）
            n = len(x_vals)
            if n > 8000:
                target = 2000
                step = max(1, n // target)
                x_vals = x_vals[::step]
                y_vals = y_vals[::step]

            self.send_response({
                'type': 'analysis_result',
                'bottle_num': bottle_num,
                'sequence_index': sequence_index,
                'available': True,
                'series': {'x': x_vals, 'y': y_vals},
                'archive_id': archive_id,
                'path': path
            })
        except Exception as e:
            self.send_response({
                'type': 'error',
                'message': f'获取结果失败: {str(e)}'
            })

    def _ensure_archive_dir(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        archive_dir = os.path.join(base_dir, 'results_archive')
        os.makedirs(archive_dir, exist_ok=True)
        return archive_dir

    def archive_result(self, sequence_index):
        """复制当前结果文件到归档目录，返回 archive_id（时间戳+序列）。"""
        src = get_result_csv_path(int(sequence_index))
        if not src or not os.path.isfile(src):
            return None
        archive_dir = self._ensure_archive_dir()
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_id = f"{ts}_seq{sequence_index}"
        dst = os.path.join(archive_dir, f"{archive_id}.csv")
        shutil.copy2(src, dst)
        return archive_id

    def get_archive_file_path(self, archive_id):
        if not archive_id:
            return None
        archive_dir = self._ensure_archive_dir()
        candidate = os.path.join(archive_dir, f"{archive_id}.csv")
        return candidate if os.path.isfile(candidate) else None
    
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
