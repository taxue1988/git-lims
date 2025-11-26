import os
import shutil
import time
from datetime import datetime

import requests
from 艾利特机械臂 import EC66


class HPLC_module:
    def __init__(self):
        self.gc_arm = EC66('192.168.58.140')

    def get_b_status(self):
        b = self.gc_arm.get_B_value(0)
        return b

    def kb_to_hplc(self, bottle_num):
        self.gc_arm.set_B_value(0, bottle_num)
        self.gc_arm.run_jbi('ssx_take_bottle')
        self.gc_arm.run_jbi('ssx_open_door')

    def hplc_drop(self, bottle_num):
        self.gc_arm.set_B_value(0, bottle_num)
        self.gc_arm.run_jbi('ssx_lose_bottle')


class InstrumentHandler:
    def __init__(self, base_url):
        self.base_url = base_url
        self.auth_token = None

    def login(self, username, password):
        url = f"{self.base_url}/api/v1/Authentication"
        params = {
            'userName': username,
            'userPassword': password
        }
        response = requests.put(url, params=params)
        response_data = response.json()
        if response.status_code == 200 and response_data.get('statusCode') == 0:
            self.auth_token = response_data['data']['authenticationToken']
            print(f"登录成功。认证令牌：{self.auth_token}")
        else:
            raise RuntimeError(f"登录失败：{response_data}")

    def _auth_headers(self):
        return {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/json'
        }

    def get_system_info(self):
        url = f"{self.base_url}/api/v1/SystemInfo"
        response = requests.get(url, headers={'Authorization': f'Bearer {self.auth_token}'})
        response_data = response.json()
        if response.status_code == 200 and response_data.get('statusCode') == 0:
            print("系统信息：")
            print(response_data['data'])
            return response_data['data']
        raise RuntimeError(f"获取系统信息失败：{response_data}")

    def get_instrument_info_by_cdsid(self, cdsId):
        url = f"{self.base_url}/api/v1/Instrument/auto/cdsid"
        params = {'cdsId': cdsId}
        response = requests.get(url, params=params, headers=self._auth_headers())
        response_data = response.json()
        if response.status_code == 200 and response_data.get('statusCode') == 0:
            print(f"CDS ID {cdsId} 的仪器信息：")
            print(response_data['data'])
            return response_data['data']
        raise RuntimeError(f"获取仪器信息失败：{response_data}")

    def clear_instrument_vials_complete(self, cdsId, injectorId, clearPositiones):
        url = f"{self.base_url}/api/v1/Events/ClearInstrumentVialsComplete?cdsId={cdsId}&injectorId={injectorId}"
        response = requests.put(url, json=clearPositiones, headers=self._auth_headers())
        response_data = response.json()
        if response.status_code == 200 and response_data.get('statusCode') == 0:
            print(f"清理测试瓶完成事件成功：{response_data['message']}")
        else:
            raise RuntimeError(f"清理测试瓶完成事件失败：{response_data}")

    def ready_to_place_vial_to_instrument(self, cdsId, injectorId):
        url = f"{self.base_url}/api/v1/Events/ReadyToPlaceVialToInstrument?cdsId={cdsId}&injectorId={injectorId}"
        response = requests.put(url, headers=self._auth_headers())
        response_data = response.json()
        if response.status_code == 200 and response_data.get('statusCode') == 0:
            positions = response_data['data']
            print(f"仪器已准备好接收样品瓶。可用位置：{positions}")
            return positions
        raise RuntimeError(f"无法检查放样准备状态：{response_data}")

    def batch_set_sample_data(self, lims_data):
        url = f"{self.base_url}/api/v1/Sample/batch"
        response = requests.post(url, json=lims_data, headers=self._auth_headers())
        response_data = response.json()
        if response.status_code == 200 and response_data.get('statusCode') == 0:
            print(f"按批次设置样品数据成功：{response_data['message']}")
        else:
            raise RuntimeError(f"按批次设置样品数据失败：{response_data}")

    def get_sample_data_by_batch_id(self, batch_id):
        url = f"{self.base_url}/api/v1/Sample/batchId"
        params = {'batchId': batch_id}
        response = requests.get(url, params=params, headers=self._auth_headers())
        response_data = response.json()
        if response.status_code == 200 and response_data.get('statusCode') == 0:
            print(f"批次号 {batch_id} 的样品数据：")
            print(response_data['data'])
            return response_data['data']
        raise RuntimeError(f"获取样品数据失败：{response_data}")

    def get_active_workplans(self, isActive, labName):
        url = f"{self.base_url}/api/v1/Workplan/active"
        params = {'isActive': isActive, 'labName': labName}
        response = requests.get(url, params=params, headers=self._auth_headers())
        response_data = response.json()
        if response.status_code == 200 and response_data.get('statusCode') == 0:
            print(f"实验室 {labName} 的活跃计划：")
            print(response_data['data'])
            return response_data['data']
        raise RuntimeError(f"获取活跃计划失败：{response_data}")

    def remove_workplan_item(self, item_id):
        url = f"{self.base_url}/api/v1/Workplan?id={item_id}"
        response = requests.delete(url, headers=self._auth_headers())
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('statusCode') == 0:
                print(f"成功移除工作计划项 ID {item_id}")
                return
        raise RuntimeError("移除工作计划项失败")

    def generate_workplan_event(self, workPlanNo, labName, samples):
        url = f"{self.base_url}/api/v1/Events/GenerateWorkplan?workPlanNo={workPlanNo}&labName={labName}"
        response = requests.put(url, json=samples, headers=self._auth_headers())
        response_data = response.json()
        if response.status_code == 200 and response_data.get('statusCode') == 0:
            print(f"生成工作计划事件成功：{response_data['message']}")
        else:
            raise RuntimeError(f"生成工作计划事件失败：{response_data}")

    def apply_instrument_position_to_place_vial(self, cdsId, injectorId, pos):
        url = f"{self.base_url}/api/v1/Events/ApplyInstrumentPositionToPlaceVial?cdsId={cdsId}&injectorId={injectorId}&pos={pos}"
        response = requests.put(url, headers=self._auth_headers())
        response_data = response.json()
        if response.status_code == 200 and response_data.get('statusCode') == 0:
            print("申请放样到仪器特定位置事件成功发送。")
            return response_data['data']
        raise RuntimeError(f"申请放样事件失败：{response_data}")

    def place_vials_to_instrument_complete(self, cdsId, injectorId, placed_Vials):
        url = f"{self.base_url}/api/v1/Events/PlaceVialsToInstrumentComplete?cdsId={cdsId}&injectorId={injectorId}"
        response = requests.put(url, json=placed_Vials, headers=self._auth_headers())
        response_data = response.json()
        if response.status_code == 200 and response_data.get('statusCode') == 0:
            print(f"放置测试瓶到仪器完成事件成功：{response_data['message']}")
        else:
            raise RuntimeError(f"放置测试瓶完成事件失败：{response_data}")

    def start_analysis(self, cdsId, analysis_job_parameters):
        url = f"{self.base_url}/api/v1/Events/StartAnalysis?cdsId={cdsId}"
        response = requests.put(url, json=analysis_job_parameters, headers=self._auth_headers())
        response_data = response.json()
        if response.status_code == 200 and response_data.get('statusCode') == 0:
            print(f"启动分析事件成功：{response_data['message']}")
        else:
            raise RuntimeError(f"启动分析事件失败：{response_data}")

    def check_instrument_idle(self, cdsId):
        url = f"{self.base_url}/api/v1/Events/CheckInstrumentIdle?cdsId={cdsId}"
        response = requests.put(url, headers=self._auth_headers())
        response_data = response.json()
        if response.status_code == 200 and response_data.get('statusCode') == 0:
            print("仪器处于已处于Idle状态：0")
            return True
        print(f"仪器还未处于Idle状态：{response_data.get('errorMessage')}")
        return False

    def ready_to_clear_instrument(self, cdsId, injectorId):
        url = f"{self.base_url}/api/v1/Events/ReadyToClearInstrument"
        params = {'cdsId': cdsId, 'injectorId': injectorId}
        response = requests.put(url, params=params, headers=self._auth_headers())
        response_data = response.json()
        if response.status_code == 200 and response_data.get('statusCode') == 0:
            print("可以进行清理操作。进样器存储物流信息如下：")
            print(response_data['data'])
            return response_data['data']
        raise RuntimeError(f"清理仪器事件请求失败：{response_data}")

    def apply_clear_instrument_position(self, cdsId, injectorId, pos):
        url = f"{self.base_url}/api/v1/Events/ApplyClearInstrumentPosition?cdsId={cdsId}&injectorId={injectorId}&pos={pos}"
        response = requests.put(url, headers=self._auth_headers())
        response_data = response.json()
        if response.status_code == 200 and response_data.get('statusCode') == 0:
            print("申请清理仪器特定盘（塔）位事件成功发送。")
            return response_data['data']
        raise RuntimeError(f"申请清理盘位失败：{response_data}")

    @staticmethod
    def get_remote_folder_list(folder_path, substring):
        folder_list = []
        for root, dirs, files in os.walk(folder_path):
            for directory in dirs:
                if substring.lower() in directory.lower():
                    folder_list.append(directory)
            for file in files:
                if file.lower().endswith('.csv') and substring.lower() in file.lower():
                    folder_list.append(file)
        return folder_list

    @staticmethod
    def retrieve_and_save_file(remote_path, local_path):
        shutil.copy(remote_path, local_path)
        print("文件成功到达本地Data目录下")


def run_hplc_robot_and_instrument_flow(
    base_url,
    username,
    password,
    cdsId,
    injectorId,
    pos,
    workPlanNo,
    isActive,
    labName,
    batch_id,
    lims_data,
    samples,
    placed_Vials,
    analysis_job_parameters,
    remote_folder_path,
    local_save_dir,
    bottle_num
):
    # 机械臂：从仓位取瓶，打开门
    arm = HPLC_module()
    arm.kb_to_hplc(bottle_num)

    # 仪器：登录
    ins = InstrumentHandler(base_url)
    ins.login(username, password)

    # 仪器：初始检查与样品数据
    ins.get_system_info()
    time.sleep(2)
    ins.batch_set_sample_data(lims_data)
    time.sleep(2)
    ins.get_sample_data_by_batch_id(batch_id)
    time.sleep(2)
    ins.get_instrument_info_by_cdsid(cdsId)
    time.sleep(2)
    ins.check_instrument_idle(cdsId)
    time.sleep(2)

    # 仪器：生成计划与放样到盘位
    ins.generate_workplan_event(workPlanNo, labName, samples)
    time.sleep(2)
    ins.get_active_workplans(isActive, labName)
    time.sleep(2)
    ins.ready_to_place_vial_to_instrument(cdsId, injectorId)
    time.sleep(2)
    ins.apply_instrument_position_to_place_vial(cdsId, injectorId, pos)
    time.sleep(10)
    ins.place_vials_to_instrument_complete(cdsId, injectorId, placed_Vials)
    time.sleep(2)

    # 开始分析并监听远程结果文件变化
    file_flag = '.csv'
    previous_folder_list = InstrumentHandler.get_remote_folder_list(remote_folder_path, file_flag)
    ins.start_analysis(cdsId, analysis_job_parameters)

    while True:
        if ins.check_instrument_idle(cdsId):
            break
        time.sleep(20)
        current_folder_list = InstrumentHandler.get_remote_folder_list(remote_folder_path, file_flag)
        if current_folder_list != previous_folder_list:
            new_folder = [name for name in current_folder_list if name not in previous_folder_list]
            previous_folder_list = current_folder_list
            if new_folder:
                new_name = new_folder[0]
                print("新文件名称为:", new_name)
                remote_file_path = os.path.join(remote_folder_path, new_name)
                local_save_path = os.path.join(local_save_dir, new_name)
                InstrumentHandler.retrieve_and_save_file(remote_file_path, local_save_path)

    # 清理盘位并归位
    ins.ready_to_clear_instrument(cdsId, injectorId)
    time.sleep(2)
    ins.apply_clear_instrument_position(cdsId, injectorId, pos)
    time.sleep(10)
    # 使用与原脚本一致的 clearPositiones 结构
    clearPositiones = [
        {"positionIndex": -1, "positionName": pos, "vialBarcode": ""}
    ]
    ins.clear_instrument_vials_complete(cdsId, injectorId, clearPositiones)
    time.sleep(60)
    print("托盘成功归置原位")

    # 机械臂：从托盘取下小瓶放回仓位
    arm.hplc_drop(bottle_num)


if __name__ == '__main__':
    base_url = "http://192.168.58.131:9100"
    username = 'admin'
    password = 'agilent'
    cdsId = 17
    pos = "D1B-A9"
    workPlanNo = '1721207124'
    isActive = 1
    labName = 'Lab1'
    batch_id = "20240619135729"
    injectorId = '18df4f9d-01c9-4fed-bca7-f12db5febac4'
    lims_data = {
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
                        "status": "New"
                    }
                ]
            }
        ]
    }
    samples = [{
        "barCode": "20240619135729-1",
        "type": "Sample",
        "name": "石脑油1",
        "status": "New",
        "batchId": "20240619135729",
        "vialList": [{
            "type": "Vial",
            "barCode": "",
            "labName": "Lab1",
            "analysisProject": "testLC",
            "status": "New"
        }]
    }]
    placed_Vials = [{
        "positionIndex": -1,
        "positionName": "D1B-A9",
        "vialBarcode": "",
        "placeOnInstrumentDateTime": ""
    }]
    analysis_job_parameters = None
    remote_folder_path = r'\\192.168.58.132\Data'
    local_save_dir = r'station_workers/HPLC液相/Data'
    bottle_num = 0

    run_hplc_robot_and_instrument_flow(
        base_url,
        username,
        password,
        cdsId,
        injectorId,
        pos,
        workPlanNo,
        isActive,
        labName,
        batch_id,
        lims_data,
        samples,
        placed_Vials,
        analysis_job_parameters,
        remote_folder_path,
        local_save_dir,
        bottle_num
    )


