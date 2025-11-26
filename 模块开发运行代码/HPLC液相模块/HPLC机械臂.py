from 艾利特机械臂 import EC66
import time


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

    def start(self, bottle_num):
        # bottle_num的数值代表从指定仓位号里拿取与放回瓶子
        self.kb_to_hplc(bottle_num)
        """此处可填写HPLC仪器运行流程相关代码"""
        self.hplc_drop(bottle_num)


if __name__ == '__main__':
    test = HPLC_module()
    test.start(0)

