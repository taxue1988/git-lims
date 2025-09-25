from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('app01', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_id', models.CharField(blank=True, db_index=True, max_length=64, null=True, verbose_name='客户端任务ID')),
                ('name', models.CharField(max_length=255, verbose_name='实验名称')),
                ('date', models.CharField(blank=True, max_length=32, null=True, verbose_name='实验时间')),
                ('status', models.CharField(choices=[('未提交', '未提交'), ('待审核', '待审核'), ('已通过', '已通过'), ('已排程', '已排程'), ('已下发', '已下发'), ('进行中', '进行中'), ('已完成', '已完成'), ('已驳回', '已驳回'), ('已取消', '已取消')], default='待审核', max_length=10, verbose_name='状态')),
                ('source', models.CharField(default='服务器', max_length=32, verbose_name='来源')),
                ('remark', models.TextField(blank=True, null=True, verbose_name='备注')),
                ('stations', models.JSONField(blank=True, null=True, verbose_name='工站参数')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to=settings.AUTH_USER_MODEL, verbose_name='提交人')),
            ],
            options={
                'verbose_name': '实验任务',
                'verbose_name_plural': '实验任务',
                'db_table': 'task',
            },
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['created_by', 'client_id'], name='app01_task_created__da85e8_idx'),
        ),
        migrations.AddConstraint(
            model_name='task',
            constraint=models.UniqueConstraint(condition=models.Q(('client_id__isnull', False)), fields=('created_by', 'client_id'), name='uniq_user_client_task'),
        ),
    ]


