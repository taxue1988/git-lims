user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log;
pid /run/nginx.pid;

# Load dynamic modules. see /usr/share/doc/nginx/README.dynamic
include /usr/share/nginx/modules/*.conf;

events {
    worker_connections 1024;
}

http {
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile            on;
    tcp_nopush          on;
    tcp_nodelay         on;
    keepalive_timeout   65;
    types_hash_max_size 4096;

    include             /etc/nginx/mime.types;
    default_type        application/octet-stream;

    upstream django {
        server 127.0.0.1:9000;
    }

    server {
        listen  80;
        listen  [::]:80;
        # 建议添加server_name，例如：server_name your-domain.com或_;

        location /static {
            alias /data/git_lims_static/;
        }

        location / {
            uwsgi_pass  django;
            include     uwsgi_params;
        }
    }