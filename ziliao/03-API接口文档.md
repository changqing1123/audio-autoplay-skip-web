# MP3分组播放系统 API接口文档
**版本**：V1.0  
**更新时间**：2026-05-15  
**基础URL**：`/api/v1/`  
**认证方式**：JWT Token  
**数据格式**：JSON

## 一、通用说明
### 1.1 认证
所有需要登录的接口都需要在请求头中携带Token：
```
Authorization: Bearer <your_token>
```

### 1.2 响应格式
**成功响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

**错误响应**：
```json
{
  "code": 400,
  "message": "错误信息",
  "data": null
}
```

## 二、用户认证接口

### 2.1 用户登录
- **URL**：`/api/v1/auth/login/`
- **方法**：POST
- **是否需要认证**：否
- **请求参数**：
```json
{
  "username": "用户名",
  "password": "密码"
}
```
- **响应数据**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "testuser",
      "is_superuser": false
    }
  }
}
```

### 2.2 用户登出
- **URL**：`/api/v1/auth/logout/`
- **方法**：POST
- **是否需要认证**：是
- **请求参数**：无
- **响应数据**：
```json
{
  "code": 200,
  "message": "登出成功",
  "data": null
}
```

## 三、音频接口

### 3.1 获取当前用户分组的音频列表
- **URL**：`/api/v1/audios/`
- **方法**：GET
- **是否需要认证**：是
- **请求参数**：无
- **响应数据**：
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "filename": "测试音频1.mp3",
      "upload_time": "2026-05-15T10:00:00Z",
      "duration": 120
    },
    {
      "id": 2,
      "filename": "测试音频2.mp3",
      "upload_time": "2026-05-14T15:30:00Z",
      "duration": 180
    }
  ]
}
```

### 3.2 获取音频播放地址
- **URL**：`/api/v1/audios/{id}/stream/`
- **方法**：GET
- **是否需要认证**：是
- **说明**：直接返回音频文件流，用于播放

## 四、已听记录接口

### 4.1 获取当前用户的已听音频ID列表
- **URL**：`/api/v1/listened/ids/`
- **方法**：GET
- **是否需要认证**：是
- **请求参数**：无
- **响应数据**：
```json
{
  "code": 200,
  "message": "success",
  "data": [1, 3, 5]
}
```

### 4.2 标记音频为已听完
- **URL**：`/api/v1/listened/mark/`
- **方法**：POST
- **是否需要认证**：是
- **请求参数**：
```json
{
  "audio_id": 1
}
```
- **响应数据**：
```json
{
  "code": 200,
  "message": "标记成功",
  "data": null
}
```

### 4.3 获取当前用户的已听音频列表
- **URL**：`/api/v1/listened/`
- **方法**：GET
- **是否需要认证**：是
- **请求参数**：无
- **响应数据**：
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "filename": "测试音频1.mp3",
      "upload_time": "2026-05-15T10:00:00Z",
      "listened_time": "2026-05-15T14:30:00Z"
    },
    {
      "id": 3,
      "filename": "测试音频3.mp3",
      "upload_time": "2026-05-13T09:00:00Z",
      "listened_time": "2026-05-14T16:00:00Z"
    }
  ]
}
```

## 五、错误码说明
| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未登录或Token无效 |
| 403 | 没有权限访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |