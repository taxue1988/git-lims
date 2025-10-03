#!/usr/bin/env bash

# 设置颜色代码
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}-----------检查当前uWSGI进程----------------${NC}"

# 获取进程ID
PIDS=$(ps -ef | grep git_lims_uwsgi.ini | grep -v grep | awk '{print $2}')

if [ -n "$PIDS" ]; then
    echo "找到以下uWSGI进程: $PIDS"
    echo -e '\n-----------------正在关闭进程----------------- '
    echo $PIDS | xargs kill -9
    echo "已终止进程: $PIDS"
else
    echo "未找到运行的uWSGI进程。"
fi

sleep 0.5

echo -e '\n-----------启动新的uWSGI进程-----------'

# 检查uWSGI配置文件是否存在
if [ ! -f "git_lims_uwsgi.ini" ]; then
    echo -e "${RED}错误: 找不到uWSGI配置文件 git_lims_uwsgi.ini${NC}"
    exit 1
fi

# 检查日志目录是否存在
if [ ! -d "/var/log/uwsgi" ]; then
    echo -e "${RED}错误: 日志目录 /var/log/uwsgi 不存在${NC}"
    echo "请运行: sudo mkdir -p /var/log/uwsgi && sudo chmod -R 755 /var/log/uwsgi"
    exit 1
fi

# 启动uWSGI
/envs/git_lims_env/bin/uwsgi --ini git_lims_uwsgi.ini

# 检查启动是否成功
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}-------------------------uWSGI启动成功!---------------------${NC}"
else
    echo -e "\n${RED}-------------------------uWSGI启动失败!---------------------${NC}"
    echo "请检查配置文件和日志获取更多信息。"
    exit 1
fi

sleep 1

echo -e "\n${BLUE}-----------检查新的uWSGI进程----------------${NC}"
ps -ef | grep git_lims_uwsgi.ini | grep -v grep