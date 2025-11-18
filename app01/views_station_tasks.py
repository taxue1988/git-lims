"""
工站任务管理 API 视图
提供 HPLC 和 GCMS 任务的 CRUD 操作
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Max
import json

from app01.models import HPLCTask, GCMSTask

# 使用北京时间(UTC+8)格式化创建时间
CN_TZ = timezone.get_fixed_timezone(480)


# ==================== HPLC 任务 API ====================

@login_required
@require_http_methods(["GET"])
def hplc_task_list(request):
    """获取当前用户的 HPLC 任务列表"""
    try:
        tasks = HPLCTask.objects.filter(created_by=request.user).order_by('-created_at')
        
        task_list = []
        for task in tasks:
            task_list.append({
                'id': task.id,
                'displayId': task.display_id,
                'name': task.experiment_name,
                'bottleNum': task.bottle_num,
                'time': timezone.localtime(task.created_at, CN_TZ).strftime('%Y-%m-%d %H:%M'),
                'statusText': task.get_status_display(),
                'status': task.status,
                'duration': task.get_duration_display(),
                'startTime': int(task.start_time.timestamp() * 1000) if task.start_time else None,
                'endTime': int(task.end_time.timestamp() * 1000) if task.end_time else None,
                'archiveId': task.archive_id,
            })
        
        return JsonResponse({
            'success': True,
            'tasks': task_list
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def hplc_task_create(request):
    """创建新的 HPLC 任务"""
    try:
        data = json.loads(request.body)
        experiment_name = data.get('experimentName')
        bottle_num = data.get('bottleNum')
        
        if not experiment_name or bottle_num is None:
            return JsonResponse({
                'success': False,
                'error': '缺少必要参数'
            }, status=400)
        
        # 获取当前用户的最大 display_id
        max_id = HPLCTask.objects.filter(created_by=request.user).aggregate(
            Max('display_id')
        )['display_id__max'] or 0
        
        # 创建任务
        task = HPLCTask.objects.create(
            created_by=request.user,
            display_id=max_id + 1,
            experiment_name=experiment_name,
            bottle_num=bottle_num,
            status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'displayId': task.display_id,
                'name': task.experiment_name,
                'bottleNum': task.bottle_num,
                'time': timezone.localtime(task.created_at, CN_TZ).strftime('%Y-%m-%d %H:%M'),
                'statusText': task.get_status_display(),
                'status': task.status,
                'duration': task.get_duration_display(),
                'startTime': None,
                'endTime': None,
                'archiveId': None,
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def hplc_task_update(request, task_id):
    """更新 HPLC 任务状态"""
    try:
        data = json.loads(request.body)
        
        task = HPLCTask.objects.get(id=task_id, created_by=request.user)
        
        # 更新状态
        if 'status' in data:
            task.status = data['status']
        
        # 更新时间信息
        if 'startTime' in data and data['startTime']:
            task.start_time = timezone.datetime.fromtimestamp(
                data['startTime'] / 1000, tz=timezone.get_current_timezone()
            )
        
        if 'endTime' in data and data['endTime']:
            task.end_time = timezone.datetime.fromtimestamp(
                data['endTime'] / 1000, tz=timezone.get_current_timezone()
            )
            
            # 计算用时
            if task.start_time and task.end_time:
                duration = (task.end_time - task.start_time).total_seconds()
                task.duration_seconds = int(duration)
        
        # 更新归档ID
        if 'archiveId' in data:
            task.archive_id = data['archiveId']
        
        task.save()
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'displayId': task.display_id,
                'name': task.experiment_name,
                'bottleNum': task.bottle_num,
                'time': timezone.localtime(task.created_at, CN_TZ).strftime('%Y-%m-%d %H:%M'),
                'statusText': task.get_status_display(),
                'status': task.status,
                'duration': task.get_duration_display(),
                'startTime': int(task.start_time.timestamp() * 1000) if task.start_time else None,
                'endTime': int(task.end_time.timestamp() * 1000) if task.end_time else None,
                'archiveId': task.archive_id,
            }
        })
    except HPLCTask.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '任务不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def hplc_task_delete(request, task_id):
    """删除 HPLC 任务"""
    try:
        task = HPLCTask.objects.get(id=task_id, created_by=request.user)
        task.delete()
        
        return JsonResponse({
            'success': True,
            'message': '任务已删除'
        })
    except HPLCTask.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '任务不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== GCMS 任务 API ====================

@login_required
@require_http_methods(["GET"])
def gcms_task_list(request):
    """获取当前用户的 GCMS 任务列表"""
    try:
        tasks = GCMSTask.objects.filter(created_by=request.user).order_by('-created_at')
        
        task_list = []
        for task in tasks:
            task_list.append({
                'id': task.id,
                'displayId': task.display_id,
                'name': task.experiment_name,
                'bottleNum': task.bottle_num,
                'sequenceIndex': task.sequence_index,
                'sequenceName': task.sequence_name or '',
                'time': timezone.localtime(task.created_at, CN_TZ).strftime('%Y-%m-%d %H:%M'),
                'statusText': task.get_status_display(),
                'status': task.status,
                'duration': task.get_duration_display(),
                'startTime': int(task.start_time.timestamp() * 1000) if task.start_time else None,
                'endTime': int(task.end_time.timestamp() * 1000) if task.end_time else None,
                'archiveId': task.archive_id,
            })
        
        return JsonResponse({
            'success': True,
            'tasks': task_list
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def gcms_task_create(request):
    """创建新的 GCMS 任务"""
    try:
        data = json.loads(request.body)
        experiment_name = data.get('experimentName')
        bottle_num = data.get('bottleNum')
        sequence_index = data.get('sequenceIndex')
        sequence_name = data.get('sequenceName', '')
        
        if not experiment_name or bottle_num is None or sequence_index is None:
            return JsonResponse({
                'success': False,
                'error': '缺少必要参数'
            }, status=400)
        
        # 获取当前用户的最大 display_id
        max_id = GCMSTask.objects.filter(created_by=request.user).aggregate(
            Max('display_id')
        )['display_id__max'] or 0
        
        # 创建任务
        task = GCMSTask.objects.create(
            created_by=request.user,
            display_id=max_id + 1,
            experiment_name=experiment_name,
            bottle_num=bottle_num,
            sequence_index=sequence_index,
            sequence_name=sequence_name,
            status='pending'
        )
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'displayId': task.display_id,
                'name': task.experiment_name,
                'bottleNum': task.bottle_num,
                'sequenceIndex': task.sequence_index,
                'sequenceName': task.sequence_name or '',
                'time': timezone.localtime(task.created_at, CN_TZ).strftime('%Y-%m-%d %H:%M'),
                'statusText': task.get_status_display(),
                'status': task.status,
                'duration': task.get_duration_display(),
                'startTime': None,
                'endTime': None,
                'archiveId': None,
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def gcms_task_update(request, task_id):
    """更新 GCMS 任务状态"""
    try:
        data = json.loads(request.body)
        
        task = GCMSTask.objects.get(id=task_id, created_by=request.user)
        
        # 更新状态
        if 'status' in data:
            task.status = data['status']
        
        # 更新序列名称
        if 'sequenceName' in data:
            task.sequence_name = data['sequenceName']
        
        # 更新时间信息
        if 'startTime' in data and data['startTime']:
            task.start_time = timezone.datetime.fromtimestamp(
                data['startTime'] / 1000, tz=timezone.get_current_timezone()
            )
        
        if 'endTime' in data and data['endTime']:
            task.end_time = timezone.datetime.fromtimestamp(
                data['endTime'] / 1000, tz=timezone.get_current_timezone()
            )
            
            # 计算用时
            if task.start_time and task.end_time:
                duration = (task.end_time - task.start_time).total_seconds()
                task.duration_seconds = int(duration)
        
        # 更新归档ID
        if 'archiveId' in data:
            task.archive_id = data['archiveId']
        
        task.save()
        
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'displayId': task.display_id,
                'name': task.experiment_name,
                'bottleNum': task.bottle_num,
                'sequenceIndex': task.sequence_index,
                'sequenceName': task.sequence_name or '',
                'time': timezone.localtime(task.created_at, CN_TZ).strftime('%Y-%m-%d %H:%M'),
                'statusText': task.get_status_display(),
                'status': task.status,
                'duration': task.get_duration_display(),
                'startTime': int(task.start_time.timestamp() * 1000) if task.start_time else None,
                'endTime': int(task.end_time.timestamp() * 1000) if task.end_time else None,
                'archiveId': task.archive_id,
            }
        })
    except GCMSTask.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '任务不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
@require_http_methods(["DELETE"])
def gcms_task_delete(request, task_id):
    """删除 GCMS 任务"""
    try:
        task = GCMSTask.objects.get(id=task_id, created_by=request.user)
        task.delete()
        
        return JsonResponse({
            'success': True,
            'message': '任务已删除'
        })
    except GCMSTask.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '任务不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

