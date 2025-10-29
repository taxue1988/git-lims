import socket
import json
import time
import select


class EC66:
    def __init__(self, ip: str):
        super().__init__()
        self.sock = None
        self.ip = ip
        if not self.connect():
            print(f"Warning: Initial connection to arm {ip} failed. Will attempt to reconnect later.")

    def connect(self):
        """Establishes a connection to the robot arm and enables the servo. Returns True on success, False on failure."""
        if self.sock:
            self.disconnect()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.settimeout(5.0)  # Set a 5-second timeout for all socket operations
            self.sock.connect((self.ip, 8055))

            return True  # Assume connection is successful if socket connects
        except (socket.timeout, socket.error, Exception) as e:
            print(f"Arm connection failed: {e}")
            self.disconnect()  # Ensure cleanup
            return False

    def disconnect(self):
        """Safely closes the socket connection."""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                print(f"Error while closing socket: {e}")
            finally:
                self.sock = None
                print(f"Arm {self.ip} disconnected.")

    def able_servo(self, para):
        """Enables (1) or disables (0) the arm servo. Returns True/False."""
        is_success, result, _ = self.send_cmd("set_servo_status", {"status": para})
        # The arm might return 1, true (boolean), or "true" (string) on success.
        if is_success and str(result).lower() == 'true' or str(result) == '1':
            print('Arm servo enabled successfully.')
            return True
        else:
            # If enabling servo fails, print the detailed reason from the arm
            print(f'Failed to enable arm servo. Reason: {result}')
            return False

    def get_servo_status(self):
        """获取机械臂伺服状态。成功时返回True（启用）或False（未启用），失败时返回None。"""
        is_success, result, _ = self.send_cmd("getServoStatus")
        if is_success:
            # The arm might return 1, true (boolean), or "true" (string).
            if str(result).lower() == 'true' or str(result) == '1':
                return True
            else:
                return False
        else:
            print(f"获取伺服状态失败: {result}")
            return None

    def send_cmd(self, cmd, params=None, id=1):
        """Sends a command to the arm. Returns (success, result, id)."""
        if not self.sock:
            return False, "Socket not connected", None

        if params is None:
            params = {}

        sendStr = json.dumps({
            "method": cmd,
            "params": params,
            "jsonrpc": "2.0",
            "id": id
        }) + "\n"

        try:
            self.sock.sendall(bytes(sendStr, "utf-8"))
            ret = self.sock.recv(1024)
            if not ret:
                raise ConnectionResetError("Connection closed by peer")
            jdata = json.loads(str(ret, "utf-8"))
            if "result" in jdata:
                # The original version performed a double JSON load, which is necessary if the 'result' field is a string containing JSON.
                # Replicating that logic here.
                try:
                    # Try to parse the result as JSON, if it's a string.
                    if isinstance(jdata["result"], str):
                        return True, json.loads(jdata["result"]), jdata["id"]
                    else:
                        return True, jdata["result"], jdata["id"]
                except json.JSONDecodeError:
                    # If it's not a JSON string (e.g., just a number or simple string), return it directly.
                    return True, jdata["result"], jdata["id"]
            else:
                return False, jdata.get("error", "Unknown error"), jdata["id"]
        except socket.timeout as e:
            # On timeout, don't disconnect. The connection might still be alive.
            print(f"Command '{cmd}' timed out: {e}")
            return False, str(e), None
        except (ConnectionResetError, socket.error) as e:
            # On fatal network errors, disconnect.
            print(f"Command '{cmd}' failed due to network error: {e}")
            self.disconnect()
            return False, str(e), None
        except json.JSONDecodeError as e:
            print(f"Failed to decode response for '{cmd}': {e}")
            return False, str(e), None
        except Exception as e:
            print(f"An unexpected error occurred during command '{cmd}': {e}")
            self.disconnect()
            return False, str(e), None

    def get_robot_mode(self):
        """获取机器人当前模式。成功时返回模式编号，失败时返回None。"""
        is_success, result, _ = self.send_cmd("getRobotMode")
        if is_success:
            print(f"DEBUG: 收到机械臂模式: {result} (类型: {type(result)})")  # 增加调试日志
            return result
        else:
            print(f"获取机器人模式失败: {result}")
            return None

    def is_connected(self):
        """通过查询伺服状态来判断连接是否有效。
        如果get_servo_status()返回True，则视为连接成功。
        如果get_servo_status()返回False或None，则视为连接不成功。
        """
        return self.get_servo_status() is True

    # --- Other methods remain below ---
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
        self.send_cmd('setSysVarB', {"addr": addrnum, "value": num})

    def set_D_value(self, addrnum, num):
        self.send_cmd('setSysVarD', {"addr": addrnum, "value": num})

    def get_jbi_state(self):
        """获取jib文件状态：0 停止状态,1 暂停状态,2 急停状态,3 运行状态,4 错误状态"""
        suc, result, id = self.send_cmd('getJbiState', {})
        if suc and isinstance(result, dict) and 'runState' in result:
            return result['runState']
        elif suc and isinstance(result, int):
            # 如果直接返回整数状态值，也接受
            return result
        else:
            print(f"无法获取或解析jbi文件状态，收到的result: {result}")
            return None

