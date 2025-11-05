import websocket
import json
import threading
import time
import sys
import os
import csv
from datetime import datetime

# 追加模块路径，导入联合流程（从项目根目录定位 模块开发运行代码/HPLC液相模块）
_here = os.path.abspath(__file__)
_hplc_worker_dir = os.path.dirname(_here)
_station_workers_dir = os.path.dirname(_hplc_worker_dir)
_project_root = os.path.dirname(_station_workers_dir)
_hplc_module_dir = os.path.join(_project_root, '模块开发运行代码', 'HPLC液相模块')
if _hplc_module_dir not in sys.path:
    sys.path.append(_hplc_module_dir)

try:
    from HPLC机械臂与仪器联合流程 import (
        run_hplc_robot_and_instrument_flow,
        HPLC_module,
        InstrumentHandler,
    )
except ImportError:
    run_hplc_robot_and_instrument_flow = None
    HPLC_module = None
    InstrumentHandler = None


class HplcWorker:
    def __init__(self, server_url=None):
        self.server_url = (
            server_url
            or os.environ.get("HPLC_SERVER_URL")
            or "ws://127.0.0.1:8000/ws/hplc/"
        )
        self.ws = None
        self.is_connected = False
        self.current_status = "离线"

        # 运行参数（可根据需要改为从环境变量读取）
        self.base_url = os.environ.get('HPLC_BASE_URL', "http://192.168.58.131:9100")
        self.username = os.environ.get('HPLC_USERNAME', 'admin')
        self.password = os.environ.get('HPLC_PASSWORD', 'agilent')
        self.cdsId = int(os.environ.get('HPLC_CDS_ID', '17'))
        self.pos = os.environ.get('HPLC_POS', 'D1B-A9')
        self.workPlanNo = os.environ.get('HPLC_WORKPLAN', '1721207124')
        self.isActive = int(os.environ.get('HPLC_IS_ACTIVE', '1'))
        self.labName = os.environ.get('HPLC_LAB', 'Lab1')
        self.batch_id = os.environ.get('HPLC_BATCH_ID', '20240619135729')
        self.injectorId = os.environ.get('HPLC_INJECTOR_ID', '18df4f9d-01c9-4fed-bca7-f12db5febac4')
        self.analysis_job_parameters = None
        self.remote_folder_path = os.environ.get('HPLC_REMOTE_DATA', r'\\192.168.58.132\Data')
        self.local_save_dir = os.environ.get('HPLC_LOCAL_DATA', os.path.join(os.path.dirname(__file__), 'Data'))

        # LIMS与样本数据模板（与联合流程一致）
        self.lims_data = {
            "limsSamples": [
                {
                    "barCode": "20240619135729-1",
                    "type": "Sample",
                    "name": "石脑油1",
                    "status": "New",
                    "batchId": "20240619135729",
                    "vialList": [
                        {
                            "type": "Vial",
                            "barCode": "",
                            "labName": "Lab1",
                            "analysisProject": "testLC",
                            "status": "New",
                        }
                    ],
                }
            ]
        }
        self.samples = [
            {
                "barCode": "20240619135729-1",
                "type": "Sample",
                "name": "石脑油1",
                "status": "New",
                "batchId": "20240619135729",
                "vialList": [
                    {
                        "type": "Vial",
                        "barCode": "",
                        "labName": "Lab1",
                        "analysisProject": "testLC",
                        "status": "New",
                    }
                ],
            }
        ]
        self.placed_Vials = [
            {
                "positionIndex": -1,
                "positionName": self.pos,
                "vialBarcode": "",
                "placeOnInstrumentDateTime": "",
            }
        ]

    # --- WebSocket handlers ---
    def on_open(self, ws):
        self.is_connected = True
        self.current_status = "就绪"
        self.send({
            "type": "worker_connected",
            "message": "HPLC Worker 已连接",
            "status": self.current_status,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

    def on_close(self, ws, code, msg):
        self.is_connected = False
        print("HPLC Worker 连接已关闭")

    def on_error(self, ws, error):
        print(f"WebSocket 错误: {error}")
        self.is_connected = False

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
        except Exception:
            return

        if data.get('sender') == 'worker':
            return

        command = data.get('message', '')

        if command == 'get_status':
            self.handle_get_status()
        elif command == 'get_arm_status':
            self.handle_get_arm_status()
        elif command == 'get_instrument_info':
            self.handle_get_instrument_info()
        elif command.startswith('start_analysis_'):
            try:
                bottle_num = int(command.split('_')[-1])
            except Exception:
                self.send({"type": "error", "message": f"指令格式错误: {command}"})
                return
            self.handle_start_analysis(bottle_num)
        elif command.startswith('get_result_'):
            try:
                bottle_num = int(command.split('_')[-1])
            except Exception:
                bottle_num = None
            self.handle_get_result(bottle_num)
        elif command == 'force_stop':
            # 预留：如需强停逻辑
            self.send({"type": "info", "message": "已收到停止指令"})
        else:
            self.send({"type": "error", "message": f"未知指令: {command}"})

    # --- Commands ---
    def handle_get_status(self):
        status = {
            "type": "status_update",
            "status": self.current_status,
            "run_status": "Unknown",
            "run_mode": "Unknown",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.send(status)

    def handle_get_arm_status(self):
        try:
            if HPLC_module:
                arm = HPLC_module()
                b_val = arm.get_b_status()
                payload = {"type": "arm_status", "status": "正常", "b_value": b_val}
            else:
                payload = {"type": "arm_status", "status": "未加载模块"}
        except Exception as e:
            payload = {"type": "arm_status", "status": "连接失败", "error": str(e)}
        self.send(payload)

    def handle_get_instrument_info(self):
        try:
            if InstrumentHandler:
                ih = InstrumentHandler(self.base_url)
                ih.login(self.username, self.password)
                info = ih.get_system_info()
                payload = {"type": "instrument_info", "info": info}
            else:
                payload = {"type": "instrument_info", "error": "未加载模块"}
        except Exception as e:
            payload = {"type": "instrument_info", "error": str(e)}
        self.send(payload)

    def handle_start_analysis(self, bottle_num):
        def worker():
            try:
                self.current_status = "分析中"
                self.send({"type": "analysis_started", "bottle_num": bottle_num})
                run_hplc_robot_and_instrument_flow(
                    self.base_url,
                    self.username,
                    self.password,
                    self.cdsId,
                    self.injectorId,
                    self.pos,
                    self.workPlanNo,
                    self.isActive,
                    self.labName,
                    self.batch_id,
                    self.lims_data,
                    self.samples,
                    self.placed_Vials,
                    self.analysis_job_parameters,
                    self.remote_folder_path,
                    self.local_save_dir,
                    bottle_num,
                )
                self.current_status = "就绪"
                self.send({"type": "analysis_complete", "bottle_num": bottle_num})
            except Exception as e:
                self.current_status = "错误"
                self.send({"type": "analysis_error", "bottle_num": bottle_num, "message": str(e)})

        if not run_hplc_robot_and_instrument_flow:
            self.send({"type": "analysis_error", "bottle_num": bottle_num, "message": "联合流程未加载"})
            return
        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _find_latest_csv(self):
        directory = self.local_save_dir
        if not os.path.isdir(directory):
            return None
        candidates = [
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if f.lower().endswith('.csv') and os.path.isfile(os.path.join(directory, f))
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return candidates[0]

    def handle_get_result(self, bottle_num=None):
        path = self._find_latest_csv()
        if not path:
            self.send({
                'type': 'analysis_result',
                'available': False,
                'message': '未找到CSV结果文件'
            })
            return
        x_vals, y_vals = [], []
        try:
            with open(path, 'r', newline='') as f:
                reader = csv.reader(f)
                first = next(reader, None)
                if first is not None:
                    try:
                        x_vals.append(float(first[0])); y_vals.append(float(first[1]))
                    except Exception:
                        pass
                for row in reader:
                    if len(row) < 2:
                        continue
                    try:
                        x_vals.append(float(row[0]))
                        y_vals.append(float(row[1]))
                    except Exception:
                        continue
        except Exception as e:
            self.send({'type': 'analysis_result', 'available': False, 'message': f'读取CSV失败: {str(e)}'})
            return

        n = len(x_vals)
        if n > 8000:
            target = 2000
            step = max(1, n // target)
            x_vals = x_vals[::step]
            y_vals = y_vals[::step]

        self.send({
            'type': 'analysis_result',
            'available': True,
            'series': {'x': x_vals, 'y': y_vals},
            'path': path
        })

    # --- util ---
    def send(self, message: dict):
        if self.ws and self.is_connected:
            try:
                self.ws.send(json.dumps({"message": message, "sender": "worker"}))
            except Exception as e:
                print(f"发送消息失败: {e}")

    def start(self):
        self.ws = websocket.WebSocketApp(
            self.server_url,
            on_open=self.on_open,
            on_close=self.on_close,
            on_error=self.on_error,
            on_message=self.on_message,
        )
        self.ws.run_forever()


if __name__ == '__main__':
    url = None
    try:
        if "-s" in sys.argv:
            i = sys.argv.index("-s"); url = sys.argv[i+1]
        elif "--server-url" in sys.argv:
            i = sys.argv.index("--server-url"); url = sys.argv[i+1]
    except Exception:
        url = None

    worker = HplcWorker(server_url=url)
    try:
        worker.start()
    except KeyboardInterrupt:
        print("\n正在关闭 HPLC Worker...")

