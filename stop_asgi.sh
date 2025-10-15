#!/usr/bin/env bash

# Gunicorn 进程标识符
APP_NAME="lims.asgi:application"

echo -e "\033[34m-----------Gunicorn 进程----------------\033[0m"

ps -ef | grep "gunicorn.*${APP_NAME}" | grep -v grep

sleep 0.5

echo -e'\n-----------------准备关闭----------------- '

# 查找并终止 Gunicorn 进程
PIDS=$(ps -ef | grep "gunicorn.*${APP_NAME}" | grep -v grep | awk '{print $2}')

if [ -n "$PIDS" ]; then
    echo "正在终止 Gunicorn 进程: $PIDS"
    echo $PIDS | xargs kill -9
    echo "进程已终止。"
else
    echo "未找到正在运行的 Gunicorn 进程。"
fi

sleep 0.5

