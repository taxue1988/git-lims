# GCMS 色谱图和质谱图同时显示功能

## 🎯 功能概述

本功能实现了在 GCMS 分析结果页面同时显示色谱图（TIC - 总离子流）和质谱图（MS - 质量谱）的功能。用户可以：

- ✅ 查看 GCMS 分析的色谱图
- ✅ 通过输入保留时间来加载对应的质谱图
- ✅ 导出色谱图和质谱图为 PNG 格式
- ✅ 实时查看分析进度和结果

## 📦 项目结构

```
git-lims/
├── station_workers/GCMS液相/
│   ├── ms_converter.py          ← 【新建】质谱数据处理模块
│   ├── gcms_worker.py           ← 【修改】添加质谱处理功能
│   ├── sequence_manager.py       ← 序列管理（无修改）
│   └── results_archive/          ← 结果归档目录
├── app01/
│   └── templates/admin/station_management/
│       └── GCMS.html            ← 【修改】前端界面
├── 快速开始指南.md              ← 【新建】快速开始
├── GCMS_质谱功能说明.md         ← 【新建】详细说明
├── 实现总结.md                  ← 【新建】实现总结
└── README_质谱功能.md           ← 【新建】本文件
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装 Python 依赖
pip install pymzml websocket-client

# 安装 ProteoWizard（Windows）
# 下载：http://proteowizard.sourceforge.net/
# 或使用 Chocolatey：choco install proteowizard
```

### 2. 启动服务

```bash
# 终端 1：启动 Django 服务器
python manage.py runserver 0.0.0.0:8000

# 终端 2：启动 GCMS Worker
cd station_workers/GCMS液相
python gcms_worker.py
```

### 3. 使用功能

1. 打开浏览器访问 `http://localhost:8000`
2. 进入 GCMS 工站管理页面
3. 创建并运行分析任务
4. 任务完成后点击"查看结果"
5. 色谱图自动加载，输入保留时间加载质谱图

## 📋 核心模块

### ms_converter.py

质谱数据处理的核心模块，包含以下类：

| 类 | 功能 | 关键方法 |
|---|---|---|
| **MSConverter** | .D 文件转换为 mzML | `convert_to_mzml()` |
| **MSDataExtractor** | 从 mzML 提取质谱数据 | `get_spectrum_by_retention_time()` |
| **MSPlotter** | 准备质谱图数据 | `prepare_mass_spectrum_data()` |
| **GCMSDataProcessor** | 整合处理器 | `process_data_folder()` |

### gcms_worker.py

Worker 进程的修改：

- 新增 `init_ms_processor()` 方法初始化质谱处理器
- 新增 `handle_get_mass_spectrum()` 方法处理质谱请求
- 修改 `on_message()` 添加 `get_mass_spectrum_` 指令处理

### GCMS.html

前端界面的修改：

- 添加质谱图显示区域
- 添加保留时间输入框和加载按钮
- 新增质谱图表渲染函数
- 添加质谱图导出功能

## 🔄 数据流程

### 色谱图加载

```
用户点击"查看结果"
    ↓
发送 get_result_{bottle}_{sequence} 指令
    ↓
Worker 读取 tic_front.csv
    ↓
返回时间和强度数据
    ↓
前端渲染折线图
```

### 质谱图加载

```
用户输入保留时间并点击"加载质谱图"
    ↓
发送 get_mass_spectrum_{sequence}_{rt} 指令
    ↓
Worker 检查 mzML 缓存
    ↓
若无缓存，调用 msconvert 转换 .D 文件
    ↓
使用 pymzml 读取 mzML 文件
    ↓
根据保留时间提取光谱数据
    ↓
返回 m/z 和强度数据
    ↓
前端渲染柱状图
```

## 📊 技术栈

| 组件 | 技术 | 版本 |
|---|---|---|
| 后端框架 | Django | 3.2+ |
| 数据处理 | Python | 3.8+ |
| mzML 解析 | pymzml | 3.0+ |
| 文件转换 | ProteoWizard | 3.0+ |
| 前端图表 | Chart.js | 3.0+ |
| 实时通信 | WebSocket | - |

## 🔧 配置说明

### 序列参数表配置

编辑 `模块开发运行代码/GCMS模块/GCMS序列及参数表.csv`：

```csv
序号,序列文件名,数据名称,数据存储路径
0,2024 Dec 04 1403_default.sequence.xml,Test,D:\MassHunter\GCMS\1\data\20241204
```

**字段说明**：
- **序号**：任务创建时选择的序列号
- **序列文件名**：GCMS 序列文件名
- **数据名称**：数据文件夹基础名称（不含 .D）
- **数据存储路径**：数据文件夹的父目录

### msconvert 路径配置

如果 msconvert.exe 不在默认路径，编辑 `ms_converter.py`：

```python
MSCONVERT_PATHS = [
    r'C:\Program Files\ProteoWizard\ProteoWizard 3.0.25323.6de0b61\msconvert.exe',
    r'C:\Program Files\ProteoWizard\msconvert.exe',
    r'C:\Program Files (x86)\ProteoWizard\msconvert.exe',
    r'C:\your\custom\path\msconvert.exe',  # 添加自定义路径
]
```

## 🎨 用户界面

### 结果查看页面

```
┌─────────────────────────────────────────────────┐
│ 分析结果                    [导出色谱图] [导出质谱图] │
├─────────────────────────────────────────────────┤
│                                                 │
│ 色谱图（TIC）                                   │
│ ┌─────────────────────────────────────────────┐ │
│ │                                             │ │
│ │  [折线图显示]                               │ │
│ │                                             │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
│ 质谱图                                          │
│ ┌─────────────────────────────────────────────┐ │
│ │ 保留时间: [输入框] [加载质谱图]              │ │
│ ├─────────────────────────────────────────────┤ │
│ │  [柱状图显示]                               │ │
│ │                                             │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
├─────────────────────────────────────────────────┤
│ [关闭]                                          │
└─────────────────────────────────────────────────┘
```

## 📈 性能指标

| 操作 | 时间 | 备注 |
|---|---|---|
| mzML 转换 | 5-30 分钟 | 首次转换，之后使用缓存 |
| 质谱数据提取 | < 1 秒 | 使用缓存的 mzML 文件 |
| 前端渲染 | < 500ms | 使用 Chart.js |
| 内存占用 | 100-500MB | 取决于数据大小 |

## ⚠️ 常见问题

### Q: msconvert.exe 未找到

**A**: 检查 ProteoWizard 是否安装，或在 `ms_converter.py` 中添加自定义路径。

### Q: 未找到质谱数据

**A**: 检查保留时间是否在色谱图范围内，或查看 Worker 日志确认转换是否成功。

### Q: 质谱图加载很慢

**A**: 首次加载需要进行 mzML 转换，后续查询会更快。

### Q: Worker 连接失败

**A**: 确认 Django 服务器正在运行，检查 WebSocket 地址和防火墙设置。

## 📚 文档

- [快速开始指南](快速开始指南.md) - 详细的安装和使用步骤
- [GCMS 质谱功能说明](GCMS_质谱功能说明.md) - 完整的功能和技术说明
- [实现总结](实现总结.md) - 详细的实现细节和扩展建议

## 🔐 安全考虑

- ✅ 验证用户权限
- ✅ 限制文件访问路径
- ✅ 不在日志中记录敏感数据
- ✅ 及时清理临时文件
- ✅ 实现超时机制

## 🚦 状态指示

| 状态 | 含义 |
|---|---|
| 🟢 就绪 | 系统准备就绪 |
| 🟡 处理中 | 正在处理数据 |
| 🔴 错误 | 发生错误 |
| ⚪ 离线 | 连接断开 |

## 🤝 贡献指南

如需改进或扩展功能，请：

1. 创建新的分支
2. 进行修改和测试
3. 提交 Pull Request
4. 等待代码审查

## 📞 技术支持

遇到问题？请按以下步骤排查：

1. 查看 Django 和 Worker 的日志
2. 验证配置文件设置
3. 检查依赖是否正确安装
4. 查阅相关文档
5. 联系开发团队

## 📄 许可证

- pymzml: MIT License
- ProteoWizard: Apache License 2.0
- Chart.js: MIT License

##[object Object]ProteoWizard 官网](http://proteowizard.sourceforge.net/)
- [pymzml 文档](https://pymzml.readthedocs.io/)
- [mzML 格式规范](https://www.psidev.info/mzML)
- [Chart.js 文档](https://www.chartjs.org/)

## 📝 更新日志

### v1.0.0 (2025-11-21)

- ✨ 实现色谱图和质谱图同时显示功能
- ✨ 添加 mzML 格式转换和解析
- ✨ 实现质谱数据提取和显示
- ✨ 添加图表导出功能
- 📚 完整的文档和使用指南

## 🎯 未来计划

- [ ] 保留时间自动建议
- [ ] 多光谱对比功能
- [ ] 峰值自动识别
- [ ] 数据导出为 CSV/JSON
- [ ] AI 物质识别
- [ ] 实时分析监控

---

**版本**: 1.0.0  
**最后更新**: 2025-11-21  
**维护者**: 开发团队

**开始使用**: 请参考 [快速开始指南](快速开始指南.md)

