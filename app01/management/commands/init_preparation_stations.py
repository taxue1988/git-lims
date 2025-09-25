from django.core.management.base import BaseCommand
from app01.models import PreparationStation, MaterialKind


class Command(BaseCommand):
    help = '初始化备料工站位置数据'

    def handle(self, *args, **options):
        # 定义24个位置的配置
        positions_config = [
            # 备料区位置
            ('prep_1', 'preparation', '备料区-1', MaterialKind.TEST_TUBE_15),
            ('prep_2', 'preparation', '备料区-2', MaterialKind.LAIYU_POWDER),
            ('prep_3', 'preparation', '备料区-3', MaterialKind.REAGENT_BTL_150),
            ('prep_4', 'preparation', '备料区-4', MaterialKind.SAMPLE_TUBE),
            ('prep_5', 'preparation', '备料区-5', MaterialKind.TIP_1),
            ('prep_6', 'preparation', '备料区-6', MaterialKind.TIP_5),
            ('prep_7', 'preparation', '备料区-7', MaterialKind.TEST_TUBE_15),
            ('prep_8', 'preparation', '备料区-8', MaterialKind.JINGTAI_POWDER),
            ('prep_9', 'preparation', '备料区-9', MaterialKind.REAGENT_BTL_150),
            ('prep_10', 'preparation', '备料区-10', MaterialKind.MIXTURE_TUBE),
            ('prep_11', 'preparation', '备料区-11', MaterialKind.SAMPLE_FILTER),
            ('prep_12', 'preparation', '备料区-12', MaterialKind.TIP_10),
            
            # 回料区位置
            ('return_1', 'return', '回料区-1', MaterialKind.TEST_TUBE_15),
            ('return_2', 'return', '回料区-2', MaterialKind.LAIYU_POWDER),
            ('return_3', 'return', '回料区-3', MaterialKind.REAGENT_BTL_150),
            ('return_4', 'return', '回料区-4', MaterialKind.SAMPLE_TUBE),
            ('return_5', 'return', '回料区-5', MaterialKind.TIP_1),
            ('return_6', 'return', '回料区-6', MaterialKind.TIP_5),
            ('return_7', 'return', '回料区-7', MaterialKind.TEST_TUBE_15),
            ('return_8', 'return', '回料区-8', MaterialKind.JINGTAI_POWDER),
            ('return_9', 'return', '回料区-9', MaterialKind.REAGENT_BTL_150),
            ('return_10', 'return', '回料区-10', MaterialKind.MIXTURE_TUBE),
            ('return_11', 'return', '回料区-11', MaterialKind.SAMPLE_FILTER),
            ('return_12', 'return', '回料区-12', MaterialKind.TIP_10),
        ]
        
        created_count = 0
        updated_count = 0
        
        for position, area_type, position_name, material_kind in positions_config:
            station, created = PreparationStation.objects.get_or_create(
                position=position,
                defaults={
                    'area_type': area_type,
                    'position_name': position_name,
                    'expected_material_kind': material_kind,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'创建位置: {position_name} ({material_kind})')
                )
            else:
                # 更新现有记录
                station.area_type = area_type
                station.position_name = position_name
                station.expected_material_kind = material_kind
                station.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'更新位置: {position_name} ({material_kind})')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'初始化完成！创建了 {created_count} 个位置，更新了 {updated_count} 个位置'
            )
        )
