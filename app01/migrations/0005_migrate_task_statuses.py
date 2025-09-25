from django.db import migrations

def migrate_task_statuses(apps, schema_editor):
    """
    将旧的状态值转换为新的状态值
    """
    Task = apps.get_model('app01', 'Task')
    
    # 状态映射：旧状态 -> 新状态
    status_mapping = {
        '未提交': 'draft',
        '待审核': 'pending',
        '已通过': 'approved',
        '已排程': 'scheduled',
        '已下发': 'scheduled',  # 已下发合并到已排程
        '进行中': 'in_progress',
        '已完成': 'completed',
        '已驳回': 'rejected',
        '已取消': 'cancelled',
    }
    
    # 批量更新状态
    for old_status, new_status in status_mapping.items():
        Task.objects.filter(status=old_status).update(status=new_status)

def reverse_migrate_task_statuses(apps, schema_editor):
    """
    反向迁移：将新状态值转换回旧状态值
    """
    Task = apps.get_model('app01', 'Task')
    
    # 反向状态映射
    reverse_status_mapping = {
        'draft': '未提交',
        'pending': '待审核',
        'approved': '已通过',
        'scheduled': '已排程',
        'in_progress': '进行中',
        'completed': '已完成',
        'rejected': '已驳回',
        'cancelled': '已取消',
    }
    
    # 批量更新状态
    for new_status, old_status in reverse_status_mapping.items():
        Task.objects.filter(status=new_status).update(status=old_status)


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0004_taskstatuslog_alter_task_status_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_task_statuses, reverse_migrate_task_statuses),
    ]
