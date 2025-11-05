from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # 兼容两种路由：带 client_id 和不带 client_id
    # 例如: ws/test/client_A/ 或 ws/test/user_123/
    re_path(r'ws/test/(?P<client_id>\w+)/$', consumers.TestConsumer.as_asgi()),
    re_path(r'ws/test/$', consumers.TestConsumer.as_asgi()),
    # GCMS 专用路由
    re_path(r'ws/gcms/$', consumers.GcmsConsumer.as_asgi()),
    # HPLC 专用路由
    re_path(r'ws/hplc/$', consumers.HplcConsumer.as_asgi()),
]
