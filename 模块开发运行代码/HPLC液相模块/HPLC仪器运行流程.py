import os
import shutil
import time
from datetime import datetime

import requests
class InstrumentHandler:
    def __init__(self, base_url):
        self.base_url = base_url
        self.auth_token = None

    # 登录方法
    def login(self, username, password):
        url = f"{self.base_url}/api/v1/Authentication"
        params = {
            'userName': username,
            'userPassword': password
        }

        try:
            response = requests.put(url, params=params)
            response_data = response.json()

            if response.status_code == 200:
                if response_data['statusCode'] == 0:
                    self.auth_token = response_data['data']['authenticationToken']
                    print(f"登录成功。认证令牌：{self.auth_token}")
                else:
                    print(f"登录失败。错误消息：{response_data['errorMessage']}")
            else:
                print(f"请求失败，状态码：{response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"发生错误：{e}")

    # 获取系统信息方法
    def get_system_info(self):
        url = f"{self.base_url}/api/v1/SystemInfo"

        headers = {
            'Authorization': f'Bearer {self.auth_token}'
        }

        try:
            response = requests.get(url, headers=headers)
            response_data = response.json()
            if response.status_code == 200:
                if response_data['statusCode'] == 0:
                    system_info = response_data['data']
                    print("系统信息：")
                    print(system_info)
                    return system_info
                else:
                    error_message = response_data['errorMessage']
                    print(f"无法获取系统信息。错误消息：{error_message}")
            else:
                print(f"请求失败，状态码：{response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"发生错误：{e}")

    # 根据 CDS ID 获取仪器信息方法
    def get_instrument_info_by_cdsid(self, cdsId):
        url = f"{self.base_url}/api/v1/Instrument/auto/cdsid"

        params = {
            'cdsId': cdsId
        }

        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/json'
        }

        try:
            response = requests.get(url, params=params, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                if response_data['statusCode'] == 0:
                    instrument_info = response_data['data']
                    print(f"CDS ID {cdsId} 的仪器信息：")
                    print(instrument_info)
                    return instrument_info
                else:
                    error_message = response_data['errorMessage']
                    print(f"无法获取仪器信息。错误消息：{error_message}")
            else:
                print(f"请求失败，状态码：{response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"发生错误：{e}")
    # 清理测试瓶完成事件方法
    def clear_instrument_vials_complete(self, cdsId, injectorId, clearPositiones):
        url = f"{self.base_url}/api/v1/Events/ClearInstrumentVialsComplete?cdsId={cdsId}&injectorId={injectorId}"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/json'
        }
        try:
            response = requests.put(url, json=clearPositiones, headers=headers)
            response_data = response.json()
            if response.status_code == 200:
                if response_data['statusCode'] == 0:
                    message = response_data['message']
                    print(f"清理测试瓶完成事件成功：{message}")
                else:
                    error_message = response_data['errorMessage']
                    error_code = response_data['errorCode']
                    print(f"清理测试瓶完成事件失败。错误码：{error_code}，错误消息：{error_message}")
            else:
                print(f"请求失败，状态码：{response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"发生请求异常：{e}")

    # 准备放样到仪器事件方法
    def ready_to_place_vial_to_instrument(self, cdsId, injectorId):
        url = f"{self.base_url}/api/v1/Events/ReadyToPlaceVialToInstrument?cdsId={cdsId}&injectorId={injectorId}"

        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/json'
        }
        try:
            response = requests.put(url, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                if response_data['statusCode'] == 0:
                    positions = response_data['data']
                    print(f"仪器已准备好接收样品瓶。可用位置：{positions}")
                    return positions
                else:
                    error_message = response_data['errorMessage']
                    print(f"无法检查放样准备状态。错误消息：{error_message}")
            else:
                print(f"请求失败，状态码：{response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"发生错误：{e}")

    # 按批次进行设置样品数据
    def batch_set_sample_data(self, lims_data):
        url = f"{self.base_url}/api/v1/Sample/batch"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/json'
        }
        try:
            response = requests.post(url, json=lims_data, headers=headers)
            response_data = response.json()
            if response.status_code == 200:
                if response_data['statusCode'] == 0:
                    message = response_data['message']
                    print(f"按批次设置样品数据成功：{message}")
                else:
                    error_message = response_data['errorMessage']
                    error_code = response_data['errorCode']
                    print(f"按批次设置样品数据失败。错误码：{error_code}，错误消息：{error_message}")
            else:
                print(f"请求失败，状态码：{response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"发生请求异常：{e}")

    #根据Batch id查询样本数据
    def get_sample_data_by_batch_id(self, batch_id):
        url = f"{self.base_url}/api/v1/Sample/batchId"

        params = {
            'batchId': batch_id
        }

        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/json'
        }

        try:
            response = requests.get(url, params=params, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                if response_data['statusCode'] == 0:
                    sample_data = response_data['data']
                    print(f"批次号 {batch_id} 的样品数据：")
                    print(sample_data)
                    return sample_data
                else:
                    error_message = response_data['errorMessage']
                    print(f"无法获取样品数据。错误消息：{error_message}")
            else:
                print(f"请求失败，状态码：{response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"发生错误：{e}")

    # 查询计划事件
    def get_active_workplans(self, isActive,labName):
        url = f"{self.base_url}/api/v1/Workplan/active"

        params = {
            'isActive': isActive,
            'labName': labName
        }

        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/json'
        }

        try:
            response = requests.get(url, params=params, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                if response_data['statusCode'] == 0:
                    workplans = response_data['data']
                    print(f"实验室 {labName} 的活跃计划：")
                    print(workplans)
                    return workplans
                else:
                    error_message = response_data['errorMessage']
                    print(f"无法获取活跃计划数据。错误消息：{error_message}")
            else:
                print(f"请求失败，状态码：{response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"发生错误：{e}")

    # 移除工作计划项
    def remove_workplan_item(self, item_id):
        url = f"{self.base_url}/api/v1/Workplan?id={item_id}"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/json'
        }

        try:
            response = requests.delete(url, headers=headers)

            if response.status_code == 200:
                response_data = response.json()
                if response_data['statusCode'] == 0:
                    print(f"成功移除工作计划项 ID {item_id}")
                else:
                    error_message = response_data.get('errorMessage', '未知错误')
                    print(f"无法移除工作计划项。错误消息：{error_message}")
            else:
                print(f"请求失败，状态码：{response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"发生请求异常：{e}")

    # 生成计划事件
    def generate_workplan_event(self, workPlanNo, labName, samples):
        url = f"{self.base_url}/api/v1/Events/GenerateWorkplan?workPlanNo={workPlanNo}&labName={labName}"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/json'
        }
        try:
            # payload = {
            #     'samples': samples
            # }
            response = requests.put(url, json=samples, headers=headers)
            response_data = response.json()
            if response.status_code == 200:
                # Assuming the API response structure has statusCode and message fields
                if response_data['statusCode'] == 0:
                    message = response_data['message']
                    print(f"生成工作计划事件成功：{message}")
                else:
                    error_message = response_data.get('errorMessage', 'Unknown error')
                    error_code = response_data.get('errorCode', 'Unknown')
                    print(f"生成工作计划事件失败。错误码：{error_code}，错误消息：{error_message}")
            else:
                print(f"请求失败，状态码：{response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"发生请求异常：{e}")

    # 根据可用位置开始进样盘位
    def apply_instrument_position_to_place_vial(self, cdsId, injectorId, pos):
        url = f"{self.base_url}/api/v1/Events/ApplyInstrumentPositionToPlaceVial?cdsId={cdsId}&injectorId={injectorId}&pos={pos}"

        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/json'
        }

        try:
            response = requests.put(url, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                if response_data['statusCode'] == 0:
                    positions = response_data['data']
                    print(f"申请放样到仪器特定位置事件成功发送。")
                    return positions
                else:
                    error_message = response_data['errorMessage']
                    print(f"无法发送申请放样事件。错误消息：{error_message}")
            else:
                print(f"请求失败，状态码：{response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"发生请求异常：{e}")

    # 放置测试瓶到仪器完成事件
    def place_vials_to_instrument_complete(self, cdsId, injectorId, placed_Vials):
        url = f"{self.base_url}/api/v1/Events/PlaceVialsToInstrumentComplete?cdsId={cdsId}&injectorId={injectorId}"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/json'
        }
        try:
            response = requests.put(url, json=placed_Vials, headers=headers)
            response_data = response.json()
            if response.status_code == 200:
                if response_data['statusCode'] == 0:
                    message = response_data['message']
                    print(f"放置测试瓶到仪器完成事件成功：{message}")
                else:
                    error_message = response_data['errorMessage']
                    error_code = response_data['errorCode']
                    print(f"放置测试瓶到仪器完成事件失败。错误码：{error_code}，错误消息：{error_message}")
            else:
                print(f"请求失败，状态码：{response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"发生请求异常：{e}")

    #开始运行分析事件
    def start_analysis(self,cdsId, analysis_job_parameters):
        url = f"{self.base_url}/api/v1/Events/StartAnalysis?cdsId={cdsId}"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/json'
        }
        try:
            response = requests.put(url, json=analysis_job_parameters, headers=headers)
            response_data = response.json()
            if response.status_code == 200:
                if response_data['statusCode'] == 0:
                    message = response_data['message']
                    print(f"启动分析事件成功：{message}")
                else:
                    error_message = response_data['errorMessage']
                    error_code = response_data['errorCode']
                    print(f"启动分析事件失败。错误码：{error_code}，错误消息：{error_message}")
            else:
                print(f"请求失败，状态码：{response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"发生请求异常：{e}")


    # 检查仪器状态
    def check_instrument_idle(self, cdsId):
        url = f"{self.base_url}/api/v1/Events/CheckInstrumentIdle?cdsId={cdsId}"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/json'
        }
        try:
            response = requests.put(url, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                if response_data['statusCode'] == 0:
                    instrument_idle = response_data['statusCode']
                    print(f"仪器处于已处于Idle状态：{instrument_idle}")
                    return True
                else:
                    error_message = response_data['errorMessage']
                    print(f"仪器还未处于Idle状态：{error_message}")
            else:
                print(f"请求失败，状态码：{response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"发生错误：{e}")

        return False
    # 准备清洗仪器事件
    def ready_to_clear_instrument(self, cdsId, injectorId):
        url = f"{self.base_url}/api/v1/Events/ReadyToClearInstrument"
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/json'
        }
        params = {
            'cdsId': cdsId,
            'injectorId': injectorId
        }
        try:
            response = requests.put(url, params=params, headers=headers)
            response_data = response.json()
            if response.status_code == 200:
                if response_data['statusCode'] == 0:
                    logistics_info = response_data['data']
                    print("可以进行清理操作。进样器存储物流信息如下：")
                    print(logistics_info)
                else:
                    error_message = response_data['errorMessage']
                    print(f"清理仪器事件请求失败。错误消息：{error_message}")
            else:
                print(f"请求失败，状态码：{response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"发生请求异常：{e}")

    # 申请清理仪器特定盘（塔）位事件
    def apply_clear_instrument_position(self, cdsId, injectorId, pos):
        url = f"{self.base_url}/api/v1/Events/ApplyClearInstrumentPosition?cdsId={cdsId}&injectorId={injectorId}&pos={pos}"

        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json,text/json'
        }

        try:
            response = requests.put(url, headers=headers)
            response_data = response.json()

            if response.status_code == 200:
                if response_data['statusCode'] == 0:
                    print(f"申请清理仪器特定盘（塔）位事件成功发送。")
                    return response_data['data']
                else:
                    error_message = response_data['errorMessage']
                    print(f"无法发送申请清理仪器特定盘（塔）位事件。错误消息：{error_message}")
            else:
                print(f"请求失败，状态码：{response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"发生请求异常：{e}")

    #自动化，起初信息
    def virgin_ins(self):
        self.get_system_info()
        time.sleep(2)
        # 按批次进行设置样品数据
        self.batch_set_sample_data(lims_data)
        time.sleep(2)
        # 根据BatchID获取样本信息
        self.get_sample_data_by_batch_id(batch_id)
        time.sleep(2)
        # 根据 CDS ID 获取仪器信息示例
        self.get_instrument_info_by_cdsid(cdsId)
        time.sleep(2)
        # 检查仪器是否处于可操作的Idle状态
        self.check_instrument_idle(cdsId)
        time.sleep(2)

    # 远程文件
    def get_remote_folder_list(self, folder_path, substring):
        folder_list = []
        for root, dirs, files in os.walk(folder_path):
            for directory in dirs:
                if substring.lower() in directory.lower():
                    folder_list.append(directory)
            for file in files:
                if file.lower().endswith('.csv') and substring.lower() in file.lower():
                    folder_list.append(file)  # 只添加文件名，不带路径
        return folder_list

    # 开始配置计划
    def intend_ins(self):
        # 生成计划事件
        self.generate_workplan_event(workPlanNo, labName, samples)
        time.sleep(2)
        # # 查询计划事件
        self.get_active_workplans(isActive, labName)
        time.sleep(2)
        # 准备放样到仪器事件
        self.ready_to_place_vial_to_instrument(cdsId, injectorId)
        time.sleep(2)
        # 根据可用位置开始申请进样盘位
        self.apply_instrument_position_to_place_vial(cdsId, injectorId, pos)
        time.sleep(10)
        # 放置测试瓶完成事件
        self.place_vials_to_instrument_complete(cdsId, injectorId, placed_Vials)
        time.sleep(2)
    def star_run(self):
        # step A: 查询远程文件夹下的内容
        folder_path = r'\\192.168.58.132\Data'
        file_flag = '.csv'
        previous_folder_list = self.get_remote_folder_list(folder_path, file_flag)
        # step B: 开始实验
        # 开始运行事件
        self.start_analysis(cdsId, analysis_job_parameters)
        while True:
            if self.check_instrument_idle(cdsId):
                # 在仪器空闲时执行其他事件方法
                # self.ready_to_clear_instrument(cdsId, injectorId)
                break  # 可以选择退出循环，或根据需要继续检测
            time.sleep(20)  # 每隔20秒钟检测一次仪器状态
            current_folder_list = self.get_remote_folder_list(folder_path, file_flag)
            if current_folder_list != previous_folder_list:
                # step1:找到新出现的文件夹名称
                new_folder = [name for name in current_folder_list if name not in previous_folder_list]
                previous_folder_list = current_folder_list
                new_folder_name = new_folder[0]
                # print(datetime.now().strftime("%Y%m%d_%H%M%S_%f"), new_folder_name)
                print("新文件名称为:",new_folder_name)

                # 读取远程文件并保存到本地
                remote_file_path = os.path.join(folder_path, new_folder_name)
                local_save_path = os.path.join(r'F:\协同开发\lgs分支\git-lims\station_workers\HPLC液相\Data', new_folder_name)  # 修改为你的本地保存路径
                self.retrieve_and_save_file(remote_file_path, local_save_path)

    def later_clear(self):
        # 检查仪器是否处于可操作的Idle状态
        self.ready_to_clear_instrument(cdsId, injectorId)
        time.sleep(2)
        # 申请清理仪器特定盘（塔）位事件
        self.apply_clear_instrument_position(cdsId, injectorId, pos)
        time.sleep(10)
        # 清理测试瓶完成事件
        self.clear_instrument_vials_complete(cdsId, injectorId, clearPositiones)
        time.sleep(60)
        print("托盘成功归置原位")

    # 将远程文件复制到本地指定路径
    def retrieve_and_save_file(self, remote_path, local_path):
        try:
            # 使用shutil库从远程路径复制到本地路径
            shutil.copy(remote_path, local_path)
            # print(f"成功从远程路径 {remote_path} 复制文件到本地路径 {local_path}")
            print("文件成功到达本地Data目录下")
        except Exception as e:
            print(f"复制文件时发生错误：{e}")


if __name__ == '__main__':
    base_url = "http://192.168.58.131:9100"
    username = 'admin'
    password = 'agilent'
    cdsId = 17
    pos = "D1B-A9"
    workPlanNo = '1721207124'
    # workPlanNo = '1821207126'
    isActive=1
    labName='Lab1'
    batch_id = "20240619135729"
    injectorId = '18df4f9d-01c9-4fed-bca7-f12db5febac4'  # 实际的注射器 ID d1b
    clearPositiones = [
        {"positionIndex": -1, "positionName": "D1B-A9", "vialBarcode": ""},
    ]
    # "vialBarcode": "20240619135729-1-001"
    lims_data = {
        "limsSamples": [
            {   "barCode": "20240619135729-1",
                "type": "Sample",
                "name": "石脑油1",
                "status": "New",
                "batchId": "20240619135729",
                "vialList": [{
                    "type": "Vial",
                    # "barCode": "20240619135729-1-001",
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
            # "barCode": "20240619135729-1-001",
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
        # "vialBarcode": "20240619135729-1-001",
        "placeOnInstrumentDateTime": ""
    }]
    analysis_job_parameters = None
    # 创建仪器处理类实例
    instrument_handler = InstrumentHandler(base_url)
    # 登录获取认证令牌
    instrument_handler.login(username, password)

    if instrument_handler.auth_token:
        # 仪器自动化开始
        instrument_handler.virgin_ins()
        instrument_handler.intend_ins()
        instrument_handler.star_run()
        instrument_handler.later_clear()






