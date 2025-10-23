import json
import urllib.request
import urllib.parse
import urllib.error


# 序列1 未包括报告方法、方法路径、DA方法文件 2024 May 09 1058_default.sequence.xml
# 序列2 包括了报告方法、方法路径、DA方法文件 2024 May 15 1416_default.sequence.xml
# 序列3 stand序列 2024 May 21 1702_default.sequence.xml
class InstrumentControl:
    def __init__(self, base_url):
        self.base_url = base_url

    def check_connection(self):
        """检查与GCMS仪器的HTTP连接"""
        try:
            # get_status是一个轻量级的请求，适合用于心跳检查
            self.get_status()
            return True
        except (urllib.error.URLError, urllib.error.HTTPError):
            return False

    def get_model(self):  # 读取仪器型号
        url = f"{self.base_url}/Instrument/model"
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
        print("仪器型号:")
        print(data)
        return data

    def get_status(self):  # 读取仪器状态
        url = f"{self.base_url}/Instrument/Status"
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
        print("仪器状态:")
        print(data)
        return data

    def get_tower_position(self, position, bottle):  # 读取塔台位置
        url = f"{self.base_url}/Instrument/Tower/Pos"
        values = {'Position': position, 'Bottle': bottle}
        params = urllib.parse.urlencode(values)
        with urllib.request.urlopen(url, params.encode('utf-8')) as response:
            data = response.read().decode('utf-8')
        print("塔的位置数据:")
        print(params)
        print(data)
        return data

    def get_sequence_info(self, sequence_path):  # 读取序列信息
        url = f"{self.base_url}/Instrument/Sequence"
        values = {'ValidDataAcquisition': False, 'Absolute': False, 'SequencePath': sequence_path}
        params = urllib.parse.urlencode(values)
        full_url = f"{url}?{params}"
        req = urllib.request.Request(full_url, method='GET')
        try:
            with urllib.request.urlopen(req) as response:
                data = response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            data = f'HTTP Error: {e.code} - {e.reason} - {e.read().decode("utf-8")}'
        except urllib.error.URLError as e:
            data = f'HTTP Error: {e.code} - {e.reason}'
        print("序列信息:")
        print(data)
        return data

    def get_sequence_result_info(self, sequence_path):  # 采集执行结果信息
        # 构造URL
        url = f"{self.base_url}/Instrument/SequenceResult"
        values = {'ValidDataAcquisition': False, 'Absolute': False, 'SequencePath': sequence_path}
        params = urllib.parse.urlencode(values)
        full_url = f"{url}?{params}"
        req = urllib.request.Request(full_url, method='GET')
        try:
            with urllib.request.urlopen(req) as response:
                data = response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            data = f'HTTP Error: {e.code} - {e.reason} - {e.read().decode("utf-8")}'
        except urllib.error.URLError as e:
            data = f'HTTP Error: {e.reason}'
        print("采集执行结果信息:")
        print(data)
        return data

    def get_report_result_info(self, sequence_path):  # 读取报告数据(如果序列未设置报告返回内容为空)
        # 构造URL
        url = f"{self.base_url}/Instrument/ReportResult"
        values = {'ValidDataAcquisition': False, 'Absolute': False, 'SequencePath': sequence_path}
        params = urllib.parse.urlencode(values)
        full_url = f"{url}?{params}"

        # 发送GET请求
        req = urllib.request.Request(full_url, method='GET')
        try:
            with urllib.request.urlopen(req) as response:
                data = response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            data = f'HTTP Error: {e.code} - {e.reason} - {e.read().decode("utf-8")}'
        except urllib.error.URLError as e:
            data = f'HTTP Error: {e.reason}'
        print("读取报告数据信息:")
        print(data)
        return data

    def get_run_status(self):  # 读取运行状态
        url = f"{self.base_url}/Instrument/RunStatus"
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
        print("运行状态:")
        print(data)
        return data

    def get_run_mode(self):  # 读取运行模式
        url = f"{self.base_url}/Instrument/RunMode"
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
        print("运行模式:")
        print(data)
        return data

    def get_laboratory(self):  # 读取实验室
        url = f"{self.base_url}/Instrument/Laboratory"
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
        print("读取实验室:")
        print(data)
        return data

    def start_data_acquisition(self, sequence_path, start_index, rename_existing_data):  # 启动序列文件采集
        url_base = f"{self.base_url}/Instrument/StartDataAcquisition/File"
        values = {
            'SequencePath': sequence_path,
            'StartIndex': start_index,
            'RenameExistingData': rename_existing_data
        }
        data = urllib.parse.urlencode(values).encode()
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        req = urllib.request.Request(url_base, headers=headers, data=data, method='POST')
        try:
            with urllib.request.urlopen(req) as response:
                data = response.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            data = f'HTTP Error: {e.code} - {e.reason} - {e.read().decode("utf-8")}'
        except urllib.error.URLError as e:
            data = f'HTTP Error: {e.code} - {e.reason}'
        print("启动序列采集:")
        print(data)
        return data

    # 提交并运行序列
    def submit_and_run_sequence(self, values):
        url_base = f"{self.base_url}/Instrument/StartDataAcquisition"
        # 安装代理处理器
        urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler()))

        # 将字典转换为JSON字符串
        json_data = json.dumps(values).encode('utf-8')

        # 定义请求头
        headers = {
            'Content-Type': 'application/json',  # 内容类型
        }
        print("提交并运行序列:")

        # 创建请求
        req = urllib.request.Request(url_base, headers=headers, data=json_data, method='POST')

        try:
            # 发送请求
            response = urllib.request.urlopen(req)

            # 读取并打印响应
            data = response.read().decode('utf-8')
            print(data)

            return data  # 返回响应数据
        except urllib.error.HTTPError as e:
            # 捕获HTTP错误
            print(f'HTTP Error: {e.code} - {e.reason} - {e.read().decode("utf-8")}')
        except urllib.error.URLError as e:
            # 捕获URL错误
            print(f'HTTP Error: {e.reason}')

    # 当前序列是否暂停
    def is_paused(self):
        url = f"{self.base_url}/Instrument/Paused"
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
        print("当前序列是否暂停:")
        print(data)
        return data

    def pause_data_acquisition(self):  # 暂停当前采集
        url = f"{self.base_url}/Instrument/PauseDataAcquisition"

        # 准备POST请求的数据（假设没有数据需要发送）
        post_data = {}
        post_data_encoded = urllib.parse.urlencode(post_data).encode('utf-8') if post_data else None

        # 创建一个请求对象
        req = urllib.request.Request(url, data=post_data_encoded, method='POST')

        # 发送请求并获取响应
        try:
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode('utf-8')
            print(response_data)
            return response_data
        except urllib.error.HTTPError as e:
            # print(f"HTTP错误: {e.code} - {e.reason}")
            print("暂停当前采集:")
            print(e.read().decode('utf-8'))
        except urllib.error.URLError as e:
            print("URL错误:")
            print(e.reason)

    # 恢复并继续当前序列
    def resume_data_acquisition(self):  # 恢复并继续当前序列
        url = f"{self.base_url}/Instrument/ContinueDataAcquisition"

        # 准备POST请求的数据（假设没有数据需要发送）
        post_data = {}
        post_data_encoded = urllib.parse.urlencode(post_data).encode('utf-8') if post_data else None

        # 创建一个请求对象
        req = urllib.request.Request(url, data=post_data_encoded, method='POST')

        # 发送请求并获取响应
        try:
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode('utf-8')
            # print("恢复并继续执行当前序列:")
            print(response_data)
            return response_data
        except urllib.error.HTTPError as e:
            print("恢复并继续执行当前序列:")
            print({e.code})
            print(e.read().decode('utf-8'))
        except urllib.error.URLError as e:
            print("恢复并继续执行当前序列时出现URL错误:")
            print(e.reason)

    # 执行 Tray 的  Park 指令
    def park_tray(self, park_value=0, block=True):
        # 定义POST数据
        values = {
            'Park': str(park_value),
            'Block': str(block).lower()
        }

        # 将字典转换为URL编码的字符串
        data = urllib.parse.urlencode(values).encode()

        # 定义URL的基础部分
        url_base = f"{self.base_url}/Instrument/Tray/Park"

        # 定义请求头
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        print("执行 Tray 的 Park 指令:")

        # 创建请求对象
        req = urllib.request.Request(url_base, headers=headers, data=data, method='POST')

        try:
            # 执行请求并获取响应
            with urllib.request.urlopen(req) as response:
                # 读取响应内容并解码为字符串
                response_data = response.read().decode('utf-8')
                print("Tray Park 指令执行结果:")
                print(response_data)
                return response_data
        except urllib.error.HTTPError as e:
            # 处理HTTP错误
            print(f'HTTP Error: {e.code} - {e.reason} - {e.read().decode("utf-8")}')
            return f'HTTP Error: {e.code} - {e.reason} - {e.read().decode("utf-8")}'
        except urllib.error.URLError as e:
            # 处理URL错误
            print(f'URL Error: {e.reason}')
            return f'URL Error: {e.reason}'

    # 执行Tower转到指定位置的指令post
    def move_tower_to_position(self, position, bottle):
        # 定义POST数据
        values = {
            'Position': str(position),
            'Bottle': str(bottle)
        }

        # 将字典转换为URL编码的字符串
        data = urllib.parse.urlencode(values).encode('utf-8')

        # 定义URL的基础部分
        url_base = f"{self.base_url}/Instrument/Tower/Pos"

        # 定义请求头
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        print("执行 Tower 转到指定位置的指令:")

        # 创建请求对象
        req = urllib.request.Request(url_base, headers=headers, data=data, method='POST')

        try:
            # 执行请求并获取响应
            with urllib.request.urlopen(req) as response:
                # 读取响应内容并解码为字符串
                response_data = response.read().decode('utf-8')
                print("Tower 转到指定位置指令执行结果:")
                print(response_data)
                return response_data
        except urllib.error.HTTPError as e:
            # 处理HTTP错误
            print(f'HTTP Error: {e.code} - {e.reason} - {e.read().decode("utf-8")}')
            return f'HTTP Error: {e.code} - {e.reason} - {e.read().decode("utf-8")}'
        except urllib.error.URLError as e:
            # 处理URL错误
            print(f'URL Error: {e.reason}')
            return f'URL Error: {e.reason}'

    # 读取Report数据get
    def read_report_data(self, path, template_name, format='csv', encoding='gb2312'):
        # 拼接参数
        params = {
            'Path': path,
            'TemplateName': template_name,
            'Format': format,
            'Encoding': encoding
        }
        encoded_params = urllib.parse.urlencode(params)

        # 拼接URL
        url = f"{self.base_url}/Test/ReportData?{encoded_params}"

        print('读取Report数据:')
        # 创建GET请求
        req = urllib.request.Request(url, method='GET')

        try:
            # 发送请求并获取响应
            with urllib.request.urlopen(req) as response:
                # 读取响应内容并解码
                data = response.read().decode(encoding, 'ignore')
                return data
        except urllib.error.HTTPError as e:
            # 处理HTTP错误
            print('读取Report数据发生HTTP错误:')
            print(f'HTTP Error: {e.code} - {e.reason} - {e.read().decode("utf-8")}')
            raise  # 可以选择重新抛出异常或返回None
        except urllib.error.URLError as e:
            # 处理URL错误
            print('读取Report数据发生URL错误:')
            print(f'URL Error: {e.reason}')
            raise  # 可以选择重新抛出异常或返回None

    # 释放程序锁post
    def release_lock(self):
        # 构造URL
        url = f"{self.base_url}/Test/ReleaseLock"

        # 准备POST请求的数据（如果没有数据，则使用一个空字典）
        post_data = {}
        post_data_encoded = urllib.parse.urlencode(post_data).encode('utf-8') if post_data else None

        # 创建一个请求对象
        req = urllib.request.Request(url, data=post_data_encoded, method='POST')

        # 发送请求并获取响应
        try:
            with urllib.request.urlopen(req) as response:
                response_data = response.read().decode('utf-8')
                print("释放锁:")
                print(response_data)
                return response_data
        except urllib.error.HTTPError as e:
            print("HTTP错误:")
            print(f"状态码: {e.code}")
            print(e.read().decode('utf-8'))
        except urllib.error.URLError as e:
            # URL错误
            print("URL错误:")
            print(e.reason)
