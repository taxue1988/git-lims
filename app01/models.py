# region 导入与基础依赖
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
# endregion


# region 用户与角色(User)
class User(AbstractUser):
    """
    自定义用户模型，支持不同用户角色
    """

    ROLE_CHOICES = (
        ("admin", "管理员"),
        ("preparator", "备料员"),  # 新增
        ("user", "普通用户"),
    )

    role = models.CharField(
        max_length=10, choices=ROLE_CHOICES, default="user", verbose_name="用户角色"
    )
    department = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="部门"
    )
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="电话")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "user"
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def is_admin(self):
        """
        判断用户是否为管理员
        """
        return self.role == "admin" or self.is_superuser

    def is_preparator(self):
        """
        判断用户是否为备料员
        """
        return self.role == "preparator"


# endregion


# region 任务状态枚举(TaskStatus)
class TaskStatus(models.TextChoices):
    """
    实验任务状态枚举
    """

    DRAFT = "draft", "草稿"
    PENDING = "pending", "待审核"
    APPROVED = "approved", "已通过"
    SCHEDULED = "scheduled", "已排程"
    IN_PROGRESS = "in_progress", "进行中"
    COMPLETED = "completed", "已完成"
    REJECTED = "rejected", "已驳回"
    CANCELLED = "cancelled", "已取消"


# endregion


# region 任务状态管理器(TaskStatusManager)
class TaskStatusManager:
    """
    任务状态管理器
    """

    # 状态流转规则
    STATUS_TRANSITIONS = {
        TaskStatus.DRAFT: [TaskStatus.PENDING],
        TaskStatus.PENDING: [TaskStatus.APPROVED, TaskStatus.REJECTED],
        # 审核通过后允许在排程前直接取消
        TaskStatus.APPROVED: [TaskStatus.SCHEDULED, TaskStatus.CANCELLED],
        TaskStatus.SCHEDULED: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
        TaskStatus.IN_PROGRESS: [TaskStatus.COMPLETED, TaskStatus.CANCELLED],
        TaskStatus.COMPLETED: [],
        TaskStatus.REJECTED: [TaskStatus.PENDING],
        TaskStatus.CANCELLED: [],
    }

    @classmethod
    def can_transition(cls, from_status, to_status):
        """
        检查状态转换是否合法
        """
        return to_status in cls.STATUS_TRANSITIONS.get(from_status, [])

    @classmethod
    def get_available_transitions(cls, current_status):
        """
        获取当前状态可用的转换选项
        """
        return cls.STATUS_TRANSITIONS.get(current_status, [])

    @classmethod
    def validate_status(cls, status):
        """
        验证状态值是否有效
        """
        valid_statuses = [choice[0] for choice in TaskStatus.choices]
        if status not in valid_statuses:
            raise ValidationError(f"无效的状态值: {status}")
        return status


# endregion


# region 实验任务(Task)
class Task(models.Model):
    """
    实验任务模型：存储 user_task_management 提交的任务
    """

    # 关联提交用户
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name="提交人",
    )

    # 前端本地任务的ID，用于幂等去重（同一用户下唯一）
    client_id = models.CharField(
        max_length=64, blank=True, null=True, db_index=True, verbose_name="客户端任务ID"
    )

    name = models.CharField(max_length=255, verbose_name="实验名称")
    date = models.CharField(
        max_length=32, blank=True, null=True, verbose_name="实验时间"
    )
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.DRAFT,
        verbose_name="状态",
    )
    remark = models.TextField(blank=True, null=True, verbose_name="备注")

    stations = models.JSONField(blank=True, null=True, verbose_name="工站参数")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "task"
        verbose_name = "实验任务"
        verbose_name_plural = "实验任务"
        indexes = [
            models.Index(fields=["created_by", "client_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["created_by", "client_id"],
                name="uniq_user_client_task",
                condition=models.Q(client_id__isnull=False),
            ),
        ]

    def __str__(self):
        return f"{self.name} - {self.get_status_display()}"

    def can_transition_to(self, new_status):
        """
        检查是否可以转换到指定状态
        """
        return TaskStatusManager.can_transition(self.status, new_status)

    def transition_to(self, new_status, user, reason=None):
        """
        转换到新状态
        """
        if not self.can_transition_to(new_status):
            raise ValidationError(
                f"不允许从 {self.get_status_display()} 转换到 {dict(TaskStatus.choices).get(new_status, new_status)}"
            )

        old_status = self.status
        self.status = new_status
        self.updated_at = timezone.now()
        self.save()

        # 记录状态变更日志
        TaskStatusLog.objects.create(
            task=self,
            from_status=old_status,
            to_status=new_status,
            changed_by=user,
            reason=reason,
        )

        return self

    def get_available_statuses(self):
        """
        获取当前可用的状态转换选项
        """
        return TaskStatusManager.get_available_transitions(self.status)

    def is_editable(self):
        """
        检查任务是否可编辑
        """
        return self.status in [TaskStatus.DRAFT, TaskStatus.REJECTED]

    def is_deletable(self):
        """
        检查任务是否可删除
        """
        return self.status in [TaskStatus.DRAFT, TaskStatus.REJECTED, TaskStatus.CANCELLED]


# endregion


# region 任务状态变更日志(TaskStatusLog)
class TaskStatusLog(models.Model):
    """
    任务状态变更日志
    """

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="status_logs", verbose_name="任务"
    )
    from_status = models.CharField(max_length=20, verbose_name="原状态")
    to_status = models.CharField(max_length=20, verbose_name="新状态")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="变更人"
    )
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="变更时间")
    reason = models.TextField(blank=True, null=True, verbose_name="变更原因")

    class Meta:
        db_table = "task_status_log"
        verbose_name = "任务状态日志"
        verbose_name_plural = "任务状态日志"
        ordering = ["-changed_at"]
        indexes = [
            models.Index(fields=["task", "changed_at"]),
            models.Index(fields=["changed_by", "changed_at"]),
        ]

    def __str__(self):
        return f"{self.task.name}: {self.get_from_status_display()} -> {self.get_to_status_display()}"

    def get_from_status_display(self):
        """获取原状态显示名称"""
        return dict(TaskStatus.choices).get(self.from_status, self.from_status)

    def get_to_status_display(self):
        """获取新状态显示名称"""
        return dict(TaskStatus.choices).get(self.to_status, self.to_status)


# endregion


# region 工站类型与工站模型(StationType, Station)


class StationType(models.TextChoices):
    """工站类型枚举"""

    MANUAL_PREP = "manual_prep", "人工备料"
    SOLID_LIQUID = "solid_liquid", "固液配料"
    REACTION = "reaction", "反应"
    GLOVEBOX = "glovebox", "手套箱固液配料与反应"
    FILTRATION = "filtration", "过滤分液"
    EVAPORATION = "evaporation", "旋蒸"
    COLUMN = "column", "过柱"
    TLC = "tlc", "点板"
    GCMS = "gcms", "GCMS"
    HPLC = "hplc", "HPLC"


class Station(models.Model):
    """
    工站
    """

    name = models.CharField(
        max_length=64, unique=True, db_index=True, verbose_name="工站名"
    )
    station_type = models.CharField(
        max_length=32,
        choices=StationType.choices,
        default=StationType.MANUAL_PREP,
        verbose_name="工站类型",
    )
    desc = models.CharField(max_length=255, blank=True, null=True, verbose_name="描述")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "station"
        verbose_name = "工站"
        verbose_name_plural = "工站"

    def __str__(self):
        return self.name


# endregion

# region 物料类型与转移仓规范(MaterialKind, ContainerSpec)


class MaterialKind(models.TextChoices):
    """
    物料类型（规范层）
    """

    TEST_TUBE_15 = "test_tube_15", "15mL试管"
    LAIYU_POWDER = "laiyu_powder", "铼羽粉筒"
    JINGTAI_POWDER = "jingtai_powder", "晶泰粉筒"
    REAGENT_BTL_150 = "reagent_bottle_150", "150mL试剂瓶"
    TIP_1 = "tip_1", "1mL枪头"
    TIP_5 = "tip_5", "5mL枪头"
    TIP_10 = "tip_10", "10mL枪头"
    SAMPLE_FILTER = "sample_filter", "采样滤头"
    FILTRATION_FILTER = "filtration_filter", "过滤滤头"
    MIXTURE_TUBE = "mixture_tube", "混合瓶"
    SAMPLE_TUBE = "sample_tube", "采样瓶"
    SAMPLE_CYLINDER = "sample_cylinder", "进样柱"
    CHROMATOGRAPHIC_CYL = "chromatographic_cylinder", "色谱柱"


class ContainerSpec(models.Model):
    """
    转移仓类型规范
    """

    class ContainerState(models.TextChoices):
        IDLE = "idle", "空闲"
        IN_USE = "in_use", "使用中"

    name = models.CharField(max_length=64, unique=True, verbose_name="类型名")
    code = models.CharField(max_length=64, unique=True, verbose_name="类型编码")
    capacity = models.PositiveIntegerField(verbose_name="容量/槽位数")
    allowed_material_kind = models.CharField(
        max_length=64, choices=MaterialKind.choices, verbose_name="允许物料类型"
    )
    slot_meta_schema = models.JSONField(
        blank=True, null=True, verbose_name="槽位Meta结构定义"
    )

    class Meta:
        db_table = "container_spec"
        verbose_name = "转移仓类型规范"
        verbose_name_plural = "转移仓类型规范"

    def __str__(self):
        return f"{self.name}({self.code})"


# endregion

# region 转移仓与槽位(Container, ContainerSlot)


class Container(models.Model):
    """
    转移仓实例
    """

    class State(models.TextChoices):
        IDLE = "idle", "空闲"
        IN_USE = "in_use", "使用中"

    name = models.CharField(
        max_length=128, unique=True, db_index=True, verbose_name="唯一名"
    )
    spec = models.ForeignKey(
        ContainerSpec,
        on_delete=models.PROTECT,
        related_name="containers",
        verbose_name="类型",
    )
    state = models.CharField(
        max_length=16, choices=State.choices, default=State.IDLE, verbose_name="状态"
    )
    current_station = models.ForeignKey(
        Station,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="current_containers",
        verbose_name="当前工站",
    )
    target_station = models.ForeignKey(
        Station,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="target_containers",
        verbose_name="目标工站",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "container"
        verbose_name = "转移仓"
        verbose_name_plural = "转移仓"
        indexes = [
            models.Index(fields=["spec", "state"]),
            models.Index(fields=["current_station", "state"]),
        ]

    def __str__(self):
        return self.name


class ContainerSlot(models.Model):
    """
    转移仓槽位
    """

    container = models.ForeignKey(
        Container, on_delete=models.CASCADE, related_name="slots", verbose_name="转移仓"
    )
    index = models.PositiveIntegerField(verbose_name="槽位编号(0-based)")

    # 对有独立物料模型的外键（逻辑上二选一）
    test_tube_15 = models.ForeignKey(
        "TestTube15", on_delete=models.SET_NULL, blank=True, null=True
    )
    laiyu_powder = models.ForeignKey(
        "LaiyuPowder", on_delete=models.SET_NULL, blank=True, null=True
    )
    jingtai_powder = models.ForeignKey(
        "JingtaiPowder", on_delete=models.SET_NULL, blank=True, null=True
    )
    reagent_bottle_150 = models.ForeignKey(
        "ReagentBottle150", on_delete=models.SET_NULL, blank=True, null=True
    )

    # 其它无需独立模型的，由 meta 承载
    meta = models.JSONField(blank=True, null=True, verbose_name="槽位元数据")
    occupied = models.BooleanField(default=False, verbose_name="是否占用")

    class Meta:
        db_table = "container_slot"
        verbose_name = "转移仓槽位"
        verbose_name_plural = "转移仓槽位"
        unique_together = (("container", "index"),)
        indexes = [
            models.Index(fields=["container", "index"]),
            models.Index(fields=["occupied"]),
        ]

    def __str__(self):
        return f"{self.container.name}#{self.index}"


# endregion

# region 物料模型(TestTube15, LaiyuPowder, JingtaiPowder, ReagentBottle150)


class TestTube15(models.Model):
    """
    15mL试管
    """

    class State(models.TextChoices):
        IDLE = "idle", "空闲"
        IN_USE = "in_use", "使用中"

    name = models.CharField(
        max_length=128, unique=True, db_index=True, verbose_name="唯一名"
    )
    task = models.ForeignKey(
        "Task",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="实验任务ID",
    )
    state = models.CharField(
        max_length=16, choices=State.choices, default=State.IDLE, verbose_name="状态"
    )
    current_container = models.ForeignKey(
        "Container",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="当前转移仓",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "test_tube_15"
        verbose_name = "15mL试管"
        verbose_name_plural = "15mL试管"

    def __str__(self):
        return self.name


class LaiyuPowder(models.Model):
    """
    铼羽粉筒
    """

    class State(models.TextChoices):
        IDLE = "idle", "空闲"
        IN_USE = "in_use", "使用中"

    name = models.CharField(
        max_length=128, unique=True, db_index=True, verbose_name="唯一名"
    )
    material_name = models.CharField(max_length=128, verbose_name="粉末名称")
    mass_mg = models.DecimalField(
        max_digits=12, decimal_places=3, verbose_name="质量(mg)"
    )
    state = models.CharField(
        max_length=16, choices=State.choices, default=State.IDLE, verbose_name="状态"
    )
    current_container = models.ForeignKey(
        "Container",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="当前转移仓",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "laiyu_powder"
        verbose_name = "铼羽粉筒"
        verbose_name_plural = "铼羽粉筒"

    def __str__(self):
        return self.name


class JingtaiPowder(models.Model):
    """
    晶泰粉筒
    """

    class State(models.TextChoices):
        IDLE = "idle", "空闲"
        IN_USE = "in_use", "使用中"

    name = models.CharField(
        max_length=128, unique=True, db_index=True, verbose_name="唯一名"
    )
    material_name = models.CharField(max_length=128, verbose_name="粉末名称")
    mass_mg = models.DecimalField(
        max_digits=12, decimal_places=3, verbose_name="质量(mg)"
    )
    state = models.CharField(
        max_length=16, choices=State.choices, default=State.IDLE, verbose_name="状态"
    )
    current_container = models.ForeignKey(
        "Container",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="当前转移仓",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "jingtai_powder"
        verbose_name = "晶泰粉筒"
        verbose_name_plural = "晶泰粉筒"

    def __str__(self):
        return self.name


class ReagentBottle150(models.Model):
    """
    150mL试剂瓶
    """

    class State(models.TextChoices):
        IDLE = "idle", "空闲"
        IN_USE = "in_use", "使用中"

    name = models.CharField(
        max_length=128, unique=True, db_index=True, verbose_name="唯一名"
    )
    reagent_name = models.CharField(max_length=128, verbose_name="试剂名称")
    volume_ml = models.DecimalField(
        max_digits=12, decimal_places=3, verbose_name="体积(mL)"
    )
    state = models.CharField(
        max_length=16, choices=State.choices, default=State.IDLE, verbose_name="状态"
    )
    current_container = models.ForeignKey(
        "Container",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="当前转移仓",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "reagent_bottle_150"
        verbose_name = "150mL试剂瓶"
        verbose_name_plural = "150mL试剂瓶"

    def __str__(self):
        return self.name


# endregion

# region 备料清单与装填操作(PreparationList, FillOperation)


class PreparationList(models.Model):
    """
    备料清单
    """

    class Status(models.TextChoices):
        PENDING = "pending", "待备料"
        IN_PROGRESS = "in_progress", "备料中"
        COMPLETED = "completed", "已完成"
        CANCELLED = "cancelled", "已取消"

    id = models.CharField(max_length=64, primary_key=True, verbose_name="清单ID")
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="创建人"
    )
    task_ids = models.JSONField(verbose_name="任务ID列表")

    # 按工站统计的物料需求（简化结构）
    station_materials = models.JSONField(
        verbose_name="按工站物料需求",
        help_text="按工站分组的物料需求统计",
        default=dict,
    )

    # 新增：备料清单物料需求与实际装填的绑定关系
    material_fill_bindings = models.JSONField(
        verbose_name="物料装填绑定关系",
        help_text="记录备料清单中物料需求与实际装填物料的绑定关系，结构：{工站: {物料类型: {索引: 绑定信息}}}",
        default=dict,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="状态",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "preparation_list"
        verbose_name = "备料清单"
        verbose_name_plural = "备料清单"
        ordering = ["-created_at"]

    def __str__(self):
        return f"备料清单 {self.id}"

    def get_station_materials(self, station_key):
        """获取指定工站的物料需求"""
        return self.station_materials.get(station_key, {})

    def get_material_items(self, station_key, material_type):
        """获取指定工站指定物料类型的项目列表"""
        station_materials = self.get_station_materials(station_key)
        return station_materials.get(material_type, [])

    def get_consumable_count(self, station_key, material_type):
        """获取指定工站指定耗材类型的数量"""
        station_materials = self.get_station_materials(station_key)
        return station_materials.get(material_type, 0)


class FillOperation(models.Model):
    """
    装填操作记录
    """

    preparation_list = models.ForeignKey(
        PreparationList,
        on_delete=models.CASCADE,
        related_name="operations",
        verbose_name="备料清单",
    )
    container = models.ForeignKey(
        Container, on_delete=models.CASCADE, verbose_name="转移仓"
    )
    slot_index = models.PositiveIntegerField(verbose_name="槽位索引")
    material_id = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="物料ID"
    )
    material_kind = models.CharField(max_length=64, verbose_name="物料类型")
    material_name = models.CharField(max_length=128, verbose_name="物料名称")
    operated_by = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="操作人"
    )
    operated_at = models.DateTimeField(auto_now_add=True, verbose_name="操作时间")

    class Meta:
        db_table = "fill_operation"
        verbose_name = "装填操作"
        verbose_name_plural = "装填操作"
        ordering = ["-operated_at"]

    def __str__(self):
        return f"装填操作 {self.container.name}#{self.slot_index}"


# endregion

# region 备料工位(PreparationStation)


class PreparationStation(models.Model):
    """
    备料工站位置模型
    记录24个位置（12个备料区 + 12个回料区）的转移仓放置情况
    """

    class AreaType(models.TextChoices):
        PREPARATION = "preparation", "备料区"
        RETURN = "return", "回料区"

    class Position(models.TextChoices):
        # 备料区位置
        PREP_1 = "prep_1", "备料区-1"
        PREP_2 = "prep_2", "备料区-2"
        PREP_3 = "prep_3", "备料区-3"
        PREP_4 = "prep_4", "备料区-4"
        PREP_5 = "prep_5", "备料区-5"
        PREP_6 = "prep_6", "备料区-6"
        PREP_7 = "prep_7", "备料区-7"
        PREP_8 = "prep_8", "备料区-8"
        PREP_9 = "prep_9", "备料区-9"
        PREP_10 = "prep_10", "备料区-10"
        PREP_11 = "prep_11", "备料区-11"
        PREP_12 = "prep_12", "备料区-12"
        # 回料区位置
        RETURN_1 = "return_1", "回料区-1"
        RETURN_2 = "return_2", "回料区-2"
        RETURN_3 = "return_3", "回料区-3"
        RETURN_4 = "return_4", "回料区-4"
        RETURN_5 = "return_5", "回料区-5"
        RETURN_6 = "return_6", "回料区-6"
        RETURN_7 = "return_7", "回料区-7"
        RETURN_8 = "return_8", "回料区-8"
        RETURN_9 = "return_9", "回料区-9"
        RETURN_10 = "return_10", "回料区-10"
        RETURN_11 = "return_11", "回料区-11"
        RETURN_12 = "return_12", "回料区-12"

    position = models.CharField(
        max_length=20, choices=Position.choices, unique=True, verbose_name="位置"
    )
    area_type = models.CharField(
        max_length=20, choices=AreaType.choices, verbose_name="区域类型"
    )
    position_name = models.CharField(max_length=100, verbose_name="位置名称")
    expected_material_kind = models.CharField(
        max_length=64, choices=MaterialKind.choices, verbose_name="预期物料类型"
    )
    current_container = models.ForeignKey(
        Container,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="当前转移仓",
    )
    is_occupied = models.BooleanField(default=False, verbose_name="是否被占用")
    placed_at = models.DateTimeField(blank=True, null=True, verbose_name="放置时间")
    placed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="放置人"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "preparation_station"
        verbose_name = "备料工站位置"
        verbose_name_plural = "备料工站位置"
        ordering = ["area_type", "position"]
        indexes = [
            models.Index(fields=["area_type", "position"]),
            models.Index(fields=["is_occupied"]),
        ]

    def __str__(self):
        return f"{self.position_name} - {self.current_container.name if self.current_container else '空闲'}"

    def place_container(self, container, user):
        """放置转移仓"""
        if self.is_occupied:
            raise ValidationError(f"位置 {self.position_name} 已被占用")

        # 检查物料类型是否匹配
        if container.spec.allowed_material_kind != self.expected_material_kind:
            raise ValidationError(
                f"转移仓物料类型 {container.spec.allowed_material_kind} 与位置预期类型 {self.expected_material_kind} 不匹配"
            )

        # 检查转移仓是否已被占用
        if container.state == Container.State.IN_USE:
            raise ValidationError(f"转移仓 {container.name} 正在使用中")

        self.current_container = container
        self.is_occupied = True
        self.placed_at = timezone.now()
        self.placed_by = user
        self.save()

        # 更新转移仓状态
        container.state = Container.State.IN_USE
        container.current_station = None  # 备料工站不是Station模型
        container.save()

        return self

    def remove_container(self, user):
        """移除转移仓"""
        if not self.is_occupied or not self.current_container:
            raise ValidationError(f"位置 {self.position_name} 没有转移仓")

        container = self.current_container
        self.current_container = None
        self.is_occupied = False
        self.placed_at = None
        self.placed_by = None
        self.save()

        # 更新转移仓状态
        container.state = Container.State.IDLE
        container.current_station = None
        container.save()

        return self


# region 机器学习相关模型(ML)
class DataFile(models.Model):
    """
    数据文件模型，用于存储用户上传的CSV文件
    """
    
    STATUS_CHOICES = (
        ('uploading', '上传中'),
        ('processing', '处理中'),
        ('ready', '就绪'),
        ('error', '错误'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    filename = models.CharField(max_length=255, verbose_name="文件名")
    original_filename = models.CharField(max_length=255, verbose_name="原始文件名")
    file_path = models.CharField(max_length=500, verbose_name="文件路径")
    file_size = models.BigIntegerField(verbose_name="文件大小(字节)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploading', verbose_name="状态")
    
    # 数据统计信息
    total_rows = models.IntegerField(null=True, blank=True, verbose_name="总行数")
    total_columns = models.IntegerField(null=True, blank=True, verbose_name="总列数")
    column_names = models.JSONField(null=True, blank=True, verbose_name="列名列表")
    data_types = models.JSONField(null=True, blank=True, verbose_name="数据类型")
    
    # 数据质量分析
    missing_values = models.JSONField(null=True, blank=True, verbose_name="缺失值统计")
    outlier_info = models.JSONField(null=True, blank=True, verbose_name="异常值统计")
    
    # 数据预览和分析结果
    data_preview = models.JSONField(null=True, blank=True, verbose_name="数据预览")
    quality_analysis = models.JSONField(null=True, blank=True, verbose_name="质量分析结果")
    
    # 处理日志和错误信息
    processing_log = models.TextField(blank=True, verbose_name="处理日志")
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = "data_file"
        verbose_name = "数据文件"
        verbose_name_plural = "数据文件"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.original_filename} ({self.user.username})"
    
    def get_file_size_display(self):
        """格式化文件大小显示"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def get_status_display(self):
        """获取状态显示名称"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)


class MLAlgorithm(models.Model):
    """
    机器学习算法模型
    """
    
    ALGORITHM_TYPE_CHOICES = (
        ('regression', '回归'),
        ('classification', '分类'),
        ('clustering', '聚类'),
    )
    
    name = models.CharField(max_length=100, verbose_name="算法名称")
    display_name = models.CharField(max_length=100, verbose_name="显示名称")
    algorithm_type = models.CharField(max_length=20, choices=ALGORITHM_TYPE_CHOICES, verbose_name="算法类型")
    description = models.TextField(blank=True, verbose_name="算法描述")
    # 兼容两种字段命名：seeder 使用 parameter_schema/default_parameters
    # 现有代码使用 parameters_schema
    parameters_schema = models.JSONField(verbose_name="参数配置模式", default=dict)
    parameter_schema = models.JSONField(verbose_name="参数配置模式(兼容)", default=dict)
    default_parameters = models.JSONField(verbose_name="默认参数(兼容)", default=dict)
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    is_premium = models.BooleanField(default=False, verbose_name="是否付费算法")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = "ml_algorithm"
        verbose_name = "机器学习算法"
        verbose_name_plural = "机器学习算法"
        ordering = ['algorithm_type', 'name']
    
    def __str__(self):
        return f"{self.display_name} ({self.get_algorithm_type_display()})"


class MLTask(models.Model):
    """
    机器学习任务模型
    """
    
    STATUS_CHOICES = (
        ('pending', '等待中'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('failed', '失败'),
        ('cancelled', '已取消'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    name = models.CharField(max_length=200, verbose_name="任务名称")
    description = models.TextField(blank=True, verbose_name="任务描述")
    
    # 数据文件
    data_file = models.ForeignKey(DataFile, on_delete=models.CASCADE, related_name='ml_tasks', verbose_name="数据文件")
    train_data_file = models.ForeignKey(DataFile, on_delete=models.CASCADE, null=True, blank=True, related_name='train_tasks', verbose_name="训练数据文件")
    test_data_file = models.ForeignKey(DataFile, on_delete=models.CASCADE, null=True, blank=True, related_name='test_tasks', verbose_name="测试数据文件")
    
    # 算法配置
    algorithm = models.ForeignKey(MLAlgorithm, on_delete=models.CASCADE, verbose_name="算法")
    algorithm_parameters = models.JSONField(verbose_name="算法参数")

    # 训练配置
    target_column = models.CharField(max_length=255, blank=True, verbose_name="目标列")
    feature_columns = models.JSONField(null=True, blank=True, verbose_name="特征列列表")
    train_ratio = models.FloatField(default=0.8, verbose_name="训练集比例")
    test_ratio = models.FloatField(default=0.2, verbose_name="测试集比例")
    validation_ratio = models.FloatField(default=0.0, verbose_name="验证集比例")
    
    # 任务状态
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="状态")
    progress = models.FloatField(default=0.0, verbose_name="进度(0-100)")
    error_message = models.TextField(blank=True, verbose_name="错误信息")
    training_log = models.TextField(blank=True, verbose_name="训练日志")
    
    # 任务时间
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="开始时间")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = "ml_task"
        verbose_name = "机器学习任务"
        verbose_name_plural = "机器学习任务"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"
    
    def get_status_display(self):
        """获取状态显示名称"""
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def get_duration_display(self):
        """返回运行时长的人类可读字符串"""
        if not self.started_at:
            return "未开始"
        end_time = self.completed_at or timezone.now()
        delta = end_time - self.started_at
        seconds = int(delta.total_seconds())
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        if hours > 0:
            return f"{hours}小时{minutes}分{seconds}秒"
        if minutes > 0:
            return f"{minutes}分{seconds}秒"
        return f"{seconds}秒"

    # 兼容旧代码：使用 task.task_name 访问 name
    @property
    def task_name(self):
        return self.name

    @task_name.setter
    def task_name(self, value):
        self.name = value


class MLTaskResult(models.Model):
    """
    机器学习任务结果模型
    """
    
    task = models.OneToOneField(MLTask, on_delete=models.CASCADE, related_name='result', verbose_name="任务")
    
    # 模型性能指标
    accuracy = models.FloatField(null=True, blank=True, verbose_name="准确率")
    precision = models.FloatField(null=True, blank=True, verbose_name="精确率")
    recall = models.FloatField(null=True, blank=True, verbose_name="召回率")
    f1_score = models.FloatField(null=True, blank=True, verbose_name="F1分数")
    mse = models.FloatField(null=True, blank=True, verbose_name="均方误差")
    mae = models.FloatField(null=True, blank=True, verbose_name="平均绝对误差")
    r2_score = models.FloatField(null=True, blank=True, verbose_name="R²分数")
    
    # 模型文件路径
    model_path = models.CharField(max_length=500, blank=True, verbose_name="模型文件路径")
    
    # 解释/图表/曲线等
    feature_importance = models.JSONField(null=True, blank=True, verbose_name="特征重要性")
    learning_curve = models.JSONField(null=True, blank=True, verbose_name="学习曲线")
    confusion_matrix = models.JSONField(null=True, blank=True, verbose_name="混淆矩阵")
    chart_data = models.JSONField(null=True, blank=True, verbose_name="图表数据")

    # 详细结果
    detailed_results = models.JSONField(null=True, blank=True, verbose_name="详细结果")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = "ml_task_result"
        verbose_name = "机器学习任务结果"
        verbose_name_plural = "机器学习任务结果"
    
    def __str__(self):
        return f"{self.task.name} - 结果"


class DataProcessingLog(models.Model):
    """
    数据处理日志模型
    """
    
    PROCESSING_TYPE_CHOICES = (
        ('missing_values', '缺失值处理'),
        ('outliers', '异常值处理'),
        ('data_split', '数据分割'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    data_file = models.ForeignKey(DataFile, on_delete=models.CASCADE, verbose_name="数据文件")
    processing_type = models.CharField(max_length=20, choices=PROCESSING_TYPE_CHOICES, verbose_name="处理类型")
    parameters = models.JSONField(verbose_name="处理参数")
    result_summary = models.TextField(blank=True, verbose_name="处理结果摘要")
    processing_log = models.TextField(blank=True, verbose_name="处理日志")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        db_table = "data_processing_log"
        verbose_name = "数据处理日志"
        verbose_name_plural = "数据处理日志"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_processing_type_display()} - {self.data_file.original_filename}"


# endregion
