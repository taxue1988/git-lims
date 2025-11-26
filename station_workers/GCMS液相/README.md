# GCMS Worker 使用说明与变更记录

## 目的
让同事电脑运行的 `gcms_worker.py` 能直接连接部署在服务器的 WebSocket 服务，从而在网页端（服务器域名/IP）查看仪器状态并下发任务。

## 关键改动
文件：`station_workers/gcms_worker.py`

- 支持通过命令行参数或环境变量配置 WebSocket 服务器地址：
  - 命令行参数：`-s` 或 `--server-url`
  - 环境变量：`GCMS_SERVER_URL`
- 默认地址改为公网（非 TLS）：`ws://62.234.51.178/ws/gcms/`

示例：

```bash
# 方式一：命令行参数
python gcms_worker.py -s ws://62.234.51.178/ws/gcms/

# 方式二：环境变量
set GCMS_SERVER_URL=ws://62.234.51.178/ws/gcms/
python gcms_worker.py
```

> 注意：如果服务器以 HTTPS 提供网页，建议将地址改为 `wss://62.234.51.178/ws/gcms/`，并在反向代理(Nginx)正确配置 WebSocket 升级头。

## 部署/联通要点
1. 服务器端必须开放 80/443（或你自定义端口）并正确反代 `/ws/gcms/`（WebSocket）。
2. Django/Channels 需要在 `ALLOWED_HOSTS` 中加入服务器域名/IP，并在反代层透传 `Upgrade`/`Connection` 头。
3. 前端页面里使用：`new WebSocket('ws://' + window.location.host + '/ws/gcms/');`，上线时若是 HTTPS，需要改为 `wss://`（或按域名自动拼接）。

## 变更记录
- [当前] 新增 `GCMS_SERVER_URL` 环境变量与 `--server-url` 参数；默认指向公网地址。


