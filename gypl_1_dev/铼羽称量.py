import ctypes
import sys
import threading
import struct
from ctypes import *
from time import sleep

import serial
import time
import crc16_modbus

_instance = None  # 单例实例
thread_lock = threading.Lock()


class AdvancedSamplerSystem:
    def __new__(cls, com: str = None):
            """单例模式：全局唯一实例"""
            global _instance
            if _instance is None:
                _instance = super().__new__(cls)
                _instance.__initialized = False
            return _instance

    def __init__(self, com: str):
            if not self.__initialized and com:
                self.ser = serial.Serial()
                self.open_com(com, 115200)
                self.__initialized = True

    def open_com(self, com, band):
        try:
            if self.ser.isOpen():
                return True
            else:
                self.ser = serial.Serial(com, band)
                if self.ser.isOpen():
                    return True
                else:
                    return False
        except Exception as e:
            print("自动加样仪端口打开错误：", str(e))

    def _send_rec_data(self, send_data):
        try:
            with thread_lock:
                self.ser.reset_input_buffer()
                self.ser.write(send_data)
                rec_data_list = []
                j = 1
                while j < 10:
                    rec_len = self.ser.inWaiting()  # 缓冲区信息的长度
                    if rec_len > 0:
                        rec_raw_data = self.ser.read(rec_len)  # 读取字节数据
                        for item in rec_raw_data:
                            rec_data_list.append(item)
                        return rec_data_list
                    j += 1
                    time.sleep(0.1)
                if j >= 10:
                    return False
        except Exception as e:
            print(str(e))

    def float_to_hex(self, f):
        binary = struct.pack('!f', f)  # 将浮点数转换为 32 位二进制表示
        hex_str = binary.hex()  # 将二进制数据转换为十六进制字符串
        return hex_str

    def read_status(self):
        send_data_1 = [0x01, 0x03, 0x00, 0x00, 0x00, 0x01]
        send_data_2 = crc16_modbus.appendCRCfunc(send_data_1)
        rec_data = self._send_rec_data(send_data_2)
        # 添加返回值校验
        if not rec_data or not isinstance(rec_data, list):
            print("加粉仪连接失败")
            return 0

        time.sleep(0.5)
        return rec_data

    def read_realtime_weight(self) -> float:
        """
        读取实时质量（单位：mg）
        设备指令：01 03 00 01 00 02 [CRC]
        """
        if not self.ser or not self.ser.is_open:
            print("串口未连接！")
            self.open_com('COM4', 115200)  # 重新连接
        try:
            # 构造读取指令（寄存器地址00 01）
            cmd = bytes.fromhex("01 03 00 01 00 02")
            crc = self._calculate_crc(cmd).to_bytes(2, 'little')
            full_cmd = cmd + crc

            # 带重试的发送（最多3次）
            for _ in range(3):
                raw_data = self._send_rec_data(full_cmd)
                if raw_data:
                    break
                time.sleep(0.5)
            else:
                print("读取实时质量无响应")
                return 0.0

            # 协议头校验（设备地址+功能码）
            if len(raw_data) < 7 or raw_data[0] != 0x01 or raw_data[1] != 0x03:
                print(f"协议错误，响应数据: {bytes(raw_data).hex()}")
                return 0.0

            # CRC校验
            recv_crc = int.from_bytes(raw_data[-2:], 'little')
            calc_crc = self._calculate_crc(raw_data[:-2])
            if recv_crc != calc_crc:
                print(f"CRC校验失败: 接收{recv_crc:04X} ≠ 计算{calc_crc:04X}")
                return 0.0

            # 数据解析（大端序32位有符号整数）
            value = int.from_bytes(raw_data[3:7], 'big', signed=True)

            # 单位转换（假设设备返回μg，转换为mg）
            return round(value * 0.001, 3)  # μg→mg，保留3位小数

        except Exception as e:
            print(f"读取实时质量异常: {str(e)}")
            return 0.0

    def open_baffle(self):
        send_data_1 = [0x01, 0x06, 0x00, 0x24, 0x00, 0x01]
        send_data_2 = crc16_modbus.appendCRCfunc(send_data_1)
        rec_data = self._send_rec_data(send_data_2)
        print(rec_data)
        time.sleep(0.5)

    def close_baffle(self):
        send_data_1 = [0x01, 0x06, 0x00, 0x24, 0x00, 0x00]
        send_data_2 = crc16_modbus.appendCRCfunc(send_data_1)
        rec_data = self._send_rec_data(send_data_2)
        print(rec_data)
        time.sleep(0.5)

    def add_powder(self):
        """带状态轮询的加粉流程"""
        # 1. 发送加粉指令（功能码06写寄存器21H为0001H）
        cmd = [0x01, 0x06, 0x00, 0x21, 0x00, 0x01, 0x18, 0x00]
        rec_data = self._send_rec_data(cmd)
        while True:
            current_status = self.read_status()
            # 如果状态不符合预期，跳出循环
            if current_status == [1, 3, 2, 0, 1, 121, 132]:
                break
            time.sleep(0.1)
        return True

    def pause_powder(self):
        send_data_1 = [0x01, 0x06, 0x00, 0x21, 0x00, 0x02]
        send_data_2 = crc16_modbus.appendCRCfunc(send_data_1)
        rec_data = self._send_rec_data(send_data_2)
        print(rec_data)
        time.sleep(0.5)

    def Standard_Mode(self):
        send_data_1 = [0x01, 0x06, 0x00, 0x12, 0x00, 0x00]
        send_data_2 = crc16_modbus.appendCRCfunc(send_data_1)
        rec_data = self._send_rec_data(send_data_2)
        print(rec_data)
        time.sleep(0.5)

    def Precision_Mode(self):
        send_data_1 = [0x01, 0x06, 0x00, 0x12, 0x00, 0x01, 0x18, 0x00]
        send_data_2 = crc16_modbus.appendCRCfunc(send_data_1)
        rec_data = self._send_rec_data(send_data_2)
        print(rec_data)
        time.sleep(0.5)

    def set_bottle_height(self, height_type: str):
        """
        设置瓶高（根据预定义类型选择）

        Args:
            height_type: 瓶高类型，可选：
                - "5ml"    -> 发送 00 05
                - "20ml"   -> 发送 00 20
                - "15ml" -> 发送 00 0A
        """
        height_map = {
            "5ml": 0x0005,
            "20ml": 0x0020,
            "15ml": 0x000A
        }

        if height_type.lower() not in height_map:
            raise ValueError(f"无效的瓶高类型，可选: {list(height_map.keys())}")

        height_value = height_map[height_type.lower()]
        send_data_1 = [0x01, 0x06, 0x00, 0x13, (height_value >> 8) & 0xFF, height_value & 0xFF]
        send_data_2 = crc16_modbus.appendCRCfunc(send_data_1)
        rec_data = self._send_rec_data(send_data_2)
        print(f"设置瓶高: {height_type} -> 响应: {rec_data}")
        time.sleep(0.5)
        return rec_data is not False

    def set_weight(self, weight_mg: float) -> bool:
        """设置目标质量并返回是否成功"""
        value = int(round(weight_mg * 1000))
        high_byte = (value >> 8) & 0xFF
        low_byte = value & 0xFF

        send_data_1 = [
            0x01, 0x10, 0x00, 0x10,
            0x00, 0x02, 0x04,
            0x00, 0x00, high_byte, low_byte
        ]
        send_data_2 = crc16_modbus.appendCRCfunc(send_data_1)
        rec_data = self._send_rec_data(send_data_2)

        # 成功响应格式: [设备地址, 功能码, 起始地址高, 起始地址低, 寄存器数高, 寄存器数低]
        success = rec_data and len(rec_data) >= 6 and rec_data[0] == 0x01 and rec_data[1] == 0x10
        print(f"设置重量 {weight_mg}mg -> {'成功' if success else '失败'}")
        time.sleep(0.5)
        return success  # 明确返回布尔值

    def Reset_the_balance(self):
        send_data_1 = [0x01, 0x06, 0x00, 0x22, 0xAA, 0xAA]
        send_data_2 = crc16_modbus.appendCRCfunc(send_data_1)
        rec_data = self._send_rec_data(send_data_2)
        print(rec_data)
        time.sleep(0.5)

    def Reset_the_sampler(self):
        send_data_1 = [0x01, 0x06, 0x00, 0x20, 0xAA, 0xAA]
        send_data_2 = crc16_modbus.appendCRCfunc(send_data_1)
        rec_data = self._send_rec_data(send_data_2)
        print(rec_data)
        time.sleep(0.5)

    def read_finally_weight(self) -> float:
        try:
            cmd = bytes.fromhex("01 03 00 03 00 02")
            crc = self._calculate_crc(cmd).to_bytes(2, 'little')
            full_cmd = cmd + crc

            # 带重试的发送
            for _ in range(3):
                raw_data = self._send_rec_data(full_cmd)
                if raw_data: break
                time.sleep(0.5)
            else:
                return 0

            # 协议头校验
            if len(raw_data) < 7 or raw_data[0] != 0x01 or raw_data[1] != 0x03:
                print(f"协议错误: {raw_data.hex()}")
                return 0

            # CRC校验
            recv_crc = int.from_bytes(raw_data[-2:], 'little')
            calc_crc = self._calculate_crc(raw_data[:-2])
            if recv_crc != calc_crc:
                print(f"CRC失败: {recv_crc:04X} vs {calc_crc:04X}")
                return 0

            # 数据解析（大端序32位有符号）
            value = int.from_bytes(raw_data[3:7], 'big', signed=True)
            return round(value * 0.001, 3)  # μg→mg

        except Exception as e:
            print(f"质量读取异常: {str(e)}")
            return 0

    def _calculate_crc(self, data: bytes):
        """Modbus CRC16计算实现"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc

    def full_powder_process(self, target_mg: float, mode: str, bottle_height: str) -> dict:
        result = {
            "success": False,
            "target_mg": float(target_mg),  # 确保是float类型
            "actual_mg": 0.0,  # 默认值
            "deviation": 0.0,
            "deviation_percent": 0.0
        }

        try:
            # === 1. 复位天平 ===
            print("\n[1/6] 复位天平...")
            self.Reset_the_balance()
            time.sleep(1)  # 等待复位完成

            # === 2. 选择加粉模式 ===
            print(f"[2/6] 设置模式: {mode}...")
            if mode.lower() == "precision":
                self.Precision_Mode()
            else:
                self.Standard_Mode()
            time.sleep(0.5)

            # === 3. 设置瓶高 ===
            print(f"[3/6] 设置瓶高: {bottle_height}...")
            if not self.set_bottle_height(bottle_height):  # 调用专用方法
                result["error"] = "设置瓶高失败"
                return result

            # === 4. 设置目标质量 ===
            print(f"[4/6] 设置目标质量: {target_mg}mg...")
            self.set_weight(target_mg)  # 不再检查返回值（或根据需求保留检查）
            time.sleep(1)  # 增加延时确保设备处理完成

            # === 5. 开始加粉 ===
            print("[5/6] 开始加粉...")
            add = self.add_powder()
            while add:
                # === 6. 读取实际质量 ===
                actual_mg = self.read_finally_weight()
                if actual_mg is None:
                    result["error"] = "读取实际质量失败"
                    return result

                # === 7. 复位仪器 ===
                print("[6/6] 复位仪器...")
                self.Reset_the_sampler()
                time.sleep(35)

                # === 计算偏差 ===
                deviation = actual_mg - target_mg
                deviation_percent = (deviation / target_mg) * 100 if target_mg != 0 else 0

                result.update({
                    "success": True,
                    "actual_mg": float(actual_mg),
                    "deviation": float(deviation),
                    "deviation_percent": deviation_percent
                })
                break
        except Exception as e:
            result["error"] = f"流程异常: {str(e)}"

        error = result["actual_mg"] - result["target_mg"]
        error_formatted = f"{error:+.3f}mg"  # 关键修改点：强制显示符号
        print(f"""
                      ✅ 加粉完成！
                      - 预设质量: {result['target_mg']}mg
                      - 实际质量: {result['actual_mg']:.3f}mg
                      - 误差: {error_formatted}
                      - 相对偏差: {result['deviation_percent']:+.2f}%
                      """)
        return result

    @classmethod
    def get_instance(cls):
        """获取全局实例（避免重复初始化）"""
        global _instance
        if _instance is None:
            raise RuntimeError("称重仪器未初始化！请先调用 AdvancedSamplerSystem('COMx')")
        return _instance

    def is_connected(self):
        """
        通过调用 read_status() 检查连接。
        如果 read_status() 返回 0，则视为连接失败。
        """
        if not self.ser or not self.ser.isOpen():
            return False
        try:
            # 调用 read_status() 并检查其返回值
            status_response = self.read_status()
            # 如果返回值为 0，则连接失败
            if status_response == 0:
                return False
            # 否则，视为连接成功
            return True
        except Exception as e:
            print(f"天平连接检查时发生异常: {e}")
            return False


if __name__ == '__main__':
    sampler = AdvancedSamplerSystem('com21')




