import socket
import json
import time
import sys


class EC66:
    def __init__(self, ip: str):
        super().__init__()
        self.sock = None
        self.ip = ip
        self.connect(ip)

    def connect(self, ip):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((ip, 8055))
            self.able_servo(1)
        except Exception as e:
            self.sock.close()
            print("反应_EC66初始化：失败！")

    def disconnect(self):
        try:
            self.sock.close()
            print(self.ip, "已断开连接！")
        except Exception as e:
            print(e)

    def able_servo(self, para):
        """1:机械臂伺服使能;0机械臂伺服关闭"""
        cmd = "set_servo_status"
        params = {"status": para}
        is_success, result, jdata_id = self.send_cmd(cmd, params)
        if is_success:
            print('反应_EC66伺服已使能，连接成功！')
        else:
            print('反应_EC66伺服已关闭，连接失败！')

    def send_cmd(self, cmd, params=None, id=1):
        if not params:
            params = []
        else:
            params = json.dumps(params)
        sendStr = "{{\"method\":\"{0}\",\"params\":{1},\"jsonrpc\":\"2.0\",\"id\":{2}}}".format(cmd, params,
                                                                                                id) + "\n"
        try:
            self.sock.sendall(bytes(sendStr, "utf-8"))
            ret = self.sock.recv(1024)
            jdata = json.loads(str(ret, "utf-8"))
            if "result" in jdata.keys():
                return True, json.loads(jdata["result"]), jdata["id"]
            elif "error" in jdata.keys():
                return False, jdata["error"], jdata["id"]
            else:
                return False, None, None
        except Exception as e:
            return False, None, None


    def run_jbi(self, jbi_filename):
        """filename：待运行文件名，字符串。返回值：成功true，失败false"""
        cmd = 'runJbi'  # 运行机械臂Jbi文件命令/方法
        # 检测jbi文件是否存在
        file_exists = False
        for i in range(10):
            suc, result, id = self.send_cmd('checkJbiExist', {'filename': jbi_filename})
            if suc and result == 1:
                file_exists = True
                break
            else:
                print(f"{jbi_filename} 文件不存在; 循环次数： {i}")

        if not file_exists:
            print(f"{jbi_filename} 文件不存在，无法运行。")
            return False

        # 运行jbi文件
        suc, result, id = self.send_cmd(cmd, {'filename': jbi_filename})
        if not suc:
            print(f"运行 {jbi_filename} 文件失败。")
            return False

        # 检测状态
        while True:
            state = self.get_jbi_state()
            if state is None:
                print("无法获取jbi文件状态，退出检测。")
                break
            elif state == 0:  # 停止状态
                break
            elif state == 4:  # 错误状态
                # step1 判断是否处于远程模式，否则一直等
                while self.get_robot_mode() == 2:
                    time.sleep(1)
                # step2 判断是否处于示教模式，否则一直等
                while self.get_robot_mode() == 1:
                    time.sleep(1)
                # step3 重新连接
                while self.get_robot_mode() != 2:
                    time.sleep(1)
                    self.run_jbi(jbi_filename)
            else:
                time.sleep(1)
            time.sleep(1)

        return True

    def set_B_value(self, addrnum, num):
        """设置机械臂全局变量B的参数：addr 变量地址(0~255)。value  变量值(0,2147483647)"""
        cmd = 'setSysVarB'  # 设置机械臂B寄存器命令/方法
        params = {"addr": addrnum, "value": num}  # 将机械臂B00addrnum寄存器的值设置为num
        suc, result, id = self.send_cmd(cmd, params)
        if suc and result == 1:
            print('设置B的值为' + str(num) + '成功！')

    def get_I_variable_state(self, addrnum):
        """获取机械臂I寄存器的值：addr 变量地址(0~255)"""
        cmd = 'getSysVarI'  # 获取机械臂D寄存器命令/方法
        params = {"addr": addrnum}  # 获取机械臂I000寄存器的值
        suc, result, id = self.send_cmd(cmd, params)
        print("i值为：", result)
        return result

    def get_D_variable_state(self, addrnum):
        """获取机械臂I寄存器的值：addr 变量地址(0~255)"""
        cmd = 'getSysVarD'  # 获取机械臂D寄存器命令/方法
        params = {"addr": addrnum}  # 获取机械臂I000寄存器的值
        suc, result, id = self.send_cmd(cmd, params)
        return result

    def get_jbi_state(self):
        """获取jib文件状态：0 停止状态,1 暂停状态,2 急停状态,3 运行状态,4 错误状态"""
        cmd = 'getJbiState'  # 获取机械臂B寄存器命令/方法
        params = {}
        suc, result, id = self.send_cmd(cmd, params)
        if suc and result is not None and 'runState' in result:
            return result['runState']
        else:
            print("无法获取jbi文件状态")
            return None

    def get_input_state(self, input_addr):
        """ 获取输出 IO 状态：int[0,1]，0 为关，1 为开，范围：int[0,19][48,51]。 addr：输出 IO 地址"""
        cmd = 'getInput'  # 获取机械臂输入IO状态命令/方法
        params = {"addr": input_addr}  # 获取机械臂输入X005输入状态（孔板传感器状态）
        suc, result, id = self.send_cmd(cmd, params)
        return result


    def get_robot_mode(self):
        """ 获取机器人模式： 示教模式 0，自动模式 1，远程模式 2"""
        cmd = 'getRobotMode'  # 获取机械臂输入IO状态命令/方法
        params = {}
        suc, result, id = self.send_cmd(cmd, params)
        if suc and result is not None and 'mode' in result:
            return result['mode']
        else:
            print("无法获取机器人模式")
            return None

    def get_robot_state(self):
        """ 停止状态 0，暂停状态 1，急停状态 2，运行状态 3，报警状态 4，碰撞状态 5"""
        cmd = 'getRobotState'  # 获取机械臂输入IO状态命令/方法
        params = {}
        suc, result, id = self.send_cmd(cmd, params)
        return result

    def get_B_value(self, addrnum):
        """获取机械臂全局变量B的参数：addr 变量地址(0~255)。"""
        cmd = 'getSysVarB'  # 获取机械臂B寄存器命令/方法
        params = {"addr": addrnum}  # 获取机械臂B00addrnum寄存器的值
        suc, result, id = self.send_cmd(cmd, params)
        return result


if __name__ == '__main__':
    arm = EC66('192.168.58.170')
    arm.disconnect()
