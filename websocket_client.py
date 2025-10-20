import websocket
import _thread
import time
import json

def on_message(ws, message):
    data = json.loads(message)
    print(data['message'])

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print("### closed ###")

def on_open(ws):
    print("Opened connection")

if __name__ == "__main__":
    # 请将 'your_server_ip' 替换为您的云服务器 IP 地址
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://62.234.51.178:8000/ws/test/",
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()

