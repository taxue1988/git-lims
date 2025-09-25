from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
import json

User = get_user_model()


class UserModelTest(TestCase):
    """用户模型测试"""

    def setUp(self):
        """测试前准备"""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='Admin123',
            role='admin',
            department='IT部门'
        )
        
        self.normal_user = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='User123',
            role='user',
            department='研发部门'
        )

    def test_user_creation(self):
        """测试用户创建"""
        self.assertEqual(self.admin_user.username, 'admin')
        self.assertEqual(self.admin_user.role, 'admin')
        self.assertTrue(self.admin_user.is_admin())
        
        self.assertEqual(self.normal_user.username, 'user1')
        self.assertEqual(self.normal_user.role, 'user')
        self.assertFalse(self.normal_user.is_admin())

    def test_user_str_representation(self):
        """测试用户字符串表示"""
        self.assertEqual(str(self.admin_user), 'admin (管理员)')
        self.assertEqual(str(self.normal_user), 'user1 (普通用户)')


class UserAPITest(TestCase):
    """用户API测试"""

    def setUp(self):
        """测试前准备"""
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='Admin123',
            role='admin'
        )
        
        self.normal_user = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='User123',
            role='user'
        )

    def test_user_list_api_without_auth(self):
        """测试未认证访问用户列表API"""
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, 302)  # 重定向到登录页面

    def test_user_list_api_with_normal_user(self):
        """测试普通用户访问用户列表API"""
        self.client.login(username='user1', password='User123')
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, 403)  # 权限不足

    def test_user_list_api_with_admin(self):
        """测试管理员访问用户列表API"""
        self.client.login(username='admin', password='Admin123')
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['ok'])
        self.assertIn('users', data['data'])
        self.assertIn('pagination', data['data'])

    def test_create_user_api(self):
        """测试创建用户API"""
        self.client.login(username='admin', password='Admin123')
        
        user_data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'NewUser123',
            'role': 'user',
            'department': '测试部门'
        }
        
        response = self.client.post(
            '/api/user/create/',
            data=json.dumps(user_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['ok'])
        
        # 验证用户是否创建成功
        new_user = User.objects.get(username='newuser')
        self.assertEqual(new_user.email, 'newuser@test.com')
        self.assertEqual(new_user.role, 'user')

    def test_create_user_with_weak_password(self):
        """测试创建用户时弱密码验证"""
        self.client.login(username='admin', password='Admin123')
        
        user_data = {
            'username': 'weakuser',
            'email': 'weakuser@test.com',
            'password': '123',  # 弱密码
            'role': 'user'
        }
        
        response = self.client.post(
            '/api/user/create/',
            data=json.dumps(user_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['ok'])
        self.assertIn('密码长度至少8位', str(data['details']))

    def test_update_user_api(self):
        """测试更新用户API"""
        self.client.login(username='admin', password='Admin123')
        
        update_data = {
            'department': '更新后的部门',
            'phone': '13800138000'
        }
        
        response = self.client.put(
            f'/api/user/{self.normal_user.id}/update/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['ok'])
        
        # 验证用户信息是否更新
        self.normal_user.refresh_from_db()
        self.assertEqual(self.normal_user.department, '更新后的部门')
        self.assertEqual(self.normal_user.phone, '13800138000')

    def test_toggle_user_status_api(self):
        """测试切换用户状态API"""
        self.client.login(username='admin', password='Admin123')
        
        # 初始状态
        self.assertTrue(self.normal_user.is_active)
        
        response = self.client.post(f'/api/user/{self.normal_user.id}/toggle-status/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['ok'])
        
        # 验证状态是否切换
        self.normal_user.refresh_from_db()
        self.assertFalse(self.normal_user.is_active)

    def test_delete_user_api(self):
        """测试删除用户API"""
        self.client.login(username='admin', password='Admin123')
        
        response = self.client.delete(f'/api/user/{self.normal_user.id}/delete/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['ok'])
        
        # 验证用户是否删除
        self.assertFalse(User.objects.filter(id=self.normal_user.id).exists())

    def test_user_statistics_api(self):
        """测试用户统计API"""
        self.client.login(username='admin', password='Admin123')
        
        response = self.client.get('/api/user/statistics/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['ok'])
        
        stats = data['data']
        self.assertIn('total_users', stats)
        self.assertIn('active_users', stats)
        self.assertIn('admin_users', stats)
        self.assertEqual(stats['total_users'], 2)  # admin + user1


class UserViewTest(TestCase):
    """用户视图测试"""

    def setUp(self):
        """测试前准备"""
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='Admin123',
            role='admin'
        )

    def test_login_view_get(self):
        """测试登录页面GET请求"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '用户登录')

    def test_login_view_post_success(self):
        """测试登录成功"""
        response = self.client.post('/', {
            'username': 'admin',
            'password': 'Admin123'
        })
        self.assertEqual(response.status_code, 302)  # 重定向

    def test_login_view_post_failure(self):
        """测试登录失败"""
        response = self.client.post('/', {
            'username': 'admin',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '用户名或密码错误')

    def test_admin_dashboard_access(self):
        """测试管理员仪表板访问"""
        self.client.login(username='admin', password='Admin123')
        response = self.client.get('/dashboard/admin/')
        self.assertEqual(response.status_code, 200)

    def test_user_task_management_redirect(self):
        """测试普通用户访问管理员仪表板被重定向"""
        normal_user = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='User123',
            role='user'
        )
        self.client.login(username='user1', password='User123')
        response = self.client.get('/dashboard/admin/')
        self.assertEqual(response.status_code, 302)  # 重定向到用户仪表板


class RegistrationTest(TestCase):
    """注册功能测试"""

    def setUp(self):
        """测试前准备"""
        self.client = Client()

    def test_registration_disabled(self):
        """测试注册功能已关闭"""
        # 创建第一个用户后，注册功能应该关闭
        User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='Admin123',
            role='admin'
        )
        
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 302)  # 重定向到登录页面

    def test_first_user_registration(self):
        """测试第一个用户注册"""
        response = self.client.get('/register/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '创建管理员账户')
        
        # 提交注册表单
        response = self.client.post('/register/', {
            'username': 'admin',
            'email': 'admin@test.com',
            'password': 'Admin123',
            'confirm_password': 'Admin123',
            'department': 'IT部门',
            'phone': '13800138000'
        })
        
        self.assertEqual(response.status_code, 302)  # 重定向到登录页面
        
        # 验证用户是否创建
        user = User.objects.get(username='admin')
        self.assertEqual(user.role, 'admin')
        self.assertTrue(user.is_superuser)
