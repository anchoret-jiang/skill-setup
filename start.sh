#!/bin/bash

# Claude Skills Terminal 启动脚本
# 后端: http://localhost:8000
# 前端: http://localhost:8001

set -e

# 颜色定义
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════╗"
echo "║     Claude Skills Terminal v1.0            ║"
echo "╚════════════════════════════════════════════╝"
echo -e "${NC}"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 虚拟环境路径
VENV_DIR="$SCRIPT_DIR/venv"

# 清理函数
cleanup() {
    echo -e "\n${YELLOW}正在关闭服务...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}服务已关闭${NC}"
    exit 0
}

# 捕获退出信号
trap cleanup SIGINT SIGTERM

# 检查/创建虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}创建虚拟环境...${NC}"
    python3 -m venv "$VENV_DIR"
fi

# 激活虚拟环境
source "$VENV_DIR/bin/activate"

# 清理占用的端口
echo -e "${YELLOW}清理端口...${NC}"
lsof -ti:8000 -ti:8001 2>/dev/null | xargs -r kill -9 2>/dev/null || true

# 检查依赖
echo -e "${YELLOW}检查依赖...${NC}"
python3 -c "import fastapi, uvicorn" 2>/dev/null || {
    echo -e "${YELLOW}安装依赖...${NC}"
    pip install fastapi uvicorn python-multipart
}

# 启动后端 (端口 8000)
echo -e "${GREEN}启动后端服务 (http://localhost:8000)...${NC}"
cd "$SCRIPT_DIR/skill-assistant/backend"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd "$SCRIPT_DIR"

# 等待后端启动
sleep 2

# 启动前端 (端口 8001)
echo -e "${GREEN}启动前端服务 (http://localhost:8001)...${NC}"
cd "$SCRIPT_DIR/skill-assistant/frontend"
python3 -m http.server 8001 &
FRONTEND_PID=$!
cd "$SCRIPT_DIR"

echo ""
echo -e "${CYAN}════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ 服务已启动${NC}"
echo ""
echo -e "  前端地址: ${CYAN}http://localhost:8001${NC}"
echo -e "  后端地址: ${CYAN}http://localhost:8000${NC}"
echo -e "  API 文档: ${CYAN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"
echo -e "${CYAN}════════════════════════════════════════════${NC}"
echo ""

# 等待子进程
wait
