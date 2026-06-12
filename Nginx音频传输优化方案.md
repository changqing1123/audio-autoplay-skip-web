# Nginx 接管音频传输优化方案

## 背景

当前音频播放链路是：前端请求 `/api/v1/audios/<id>/play-url/` 获取临时播放地址，再由 Django 的 `/api/v1/audios/<id>/stream/` 返回音频流。现有实现已经支持 Range 请求，但文件数据仍由 Django/uWSGI 进程参与发送。

在移动端浏览器后台播放、长音频、大文件、拖动进度条或并发访问较多时，让应用进程持续传输媒体文件可能带来以下问题：

- 后台播放时浏览器网络调度更敏感，流式连接更容易被挂起或重连。
- Django/uWSGI worker 被音频传输占用，影响接口响应能力。
- Range、断点续传、大文件发送由 Web 服务器处理通常更稳定。

## 优化目标

让 Django 继续负责鉴权、分组权限和签名 token 校验，但不直接发送音频文件；音频文件由 Nginx 使用内部路径发送。

优化后的链路：

1. 前端请求 `/api/v1/audios/<id>/play-url/` 获取带 token 的播放地址。
2. 前端播放 `/api/v1/audios/<id>/stream/?token=...`。
3. Django 校验 token、用户状态、分组权限和文件存在性。
4. Django 返回带 `X-Accel-Redirect` 的响应。
5. Nginx 根据内部路径直接发送真实音频文件。

## 预期收益

- 音频加载、拖动进度条、续播会更稳定。
- 大文件传输不再长时间占用 Django/uWSGI worker。
- Nginx 原生处理静态文件、Range 和缓存头，整体播放体验更顺滑。
- 后端接口压力降低，多个用户同时听音频时更稳。

## Nginx 配置示例

在 HTTPS 的 `server { ... }` 内新增一个内部音频路径。示例路径需按服务器真实媒体目录调整。

```nginx
location /protected-media/ {
    internal;
    alias /www/wwwroot/juejin_podcast_backend/media/;

    types {
        audio/mpeg mp3;
        audio/mp4 m4a;
        audio/ogg ogg;
        audio/wav wav;
    }

    default_type application/octet-stream;
    add_header Accept-Ranges bytes always;
    add_header Cache-Control "private, no-store" always;

    sendfile on;
    tcp_nopush on;
    aio threads;
}
```

现有 `/api/` 代理仍保留，例如：

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000/api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_buffering off;
    proxy_read_timeout 2400s;
    proxy_connect_timeout 2400s;
    proxy_send_timeout 2400s;
}
```

## 后端改造思路

主要改 `audios/views.py` 的 `build_audio_stream_response(audio, request)`：

- 保留当前 token 校验和权限判断。
- 不再返回 `FileResponse` 或 `StreamingHttpResponse`。
- 返回一个空响应，并设置 `X-Accel-Redirect` 指向 Nginx 内部路径。
- 设置 `Content-Type`、`Cache-Control`、`Accept-Ranges` 等响应头。

伪代码示例：

```python
from urllib.parse import quote
from django.http import HttpResponse


def build_audio_stream_response(audio, request):
    response = HttpResponse()
    response['Content-Type'] = 'audio/mpeg'
    response['Cache-Control'] = 'private, no-store'
    response['Accept-Ranges'] = 'bytes'
    response['X-Accel-Buffering'] = 'no'
    response['X-Accel-Redirect'] = '/protected-media/' + quote(audio.file.name)
    return response
```

注意：`audio.file.name` 通常是相对于 `MEDIA_ROOT` 的路径，例如 `audios/xxx.mp3`。Nginx 的 `alias` 必须指向 `MEDIA_ROOT`，否则内部路径无法找到文件。

## 上线步骤建议

1. 先备份当前 Nginx 站点配置。
2. 在 HTTPS `server` 内新增 `/protected-media/` internal 配置。
3. 执行 `nginx -t` 检查配置。
4. 修改后端 `audios/views.py`，让音频流接口返回 `X-Accel-Redirect`。
5. 重启 Python 项目或 uWSGI。
6. 重载 Nginx。
7. 测试：播放、后台播放、拖动进度条、连续播放下一首。

## 回滚方案

- 如果 Nginx internal 路径配置不正确或播放失败，先恢复后端 `audios/views.py` 原来的 `FileResponse/StreamingHttpResponse` 实现。
- 删除或保留 `/protected-media/` 配置都可以；只要后端不返回 `X-Accel-Redirect`，该配置不会影响现有功能。

## 当前建议

目前前端已经修复了后台播放兼容性和自动播放下一首的问题。如果当前浏览器测试可以完整播放，并且并发用户不多，可以暂时不做此优化。

后续如果出现以下情况，建议实施本方案：

- 某些移动浏览器后台播放仍偶发中断。
- 拖动进度条响应慢或失败。
- 音频文件较大，后端 worker 占用明显。
- 多用户同时播放时接口变慢。
