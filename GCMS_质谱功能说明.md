# GCMS 色谱图和质谱图同时显示功能说明

## 功能概述

本功能实现了在 GCMS 分析结果页面同时显示色谱图（TIC）和质谱图（MS）的功能。用户可以：

1. 查看色谱图（TIC - 总离子流色谱）
2. 通过输入保留时间来加载对应的质谱图
3. 导出色谱图和质谱图为 PNG 格式

## 系统架构

### 后端组件

#### 1. `ms_converter.py` - 质谱数据处理模块

位置：`station_workers/GCMS液相/ms_converter.py`

主要类：
- **MSConverter**: 将 .D 文件夹转换为 mzML 格式
- **MSDataExtractor**: 从 mzML 文件中提取质谱数据
- **MSPlotter**: 准备质谱图数据用于前端显示
- **GCMSDataProcessor**: 整合转换和提取功能的主处理器

关键方法：
```python
# 处理数据文件夹并转换为 mzML
success, mzml_path, error = processor.process_data_folder(data_folder)

# 获取指定保留时间的质谱数据
spectrum_data = processor.get_mass_spectrum_at_retention_time(rt)
```

#### 2. `gcms_worker.py` - Worker 进程修改

新增功能：
- 初始化 `GCMSDataProcessor` 实例
- 添加 `handle_get_mass_spectrum()` 方法处理质谱请求
- 在 `on_message()` 中添加 `get_mass_spectrum_` 指令处理

工作流程：
1. 接收前端的 `get_mass_spectrum_{sequence_index}_{retention_time}` 指令
2. 根据序列号找到对应的数据文件夹
3. 将 .D 文件夹转换为 mzML 格式（首次转换时）
4. 从 mzML 中提取指定保留时间的质谱数据
5. 返回 m/z 和强度数据给前端

### 前端组件

#### 1. `GCMS.html` - 前端界面修改

新增 UI 元素：
- 色谱图显示区域（保留原有功能）
- 质谱图显示区域
- 保留时间输入框
- "加载质谱图"按钮
- 导出质谱图 PNG 按钮

新增 JavaScript 函数：
- `renderMassSpectrumChart()`: 渲染质谱图表
- 质谱图数据处理逻辑

## 数据流程

### 色谱图加载流程

```
用户点击"查看结果"
    ↓
发送 get_result_{bottle}_{sequence} 指令
    ↓
Worker 读取 tic_front.csv
    ↓
返回 x（时间）和 y（强度）数据
    ↓
前端渲染色谱图
```

### 质谱图加载流程

```
用户输入保留时间并点击"加载质谱图"
    ↓
发送 get_mass_spectrum_{sequence}_{retention_time} 指令
    ↓
Worker 检查是否已转换该序列的 mzML 文件
    ↓
若未转换，调用 msconvert 将 .D 文件夹转换为 mzML
    ↓
使用 pymzml 库读取 mzML 文件
    ↓
根据保留时间找到最接近的光谱
    ↓
提取 m/z 和强度数据
    ↓
返回数据给前端
    ↓
前端渲染质谱图（柱状图）
```

## 依赖要求

### Python 依赖

```bash
pip install pymzml websocket-client
```

### 系统依赖

- **ProteoWizard**: 用于 .D 文件转换为 mzML
  - 下载地址: http://proteowizard.sourceforge.net/
  - 安装后确保 `msconvert.exe` 在以下路径之一：
    - `C:\Program Files\ProteoWizard\ProteoWizard 3.0.25323.6de0b61\msconvert.exe`
    - `C:\Program Files\ProteoWizard\msconvert.exe`
    - `C:\Program Files (x86)\ProteoWizard\msconvert.exe`

## 使用说明

### 1. 启动 Worker

```bash
cd station_workers/GCMS液相
python gcms_worker.py
```

### 2. 在网页上使用

1. 创建 GCMS 分析任务
2. 运行任务
3. 任务完成后，点击"查看结果"按钮
4. 色谱图会自动加载显示
5. 在"质谱图"区域输入保留时间（单位：分钟）
6. 点击"加载质谱图"按钮
7. 质谱图会加载并显示

### 3. 导出图表

- 点击"导出色谱图 PNG"导出色谱图
- 点击"导出质谱图 PNG"导出质谱图

## 技术细节

### 保留时间匹配

质谱数据提取器使用以下策略查找保留时间：

1. 从 mzML 文件中加载所有光谱及其保留时间
2. 当用户输入保留时间时，查找最接近的光谱
3. 默认容差为 0.01 分钟（可调整）
4. 若未找到，返回错误消息

### 数据降采样

为了提高前端性能，质谱数据会进行降采样：

- 若数据点数超过 1000 个，进行等距采样
- 保留原始数据的分布特征

### 缓存机制

- 转换后的 mzML 文件存储在临时目录
- 同一序列的多次查询会重用已转换的 mzML 文件
- 减少重复转换的时间开销

## 故障排除

### 问题 1: "msconvert.exe 未找到"

**解决方案**:
1. 确保已安装 ProteoWizard
2. 检查安装路径是否在 `ms_converter.py` 的 `MSCONVERT_PATHS` 列表中
3. 可以在初始化时指定自定义路径：
   ```python
   processor = GCMSDataProcessor()
   processor.converter.msconvert_path = r"C:\path\to\msconvert.exe"
   ```

### 问题 2: "未找到质谱数据"

**可能原因**:
- 输入的保留时间超出数据范围
- mzML 转换失败
- 数据文件夹路径不正确

**解决方案**:
1. 检查色谱图的时间范围，确保输入的保留时间在范围内
2. 查看 Worker 日志确认 mzML 转换是否成功
3. 验证 `GCMS序列及参数表.csv` 中的数据路径配置

### 问题 3: "质谱图加载缓慢"

**可能原因**:
- 首次加载需要进行 mzML 转换（可能需要几分钟）
- 数据文件过大

**解决方案**:
- 等待首次转换完成，后续查询会更快
- 检查系统磁盘空间是否充足

## 扩展建议

1. **保留时间自动建议**: 在色谱图上添加点击事件，自动填充保留时间
2. **多光谱对比**: 支持同时显示多个保留时间的质谱图进行对比
3. **数据导出**: 支持导出质谱数据为 CSV 或其他格式
4. **峰值识别**: 自动识别质谱中的主要峰值并标注

## 参考资源

- [pymzml 文档](https://pymzml.readthedocs.io/)
- [ProteoWizard 文档](http://proteowizard.sourceforge.net/)
- [mzML 格式规范](https://www.psidev.info/mzML)

