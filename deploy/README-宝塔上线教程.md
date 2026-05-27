# 掘金播客宝塔上线教程

本部署包包含：

- `backend.zip`：Django 后台代码，包含上传文件 `media`
- `frontend.zip`：Vue 前台静态文件
- `nginx-site.conf`：Nginx 反向代理配置模板

本次包 **不包含数据库 SQL**。你直接使用现在宝塔里的数据库即可。

目标效果：

- 访问 `http://你的域名/` 进入 Vue 前台
- 访问 `http://你的域名/admin/` 进入 Django 管理后台

## 一、准备工作：确认数据库

1. 宝塔里确认 MySQL 5.7 数据库已经存在。
2. 数据库里需要已经有当前项目的数据表和数据。
3. 记下数据库信息：
   - 数据库名
   - 用户名
   - 密码
   - 地址：`127.0.0.1`
   - 端口：`3306`

如果你用的是 Docker 里的 MySQL：

1. 进入宝塔「Docker」或「容器」页面，打开 MySQL 容器详情。
2. 找到「端口映射」，看宿主机端口是多少。
   - 如果显示类似 `0.0.0.0:3306 -> 3306/tcp`，Django 里填写 `HOST=127.0.0.1`、`PORT=3306`
   - 如果显示类似 `0.0.0.0:3307 -> 3306/tcp`，Django 里填写 `HOST=127.0.0.1`、`PORT=3307`
3. 不要填写 Docker 容器内部 IP，容器重启后内部 IP 可能变化。
4. MySQL 用户需要允许从容器外连接。建议在宝塔数据库管理里新建一个业务用户，权限给当前数据库，访问范围选择 `%` 或允许本机连接。

## 二、上传代码部署后端，添加 Python 项目

1. 进入宝塔「文件」。
2. 打开 `/www/wwwroot/`。
3. 上传 `backend.zip`。
4. 解压后确认目录为：
   - `/www/wwwroot/juejin_podcast_backend/manage.py`
   - `/www/wwwroot/juejin_podcast_backend/juejin_podcast/settings.py`
   - `/www/wwwroot/juejin_podcast_backend/requirements.txt`
5. 打开 `/www/wwwroot/juejin_podcast_backend/juejin_podcast/settings.py`。
6. 找到 `DATABASES`，把数据库信息改成宝塔本地数据库：
   - `NAME`：你的数据库名
   - `USER`：你的数据库用户名
   - `PASSWORD`：你的数据库密码
   - `HOST`：`127.0.0.1`
   - `PORT`：`3306`
7. 宝塔进入「Python项目」。
8. 点击「添加 Python 项目」。
9. 按下面填写：
   - 项目名称：`juejin_podcast_backend`
   - 项目端口：`8000`
   - Python环境：`Python 3.10.20`
   - 启动方式：`uwsgi`
   - 项目路径：`/www/wwwroot/juejin_podcast_backend`
   - 入口文件：`/www/wwwroot/juejin_podcast_backend/juejin_podcast/wsgi.py`
   - 通讯协议：`wsgi`
   - 应用名称：`application`
   - 启动用户：`www`
   - 安装依赖包：`/www/wwwroot/juejin_podcast_backend/requirements.txt`
10. 点击添加并启动项目。

依赖版本已经按 Python 3.10 和 MySQL 5.7 固定：

- `Django==3.2.25`
- `djangorestframework-simplejwt==5.2.2`
- `PyMySQL==1.1.1`
- `cryptography==42.0.8`

## 三、上传代码部署前端

1. 进入宝塔「文件」。
2. 打开 `/www/wwwroot/`。
3. 上传 `frontend.zip`。
4. 解压后确认目录为：
   - `/www/wwwroot/juejin_podcast_frontend/index.html`
   - `/www/wwwroot/juejin_podcast_frontend/assets/`

前端是静态文件，宝塔添加站点时请选择 **HTML项目**，不要选 Node项目。

## 四、配置 Nginx

1. 进入宝塔「网站」。
2. 添加 HTML 站点，域名填写你的域名。
3. 网站根目录选择：
   - `/www/wwwroot/juejin_podcast_frontend`
4. 打开这个站点的「配置文件」。
5. 删除原配置内容。
6. 用部署包里的 `nginx-site.conf` 内容整体粘贴进去。
7. 把配置里的 `你的域名` 改成你的真实域名。
8. 保存。

配置里已经包含：

- `/` 指向 Vue 前台
- `/api/` 反向代理到 Django API
- `/admin/` 反向代理到 Django 管理后台
- `/static/` 指向后台静态文件
- `/media/` 指向上传的音频和图片文件

## 五、重启 Nginx

1. 宝塔进入「软件商店」。
2. 找到 Nginx。
3. 点击「重载配置」。
4. 再点击「重启」。

## 六、上线后检查

1. 访问 `http://你的域名/`，应进入前台。
2. 登录账号，确认能进入首页。
3. 点击音频，确认可以播放。
4. 访问 `http://你的域名/admin/`，确认可以进入后台。
5. 后台上传音频，确认文件能进入 `media` 目录。

## 常见问题

### 访问 `/admin/` 显示 502

说明 Nginx 找不到 Django 服务。检查 Python 项目是否启动，端口是否是 `8000`。

### 后台 Internal Server Error

优先检查：

- `settings.py` 里的数据库名、用户名、密码是否正确
- `HOST` 是否是 `127.0.0.1`
- `PORT` 是否是 `3306`
- Python 项目依赖是否安装成功

### 前台能打开但登录失败

检查 Nginx 配置里是否有：

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000/api/;
}
```

### 后台样式丢失

检查目录是否存在：

```text
/www/wwwroot/juejin_podcast_backend/staticfiles/
```

并确认 Nginx 配置里有：

```nginx
location /static/ {
    alias /www/wwwroot/juejin_podcast_backend/staticfiles/;
}
```
