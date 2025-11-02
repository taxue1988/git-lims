from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    # 这个正则表达式会匹配 ws/test/ 后面跟着的任何由字母、数字、下划线组成的字符串，
    # 并将其作为名为 'client_id' 的参数传递给 Consumer。
    # 例如: ws/test/client_A/ 或 ws/test/user_123/
    re_path(r'ws/test/(?P<client_id>\w+)/$', consumers.TestConsumer.as_asgi()),
]
