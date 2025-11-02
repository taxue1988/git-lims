import sys
import time
import json
import threading
import websocket
from 艾利特机械臂 import EC66
from 铼羽称量 import AdvancedSamplerSystem

# --- WebSocket 服务器配置 ---
# 请将这里的 IP 地址替换为你服务器的真实局域网IP地址
SERVER_IP = "192.168.58.7"
WEBSOCKET_URL = f"ws://{SERVER_IP}:8000/ws/test/gypl_station_1/"  # 定义此设备站的唯一ID


class gypl:
    def __init__(self, com_port='COM21', arm_ip='192.168.58.210'):
        print("正在初始化设备...")
        try:
            self.arm = EC66(arm_ip)
        except Exception as e:
            print(f"初始化机械臂失败: {e}")
            self.arm = None

        try:
            self.sampler = AdvancedSamplerSystem(com_port)
            self.tp = AdvancedSamplerSystem.get_instance()
        except Exception as e:
            print(f"初始化天平/加粉仪失败: {e}")
            self.sampler = None
            self.tp = None

        self.current_tip = None

        # 用于存储历史记录的列表
        self.solids_history = []         # 存储每次加固的实际结果
        self.liquids_history = []        # 存储每次加液的实际结果
        self.solids_parameters_history = [] # 存储传入的固参
        self.liquids_parameters_history = [] # 存储传入的液参

    def _map_to_grid(self, logical_pos: int, cols: int) -> int:
        """将一维逻辑位置转换为二维网格物理位置。"""
        if logical_pos <= 0:
            raise ValueError("逻辑位置必须是正整数")
        row = (logical_pos - 1) // cols + 1
        col = (logical_pos - 1) % cols + 1
        return row * 10 + col

    def _get_solid_pos(self, logical_pos: int) -> int:
        """转换固体逻辑位置到物理位置（6列）。"""
        return self._map_to_grid(logical_pos, 6)

    def _get_liquid_pos(self, logical_pos: int) -> int:
        """转换液体逻辑位置到物理位置（2列）。"""
        return self._map_to_grid(logical_pos, 2)

    def _get_tube_pos(self, logical_pos: int) -> int:
        """转换试管逻辑位置到物理位置（6列）。"""
        return self._map_to_grid(logical_pos, 6)

    def _get_tip_pos(self, logical_pos: int) -> int:
        """转换枪头逻辑位置到物理位置（8列）。"""
        return self._map_to_grid(logical_pos, 8)

    def get_device_status(self):
        """获取所有设备的当前连接状态。"""
        # 检查机械臂状态，不进行自动重连
        arm_status = self.arm.is_connected() if self.arm else False

        # 检查天平/加粉仪状态，不进行自动重连
        balance_status = self.sampler.is_connected() if self.sampler else False

        # 如果连接断开，is_connected内部已经打印了详细原因
        if not arm_status:
            print("机械臂连接检查未通过（详情见上一条日志）。")
        if not balance_status:
            print("天平/加粉仪连接检查未通过。")

        return {
            'arm': arm_status,
            'balance': balance_status,
            'powder_dispenser': balance_status  # Use the key expected by the frontend
        }

    def open_15ml(self, bottle_15ml_pos):
        physical_pos = self._get_tube_pos(bottle_15ml_pos)
        self.arm.set_B_value(27, physical_pos)
        self.arm.run_jbi('guticl_ning_shiguan')

    def open_150ml(self, bottle_150ml_pos):
        physical_pos = self._get_liquid_pos(bottle_150ml_pos)
        self.arm.set_B_value(28, physical_pos)
        self.arm.run_jbi('guticl_ning_shaobei')

    def pick_tip(self, qt_pos):
        physical_pos = self._get_tip_pos(qt_pos)
        self.arm.set_B_value(26, physical_pos)
        self.arm.run_jbi('guticl_pick_tip')

    def remove_tip(self):
        self.arm.run_jbi('guticl_remove_tip')

    def add_liquid(self, bottle_150ml_pos, volume, qt_pos):
        print(f"从烧杯 {bottle_150ml_pos} 吸取 {volume} mL 液体")
        self.open_150ml(bottle_150ml_pos)
        self.pick_tip(qt_pos)
        self.arm.set_D_value(11, volume)
        self.arm.run_jbi('guticl_suck_shaobei_to_tp')
        weight1 = self.tp.read_realtime_weight()
        time.sleep(2)
        print(f"当前实时重量: {weight1} mg")
        self.remove_tip()
        self.shaobei_back(bottle_150ml_pos)

    def add_solid(self, FT_pos, target_mg, mode, bottle_height):
        print(f"从粉桶 {FT_pos} 加入 {target_mg} mg 固体")
        self.take_FT(FT_pos)
        self.sampler.full_powder_process(target_mg, mode, bottle_height)
        time.sleep(27)
        self.back_FT(FT_pos)

    def take_FT(self, FT_pos):
        physical_pos = self._get_solid_pos(FT_pos)
        self.arm.set_B_value(24, physical_pos)
        self.arm.run_jbi('guticl_fentong_take')

    def back_FT(self, FT_pos):
        physical_pos = self._get_solid_pos(FT_pos)
        self.arm.set_B_value(24, physical_pos)
        self.arm.run_jbi('guticl_fentong_back')

    def shiguan_back(self, bottle_15ml_pos):
        physical_pos = self._get_tube_pos(bottle_15ml_pos)
        self.arm.set_B_value(27, physical_pos)
        self.arm.run_jbi('shiguan_back')

    def shaobei_back(self, bottle_150_pos):
        physical_pos = self._get_liquid_pos(bottle_150_pos)
        self.arm.set_B_value(28, physical_pos)
        self.arm.run_jbi('shaobei_back')

    def _add_solids(self, solids_list: list):
        """处理加固过程"""
        print("--- 开始加固流程 ---")
        real_time_weights = []  # 用于存储实时重量数据
        
        for ft_pos, target_mg in enumerate(solids_list, 1):
            if target_mg > 0:
                # 默认使用 "precision" 模式和 "15ml" 瓶高，可以根据需要修改或作为参数传入
                mode = "precision"
                height = "15ml"

                print(f"\n=== 开始处理粉桶 {ft_pos} ===")
                print(f"- 机械臂正在取粉桶 {ft_pos}...")
                self.take_FT(ft_pos)

                print(f"- 开始向试管中加入 {target_mg}mg 固体...")
                result = self.tp.full_powder_process(
                    target_mg=target_mg,
                    mode=mode,
                    bottle_height=height
                )

                # 获取实时重量
                real_time_weight = self.tp.read_realtime_weight()
                real_time_weights.append({
                    "position": ft_pos,
                    "target": target_mg,
                    "actual": result["actual_mg"],
                    "real_time": real_time_weight
                })

                error = result["actual_mg"] - result["target_mg"]
                print(
                    f"  ✅ 加粉完成！ 预设: {result['target_mg']}mg, 实际: {result['actual_mg']:.3f}mg, 误差: {error:+.3f}mg")

                print("- 正在打开挡板并归位粉桶...")
                self.tp.open_baffle()
                time.sleep(2)
                self.back_FT(ft_pos)
        print("--- 加固流程结束 ---")
        return real_time_weights

    def _add_liquids(self, liquids_list: list, tip_pos_list: list) -> list:
        """
        处理加液过程，并返回更新后的枪头位置列表。

        Args:
            liquids_list (list): 液体体积列表。
            tip_pos_list (list): 枪头可用状态列表 (0: 不可用, 1: 可用)。

        Returns:
            list: 更新后的枪头可用状态列表。
        """
        print("--- 开始加液流程 ---")
        # 创建一个副本以在循环中安全地修改
        updated_tip_pos_list = list(tip_pos_list)

        for liquid_pos, volume in enumerate(liquids_list, 1):
            if volume <= 0:
                continue

            # 查找第一个可用的枪头
            try:
                # list.index() 会找到第一个值为1的元素的索引
                tip_index = updated_tip_pos_list.index(1)
                # 逻辑位置是索引+1
                current_tip_pos = tip_index + 1
            except ValueError:
                # 如果找不到值为1的元素，则没有可用的枪头
                print("错误：没有可用的枪头了！")
                raise Exception("加液失败：没有可用的枪头。")

            print(f"\n=== 开始处理烧杯 {liquid_pos}，使用枪头 {current_tip_pos} ===")
            self.add_liquid(liquid_pos, volume, current_tip_pos)

            # 将用过的枪头位置标记为0（不可用）
            updated_tip_pos_list[tip_index] = 0

        print("--- 加液流程结束 ---")
        return updated_tip_pos_list

    def gtcl_all(self, solids_list: list, liquids_list: list, bottle_15ml_pos: int, start_tip_pos: list):
        """
        以列表参数的形式执行完整的加料流程。

        Args:
            solids_list (list): 浮点数列表。索引对应粉桶位置，值为要添加的固体质量(mg)。
            liquids_list (list): 浮点数列表。索引对应烧杯位置，值为要添加的液体体积(mL)。
            bottle_15ml_pos (int): 本次实验中使用的15ml试管的位置。
            start_tip_pos (list): 枪头可用状态列表 (0: 不可用, 1: 可用)。长度为96。
        """
        try:
            # 0. 存储参数
            self.solids_parameters_history.append(list(solids_list))
            self.liquids_parameters_history.append(list(liquids_list))

            # 1. 打开天平挡板并移动试管到天平
            print("--- 正在打开天平挡板 ---")
            self.sampler.open_baffle()
            print(f"--- 正在移动试管 {bottle_15ml_pos} 到天平 ---")
            self.open_15ml(bottle_15ml_pos)

            # 2. 加固
            solid_results = self._add_solids(solids_list)
            self.solids_history.append(solid_results)

            # 创建更新后的 solids_list
            updated_solids_list = list(solids_list)
            for result in solid_results:
                if 0 <= result['position'] - 1 < len(updated_solids_list):
                    updated_solids_list[result['position'] - 1] = result['actual']

            # 3. 加液
            updated_tip_pos_list = self._add_liquids(liquids_list, start_tip_pos)
            # 假设请求值即为实际值并存入历史记录
            self.liquids_history.append(list(liquids_list))
            print(f"--- 加液完成 ---")

            # 4. 最终归位试管
            print(f"\n--- 实验完成，正在归位试管 {bottle_15ml_pos} ---")
            self.shiguan_back(bottle_15ml_pos)
            print("--- 流程结束 ---")

            # 5. 构建并返回结果
            result_dict = {
                "solids_list": updated_solids_list,
                "liquids_list": liquids_list,  # 当前假设液体量不变
                "bottle_15ml_pos": bottle_15ml_pos,
                "start_tip_pos": updated_tip_pos_list # 返回更新后的枪头状态列表
            }
            return result_dict

        except Exception as e:
            print(f"实验失败：{str(e)}")
            raise
