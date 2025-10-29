from crcmod import mkCrcFun
from binascii import unhexlify
from crcmod import mkCrcFun


def crc16_modbus(s):
    crc16 = mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
    return get_crc_value(s, crc16)


def get_crc_value(s, crc16):
    data = s.replace(' ', '')
    crc_out = hex(crc16(unhexlify(data))).upper()
    str_list = list(crc_out)
    if len(str_list) == 5:
        str_list.insert(2, '0')  # 位数不足补0
    crc_data = ''.join(str_list[2:])
    return crc_data[:2] + crc_data[2:]

def calcCRC(data_bytes):
    """计算字节数据的CRC值（返回2字节bytes）"""
    crc16 = mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)
    return crc16(data_bytes).to_bytes(2, byteorder='little')  # Modbus使用小端序

def verifyCRC(data_with_crc):
    """验证带CRC的数据有效性"""
    if len(data_with_crc) < 2:
        return False
    # 分离数据和CRC
    data_part = data_with_crc[:-2]
    received_crc = data_with_crc[-2:]
    # 计算实际CRC
    actual_crc = calcCRC(data_part)
    return actual_crc == received_crc

def appendCRCfunc(data_list):
    """为原始数据添加CRC校验码"""
    data_bytes = bytes(data_list)
    crc = calcCRC(data_bytes)
    return data_list + list(crc)


if __name__ == '__main__':
    send_str = [0xaa, 0x0e, 0x01, 0x02, 0x00, 0x00, 0x00, 0x00, 0x64, 0x00, 0x0a]
    print(appendCRCfunc(send_str))
