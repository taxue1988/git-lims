from 艾利特机械臂 import EC66
from GCMS import InstrumentControl
import time


class GCMS_module:
    def __init__(self):
        self.gc_arm = EC66('192.168.58.120')
        self.instrument_control = InstrumentControl("http://192.168.58.125:8082")
        self.status_flag = False

    def get_b_status(self):
        b = self.gc_arm.get_B_value(0)
        return b

    def check_arm_connection(self):
        """暴露给外部的机械臂连接检查方法"""
        return self.gc_arm.check_connection()

    def check_instrument_connection(self):
        """暴露给外部的GCMS仪器连接检查方法"""
        return self.instrument_control.check_connection()

    def check_arm_connection(self):
        return self.gc_arm.check_connection()

    def kb_to_gcms(self, bottle_num):
        self.gc_arm.set_B_value(0, bottle_num)
        self.gc_arm.run_jbi('kb_to_gcms')

    def gc_drop(self, bottle_num):
        self.gc_arm.set_B_value(0, bottle_num)
        self.gc_arm.run_jbi('gc_drop')

    def get_gcms_jbi_status(self):
        self.gc_arm.get_jbi_state()

    def gc_move_to_tower(self):
        self.instrument_control.move_tower_to_position(0, 1)  # 执行Tower转到指定位置的指令

    def gc_action_conb(self):  # GCMS执行序列
        #调用方法
        self.instrument_control.get_model()  # 读取仪器型号
        self.instrument_control.get_status()  # 读取仪器状态
        self.instrument_control.get_run_status()  # 读取运行状态
        self.instrument_control.get_run_mode()  # 读取运行模式
        self.instrument_control.get_laboratory()  # 读取实验室
        self.instrument_control.move_tower_to_position(0, 1)  # 执行Tower转到指定位置的指令
        # # # # 启动序列文件采集
        self.instrument_control.get_sequence_info('2024 Dec 04 1403_default.sequence.xml')  # 读取序列信息
        # # # 启动序列文件采集
        self.instrument_control.start_data_acquisition('2024 Dec 04 1403_default.sequence.xml', 0, True)
        self.instrument_control.get_sequence_result_info('2024 Dec 04 1403_default.sequence.xml')  # 采集执行结果信息
        self.instrument_control.is_paused()  # 当前序列是否暂停
        # 提交并运行序列post
        values = {
            "Sequence": {
                "samples": [
                    {
                        "sampleID": 0,  # 样本ID
                        # "acqMethodPathName": "D:\\MassHunter\\GCMS\\1\\methods",
                        "acqMethodPathName": "D:\\MassHunter\\GCMS\\1\\methods",
                        "acqMethodFileName": "Demo.M",
                        "dilution": 1,
                        "sampleName": "Sample 1",
                        "sampleType": 1,
                        "vial": 1
                    }
                ],
                "sequenceComment": "comment",
                "sequenceInjectBarCodeMismatch": 0,
                "sequenceOperator": "2222",
                "sequenceOverwriteExistingData": 1,
                "sequencePostSeqAcqCommand": "",
                "sequencePostSeqDACommand": "",
                "sequencePreSeqAcqCommand": "",
                "sequencePreSeqDACommand": "",
                "sequenceReProcessing": "False",
                "sequenceDecoupleDataAnalysis": 1,
                "sequenceDelayECMUpload": 0,
                # "sequenceSeqPathFileName": "C:\\MassHunter\\GCMS\\1\\DATA\\"
                "sequenceSeqPathFileName": "C:\\MassHunter\\GCMS\\1\\data\\"
            },
            "CustomDataFileName": False
        }
        self.instrument_control.submit_and_run_sequence(values)  # 提交并运行序列
        self.instrument_control.pause_data_acquisition()  # 暂停当前采集
        self.instrument_control.resume_data_acquisition()  # 恢复并继续当前采集
        self.instrument_control.park_tray(park_value=0, block=True)  # 执行 Tray 的  Park 指令
        self.instrument_control.release_lock()  # 释放程序锁
        self.instrument_control.move_tower_to_position(0, 1)  # 执行Tower转到指定位置的指令

    def start(self,bottle_num):
        self.gc_move_to_tower()
        self.kb_to_gcms(bottle_num)
        self.gc_action_conb()
        time.sleep(60)
        while test.instrument_control.get_run_mode() != "\"NotRun\"":  # 获取GCMS运行状态
            time.sleep(10)
        time.sleep(5)
        self.gc_move_to_tower()
        time.sleep(2)
        self.gc_move_to_tower()
        self.gc_drop(bottle_num)
        self.status_flag = True


if __name__ == '__main__':
    test = GCMS_module()
    test.start(1)

