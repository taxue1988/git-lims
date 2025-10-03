#!/usr/bin/env bash

# 停止uWSGI进程部分
echo -e "\033[34m-----------wsgi process----------------\033[0m"

ps -ef|grep git_lims_uwsgi.ini | grep -v grep

sleep 0.5

echo -e '\n-----------------going to close----------------- '

ps -ef|grep git_lims_uwsgi.ini | grep -v grep | awk '{print $2}' | xargs kill -9

sleep 0.5

# 启动uWSGI进程部分
echo -e '\n-----------check if the kill action is correct-----------'

/envs/git_lims_env/bin/uwsgi --ini git_lims_uwsgi.ini & >/dev/null

echo -e '\n\033[42;1m-------------------------started...---------------------\033[0m'

sleep 1

ps -ef |grep git_lims_uwsgi.ini | grep -v grep