# GCMS 和 HPLC 工站任务数据库集成说明

## 已完成的工作

### 1. 数据库模型 ✅
- 创建了 `HPLCTask` 模型（app01/models.py）
- 创建了 `GCMSTask` 模型（app01/models.py）
- 包含所有必要字段：用户关联、任务信息、状态、时间、归档ID等

### 2. API 视图 ✅
- 创建了 `app01/views_station_tasks.py`
- 实现了以下 API 端点：
  - HPLC 任务：列表、创建、更新、删除
  - GCMS 任务：列表、创建、更新、删除

### 3. URL 路由 ✅
- 在 `lims/urls.py` 中添加了所有 API 路由
- HPLC: `/api/hplc/tasks/`
- GCMS: `/api/gcms/tasks/`

### 4. HPLC.html 前端修改 ✅
- 替换 localStorage 为 API 调用
- 添加了 `loadTasksFromServer()` 函数
- 添加了 `updateTaskOnServer()` 函数
- 修改了创建、删除、运行任务的函数
- 在 WebSocket 消息处理中添加数据库更新

## 需要完成的工作

### 5. GCMS.html 前端修改 (进行中)

需要在 GCMS.html 中进行类似 HPLC.html 的修改：

#### a. 修改 saveTaskBtn 事件监听器
```javascript
saveTaskBtn.addEventListener('click', async () => {
    const experimentName = document.getElementById('experimentName').value.trim();
    const bottleNum = document.getElementById('bottleNum').value;
    const sequenceIndex = document.getElementById('sequenceIndex').value;
    const sequenceName = sequenceMap[String(sequenceIndex)] || '';
    
    if (!experimentName || bottleNum === '' || sequenceIndex === '') {
        alert('请填写所有字段');
        return;
    }
    
    try {
        const response = await fetch('/api/gcms/tasks/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                experimentName: experimentName,
                bottleNum: parseInt(bottleNum),
                sequenceIndex: parseInt(sequenceIndex),
                sequenceName: sequenceName
            })
        });

        if (!response.ok) {
            throw new Error('创建任务失败');
        }

        const data = await response.json();
        if (data.success) {
            const task = data.task;
            const newTask = {
                id: `task-${task.id}`,
                dbId: task.id,
                displayId: task.displayId,
                name: task.name,
                bottleNum: task.bottleNum,
                sequenceIndex: task.sequenceIndex,
                sequenceName: task.sequenceName || '',
                time: task.time,
                statusText: task.statusText,
                statusClass: getStatusClass(task.status),
                runButtonHTML: getRunButtonHTML(task.status),
                runButtonDisabled: shouldDisableRunButton(task.status),
                startTime: null,
                endTime: null,
                duration: '',
                archiveId: null
            };
            tasks.push(newTask);
            taskIdCounter = Math.max(taskIdCounter, task.displayId);
            renderTasks();
            createTaskForm.reset();
            createTaskModal.hide();
            addLog('任务创建成功', 'success');
        } else {
            alert('创建任务失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('创建任务失败:', error);
        alert('创建任务失败: ' + error.message);
    }
});
```

#### b. 修改 handleRunTask 函数
```javascript
window.handleRunTask = async function(taskId) {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;

    task.statusText = '排队中';
    task.statusClass = 'bg-primary';
    task.runButtonHTML = '<i class="fas fa-clock"></i> 排队中';
    task.runButtonDisabled = true;
    renderTasks();
    
    // 更新数据库状态
    await updateTaskOnServer(task.dbId, { status: 'queued' });
    
    runNextTaskInQueue();
}
```

#### c. 修改 handleDeleteTask 函数
```javascript
window.handleDeleteTask = async function(taskId) {
    if (!confirm('您确定要删除这个任务吗？')) return;
    
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;
    
    try {
        const response = await fetch(`/api/gcms/tasks/${task.dbId}/delete/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error('删除任务失败');
        }
        
        const data = await response.json();
        if (data.success) {
            const isRunning = !['待运行', '排队中', '已完成', '失败'].includes(task.statusText);
            tasks = tasks.filter(t => t.id !== taskId);
            renderTasks();
            addLog(`删除了任务: ${task.name} (瓶号: ${task.bottleNum})`, 'info');

            if (isRunning) {
                isWorkerBusy = false;
                updatePositionStatus('idle');
                stopTotalRuntime();
                sendMessage('force_stop');
                addLog('由于删除了正在运行的任务，已重置工位状态。', 'warning');
            }
        } else {
            alert('删除任务失败: ' + (data.error || '未知错误'));
        }
    } catch (error) {
        console.error('删除任务失败:', error);
        alert('删除任务失败: ' + error.message);
    }
}
```

#### d. 修改 WebSocket 消息处理中的状态更新

在 `socket.onmessage` 函数中，为每个 case 添加数据库更新：

```javascript
case 'analysis_started':
    if (task) {
        task.statusText = '任务开始';
        task.statusClass = 'bg-info';
        task.startTime = Date.now();
        // 更新数据库
        updateTaskOnServer(task.dbId, {
            status: 'task_started',
            startTime: task.startTime
        });
    }
    updatePositionStatus('running');
    startTotalRuntime();
    break;

case 'analysis_progress':
    if (task) {
        task.statusText = message.stage;
        task.statusClass = 'bg-info text-dark';
        // 更新数据库状态
        const statusMap = {
            '设备准备': 'device_preparation',
            '机械臂操作': 'arm_operation',
            '仪器分析': 'instrument_analysis',
            '等待分析完成': 'waiting_completion',
            '设备复位': 'device_reset'
        };
        const dbStatus = statusMap[message.stage] || 'task_started';
        updateTaskOnServer(task.dbId, { status: dbStatus });
    }
    updatePositionStatus('running');
    break;

case 'analysis_complete':
    if (task) {
        task.statusText = '已完成';
        task.statusClass = 'bg-success';
        task.runButtonHTML = '<i class="fas fa-redo"></i> 重新运行';
        task.runButtonDisabled = false;
        task.endTime = Date.now();
        if (message.archive_id){
            task.archiveId = message.archive_id;
        }
        if (task.startTime) {
            const durationSeconds = Math.round((task.endTime - task.startTime) / 1000);
            const minutes = Math.floor(durationSeconds / 60);
            const seconds = durationSeconds % 60;
            task.duration = `${minutes}分${seconds}秒`;
        }
        // 更新数据库
        updateTaskOnServer(task.dbId, {
            status: 'completed',
            endTime: task.endTime,
            archiveId: task.archiveId
        });
    }
    isWorkerBusy = false;
    updatePositionStatus('complete');
    runNextTaskInQueue();
    stopTotalRuntime();
    break;

case 'analysis_error':
    if (task) {
        task.statusText = '失败';
        task.statusClass = 'bg-danger';
        task.runButtonHTML = '<i class="fas fa-redo"></i> 重试';
        task.runButtonDisabled = false;
        task.endTime = Date.now();
        if (task.startTime) {
            const durationSeconds = Math.round((task.endTime - task.startTime) / 1000);
            const minutes = Math.floor(durationSeconds / 60);
            const seconds = durationSeconds % 60;
            task.duration = `${minutes}分${seconds}秒`;
        }
        // 更新数据库
        updateTaskOnServer(task.dbId, {
            status: 'failed',
            endTime: task.endTime
        });
    }
    isWorkerBusy = false;
    updatePositionStatus('error');
    runNextTaskInQueue();
    stopTotalRuntime();
    break;
```

### 6. 数据库迁移

在完成所有代码修改后，需要运行数据库迁移：

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Worker 修改（可选但推荐）

虽然前端已经在接收 WebSocket 消息时更新数据库，但为了更可靠，建议在 Worker 中也直接更新数据库。

#### hplc_worker.py 修改示例：

在文件开头添加导入：
```python
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lims.settings')
django.setup()

from app01.models import HPLCTask
```

在 `handle_start_analysis` 方法中添加数据库更新：
```python
def handle_start_analysis(self, bottle_num):
    def worker():
        try:
            # 查找对应的任务
            task = HPLCTask.objects.filter(
                bottle_num=bottle_num,
                status__in=['pending', 'queued']
            ).order_by('-created_at').first()
            
            if task:
                task.status = 'task_started'
                task.start_time = timezone.now()
                task.save()
            
            # ... 原有代码 ...
            
            if task:
                task.status = 'completed'
                task.end_time = timezone.now()
                if task.start_time:
                    duration = (task.end_time - task.start_time).total_seconds()
                    task.duration_seconds = int(duration)
                task.archive_id = archive_id
                task.save()
        except Exception as e:
            if task:
                task.status = 'failed'
                task.end_time = timezone.now()
                task.save()
```

#### gcms_worker.py 类似修改

## 测试步骤

1. **启动服务器**
   ```bash
   python manage.py runserver
   ```

2. **启动 Worker**
   ```bash
   python station_workers/HPLC液相/hplc_worker.py
   python station_workers/GCMS液相/gcms_worker.py
   ```

3. **测试流程**
   - 在浏览器 A 中登录并创建任务
   - 在浏览器 B 中登录同一账号
   - 验证浏览器 B 能看到浏览器 A 创建的任务
   - 在浏览器 A 中运行任务
   - 验证浏览器 B 能实时看到任务状态更新
   - 刷新页面，验证任务数据持久化

## 优势

✅ **跨浏览器同步**：任何浏览器登录同一账号都能看到相同的任务
✅ **数据持久化**：任务数据保存在数据库中，不会因清除缓存而丢失
✅ **多用户支持**：每个用户只能看到自己的任务
✅ **实时更新**：通过 WebSocket 和 API 实现实时状态同步
✅ **数据安全**：数据存储在服务器端，更加安全可靠

## 注意事项

1. 确保在修改前备份原文件
2. 测试时注意检查浏览器控制台是否有错误
3. 确保 CSRF token 正确配置（已在视图中使用 @csrf_exempt）
4. 如果使用 HTTPS，确保 WebSocket 使用 WSS 协议

