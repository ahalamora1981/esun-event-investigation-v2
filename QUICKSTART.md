# Docker Compose 快速入门指南

本指南帮助你快速将项目部署到 Linux 服务器。

## 最快的部署方式（推荐）

### 1. 上传文件到服务器

将以下文件/文件夹上传到 Linux 服务器：

```
event-investigation-v2/
├── src/                    # 源代码目录
├── pyproject.toml          # 项目配置
├── uv.lock                 # 依赖锁定文件
├── Dockerfile              # Docker 镜像构建文件
├── docker-compose.yml     # Docker Compose 配置
├── .env.example           # 环境变量示例
└── deploy.sh              # 部署脚本
```

**上传方法**：

```bash
# 在本地机器打包
tar -czf event-investigation-v2.tar.gz event-investigation-v2

# 使用 scp 上传到服务器
scp event-investigation-v2.tar.gz user@your-server:/home/user/

# SSH 登录服务器
ssh user@your-server

# 解压
cd /home/user/
tar -xzf event-investigation-v2.tar.gz
cd event-investigation-v2
```

### 2. 运行部署脚本

```bash
# 赋予执行权限
chmod +x deploy.sh

# 运行部署脚本
./deploy.sh
```

脚本会自动：
- ✓ 检查 Docker 和 Docker Compose
- ✓ 创建 .env 配置文件
- ✓ 创建必要的目录
- ✓ 构建 Docker 镜像
- ✓ 启动服务
- ✓ 测试服务连接

### 3. 配置环境变量

如果部署时跳过了配置，现在需要编辑 `.env` 文件：

```bash
nano .env
```

**必须配置的项**：

```bash
# CCS 密钥（必填）
CCS_APP_SECRET=your_actual_secret

# DashScope API Key（必填）
DASHSCOPE_API_KEY=your_dashscope_key

# 其他服务地址（根据实际网络修改）
CCS_API_BASE_URL=http://10.101.100.109:18110
RERANKER_URL=http://10.101.100.13:8012/v1/rerank
```

编辑完成后重启服务：

```bash
docker compose restart
```

### 4. 验证部署

```bash
# 检查容器状态
docker compose ps

# 查看日志
docker compose logs -f

# 访问 API 文档
# 在浏览器打开: http://your-server-ip:8000/docs
```

---

## 手动部署步骤

如果不使用部署脚本，可以手动执行以下步骤：

### 步骤 1：准备环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
nano .env
```

### 步骤 2：创建目录

```bash
mkdir -p src/logs src/output
chmod 755 src/logs src/output
```

### 步骤 3：构建和启动

```bash
# 构建镜像
docker compose build

# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f
```

---

## 常用命令

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose stop

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f

# 查看服务状态
docker compose ps

# 停止并删除容器
docker compose down

# 重新构建并启动
docker compose up -d --build
```

---

## 测试 API

服务启动后，可以使用 curl 测试：

```bash
# 测试服务健康状态
curl http://localhost:8000/docs

# 查看完整 API 文档
# 在浏览器访问: http://localhost:8000/docs
```

---

## 遇到问题？

1. **查看日志**：`docker compose logs`
2. **检查端口**：`netstat -tlnp | grep 8000`
3. **检查防火墙**：`sudo ufw status`
4. **详细故障排查**：参见 `DOCKER_DEPLOY.md`

---

## 下一步

- 阅读 `DOCKER_DEPLOY.md` 了解详细部署说明
- 配置 Nginx 反向代理（生产环境推荐）
- 配置 HTTPS 和域名
- 设置监控和备份

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `Dockerfile` | Docker 镜像构建文件 |
| `docker-compose.yml` | Docker Compose 编排配置 |
| `.env.example` | 环境变量配置模板 |
| `.dockerignore` | Docker 构建时忽略的文件 |
| `deploy.sh` | 自动化部署脚本 |
| `DOCKER_DEPLOY.md` | 详细部署文档 |
