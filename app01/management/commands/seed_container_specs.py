from django.core.management.base import BaseCommand
from app01.models import ContainerSpec, MaterialKind


class Command(BaseCommand):
    help = "初始化 ContainerSpec 类型数据（幂等）"

    def handle(self, *args, **options):
        specs = [
            {
                "name": "15mL试管转移仓",
                "code": "container_test_tube_15",
                "capacity": 6,
                "allowed_material_kind": MaterialKind.TEST_TUBE_15,
                "slot_meta_schema": None,
            },
            {
                "name": "铼羽粉筒转移仓",
                "code": "container_laiyu_powder",
                "capacity": 6,
                "allowed_material_kind": MaterialKind.LAIYU_POWDER,
                "slot_meta_schema": None,
            },
            {
                "name": "晶泰粉筒转移仓",
                "code": "container_jingtai_powder",
                "capacity": 3,
                "allowed_material_kind": MaterialKind.JINGTAI_POWDER,
                "slot_meta_schema": None,
            },
            {
                "name": "150mL试剂瓶转移仓",
                "code": "container_reagent_bottle_150",
                "capacity": 2,
                "allowed_material_kind": MaterialKind.REAGENT_BTL_150,
                "slot_meta_schema": None,
            },
            {
                "name": "1mL枪头转移仓",
                "code": "container_tip_1",
                "capacity": 96,
                "allowed_material_kind": MaterialKind.TIP_1,
                "slot_meta_schema": {
                    "total": {"type": "int", "min": 0, "max": 96},
                    "available_index": {"type": "int", "min": 0, "max": 95},
                },
            },
            {
                "name": "5mL枪头转移仓",
                "code": "container_tip_5",
                "capacity": 24,
                "allowed_material_kind": MaterialKind.TIP_5,
                "slot_meta_schema": {
                    "total": {"type": "int", "min": 0, "max": 24},
                    "available_index": {"type": "int", "min": 0, "max": 23},
                },
            },
            {
                "name": "10mL枪头转移仓",
                "code": "container_tip_10",
                "capacity": 24,
                "allowed_material_kind": MaterialKind.TIP_10,
                "slot_meta_schema": {
                    "total": {"type": "int", "min": 0, "max": 24},
                    "available_index": {"type": "int", "min": 0, "max": 23},
                },
            },
            {
                "name": "采样滤头转移仓",
                "code": "container_sample_filter",
                "capacity": 34,
                "allowed_material_kind": MaterialKind.SAMPLE_FILTER,
                "slot_meta_schema": {
                    "total": {"type": "int", "min": 0, "max": 34},
                    "available_index": {"type": "int", "min": 0, "max": 33},
                },
            },
            {
                "name": "过滤滤头转移仓",
                "code": "container_filtration_filter",
                "capacity": 8,
                "allowed_material_kind": MaterialKind.FILTRATION_FILTER,
                "slot_meta_schema": {
                    "total": {"type": "int", "min": 0, "max": 8},
                    "available_index": {"type": "int", "min": 0, "max": 7},
                },
            },
            {
                "name": "混合瓶转移仓",
                "code": "container_mixture_tube",
                "capacity": 34,
                "allowed_material_kind": MaterialKind.MIXTURE_TUBE,
                "slot_meta_schema": None,
            },
            {
                "name": "采样瓶转移仓",
                "code": "container_sample_tube",
                "capacity": 34,
                "allowed_material_kind": MaterialKind.SAMPLE_TUBE,
                "slot_meta_schema": {
                    "task_id": {"type": "int"},
                    "analysis_status": {
                        "type": "enum",
                        "choices": [
                            "TLC已分析",
                            "TLC未分析",
                            "GCMS已分析",
                            "GCMS未分析",
                            "HPLC已分析",
                            "HPLC未分析",
                        ],
                    },
                },
            },
            {
                "name": "进样柱转移仓",
                "code": "container_sample_cylinder",
                "capacity": 6,
                "allowed_material_kind": MaterialKind.SAMPLE_CYLINDER,
                "slot_meta_schema": None,
            },
            {
                "name": "色谱柱转移仓",
                "code": "container_chromatographic_cylinder",
                "capacity": 6,
                "allowed_material_kind": MaterialKind.CHROMATOGRAPHIC_CYL,
                "slot_meta_schema": None,
            },
        ]

        created, updated = 0, 0
        for spec in specs:
            obj, is_created = ContainerSpec.objects.update_or_create(
                code=spec["code"],
                defaults={
                    "name": spec["name"],
                    "capacity": spec["capacity"],
                    "allowed_material_kind": spec["allowed_material_kind"],
                    "slot_meta_schema": spec["slot_meta_schema"],
                },
            )
            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"ContainerSpec 初始化完成：新增 {created}，更新 {updated}"))
