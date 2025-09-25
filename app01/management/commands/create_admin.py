from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re

User = get_user_model()


class Command(BaseCommand):
    help = '创建管理员账户'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, required=True, help='用户名')
        parser.add_argument('--email', type=str, required=True, help='邮箱')
        parser.add_argument('--password', type=str, required=True, help='密码')
        parser.add_argument('--department', type=str, default='', help='部门')
        parser.add_argument('--phone', type=str, default='', help='电话')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        department = options['department']
        phone = options['phone']

        # 验证用户名
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            self.stdout.write(
                self.style.ERROR('用户名只能包含字母、数字和下划线，长度3-20位')
            )
            return

        # 验证邮箱
        try:
            validate_email(email)
        except ValidationError:
            self.stdout.write(
                self.style.ERROR('邮箱格式不正确')
            )
            return

        # 验证密码强度
        if len(password) < 8:
            self.stdout.write(
                self.style.ERROR('密码长度至少8位')
            )
            return
        if not re.search(r'[A-Z]', password):
            self.stdout.write(
                self.style.ERROR('密码必须包含大写字母')
            )
            return
        if not re.search(r'[a-z]', password):
            self.stdout.write(
                self.style.ERROR('密码必须包含小写字母')
            )
            return
        if not re.search(r'\d', password):
            self.stdout.write(
                self.style.ERROR('密码必须包含数字')
            )
            return

        # 检查用户名是否已存在
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.ERROR(f'用户名 {username} 已存在')
            )
            return

        # 检查邮箱是否已存在
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.ERROR(f'邮箱 {email} 已被使用')
            )
            return

        try:
            # 创建管理员用户
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                department=department,
                phone=phone
            )
            user.role = 'admin'
            user.save()

            self.stdout.write(
                self.style.SUCCESS(f'管理员账户 {username} 创建成功！')
            )
            self.stdout.write(f'用户名: {username}')
            self.stdout.write(f'邮箱: {email}')
            self.stdout.write(f'角色: 管理员')
            if department:
                self.stdout.write(f'部门: {department}')
            if phone:
                self.stdout.write(f'电话: {phone}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'创建管理员账户失败: {str(e)}')
            )
