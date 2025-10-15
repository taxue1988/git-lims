#!/bin/bash

# 这个脚本用于启动支持 ASGI 的 Django 应用
# 使用 Daphne 服务器

echo "正在启动 Daphne ASGI 服务器..."

# 如果您使用了虚拟环境，请取消下面这行的注释并修改为正确的路径
# source /path/to/your/venv/bin/activate

# 启动 Daphne 服务器
# -b 0.0.0.0: 绑定到所有网络接口，允许从公网访问
# -p 8000: 在 8000 端口上监听。您可以根据需要修改端口。
# lims.asgi:application: 指向您的 ASGI 应用

daphne -b 0.0.0.0 -p 8000 lims.asgi:application

