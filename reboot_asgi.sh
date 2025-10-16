#!/usr/bin/env bash

# 设置颜色代码
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Gunicorn 进程标识符，用于查找和管理进程
APP_NAME="lims.asgi:application"

echo -e "${BLUE}-----------检查当前 Gunicorn 进程----------------${NC}"

# 查找 Gunicorn 主进程
PIDS=$(ps -ef | grep "gunicorn.*${APP_NAME}" | grep -v grep | awk '{print $2}')

if [ -n "$PIDS" ]; then
    echo "找到以下 Gunicorn 进程: $PIDS"
    echo -e '\n-----------------正在关闭进程----------------- '
    echo $PIDS | xargs kill -9
    echo "已终止进程: $PIDS"
else
    echo "未找到运行的 Gunicorn 进程。"
fi

sleep 0.5

echo -e '\n-----------启动新的 Gunicorn 进程-----------'

# 检查日志目录是否存在
LOG_DIR="/var/log/gunicorn"
if [ ! -d "$LOG_DIR" ]; then
    echo "日志目录 $LOG_DIR 不存在，正在尝试创建..."
    sudo mkdir -p "$LOG_DIR"
    sudo chown -R nginx:nginx "$LOG_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}错误: 创建日志目录 $LOG_DIR 失败。请检查权限。${NC}"
        exit 1
    fi
    echo "日志目录创建成功。"
fi

# 进入项目目录
cd /data/git-lims || {
    echo -e "${RED}错误: 无法进入项目目录 /data/git-lims${NC}"
    exit 1
}

# 启动 Gunicorn + Uvicorn
# --workers: 工作进程数，根据您之前的配置设为4
# --worker-class: 指定使用 Uvicorn 作为工作器来处理 ASGI 请求
# --bind: 监听的地址和端口，与您之前的配置保持一致
# --user/--group: 以指定用户和组运行，增强安全性
# --log-file: 日志文件路径
# --daemon: 在后台运行
/envs/git_lims_env/bin/gunicorn ${APP_NAME} \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:9000 \
    --user nginx \
    --group nginx \
    --log-file /var/log/gunicorn/git_lims.log \
    --daemon

# 检查启动是否成功
sleep 2 # 等待一会，让进程有时间启动

NEW_PIDS=$(ps -ef | grep "gunicorn.*${APP_NAME}" | grep -v grep | awk '{print $2}')

if [ -n "$NEW_PIDS" ]; then
    echo -e "\n${GREEN}-------------------------Gunicorn 启动成功!---------------------${NC}"
    echo "进程ID: $NEW_PIDS"
else
    echo -e "\n${RED}-------------------------Gunicorn 启动失败!---------------------${NC}"
    echo "请检查日志文件 /var/log/gunicorn/git_lims.log 获取更多信息。"
    exit 1
fi

