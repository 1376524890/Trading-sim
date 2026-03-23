#!/bin/bash
# 系统诊断脚本 - 股票交易系统

echo "=========================================="
echo "    股票交易系统 - 系统诊断"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 获取脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# 切换到项目根目录（脚本的上级目录）
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# 检查端口
check_port() {
    local port=$1
    local name=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        echo -e "${GREEN}✓${NC} $name (端口 $port) - 运行中"
        return 0
    else
        echo -e "${RED}✗${NC} $name (端口 $port) - 未运行"
        return 1
    fi
}

# 检查进程
check_process() {
    local name=$1
    local pattern=$2
    if pgrep -f "$pattern" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name - 进程运行中"
        return 0
    else
        echo -e "${RED}✗${NC} $name - 进程未运行"
        return 1
    fi
}

# 检查目录结构
check_directory() {
    local dir=$1
    local name=$2
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✓${NC} $name - 存在"
        return 0
    else
        echo -e "${RED}✗${NC} $name - 不存在"
        return 1
    fi
}

echo "1. 服务状态检查"
echo "----------------"
check_port 8080 "后端 API"
check_port 3000 "前端 Dev Server"
echo ""

echo "2. 目录结构检查"
echo "----------------"
check_directory "$PROJECT_DIR/backend" "后端目录"
check_directory "$PROJECT_DIR/frontend" "前端目录"
check_directory "$PROJECT_DIR/backend/logs" "后端日志目录"
check_directory "$PROJECT_DIR/logs" "系统日志目录"
check_directory "$PROJECT_DIR/backend/venv" "Python 虚拟环境"
check_directory "$PROJECT_DIR/frontend/node_modules" "Node 依赖目录"
echo ""

echo "3. 文件检查"
echo "------------"
if [ -f "$PROJECT_DIR/backend/app/api_server.py" ]; then
    echo -e "${GREEN}✓${NC} API 服务器文件 - 存在"
else
    echo -e "${RED}✗${NC} API 服务器文件 - 不存在"
fi

if [ -f "$PROJECT_DIR/frontend/vite.config.ts" ]; then
    echo -e "${GREEN}✓${NC} Vite 配置文件 - 存在"
else
    echo -e "${RED}✗${NC} Vite 配置文件 - 不存在"
fi
echo ""

echo "4. 代理配置"
echo "------------"
if [ -f "$PROJECT_DIR/frontend/vite.config.ts" ]; then
    PROXY_TARGET=$(grep -o "target: 'http://[^']*'" "$PROJECT_DIR/frontend/vite.config.ts" 2>/dev/null | head -1)
    echo "Vite 代理目标: $PROXY_TARGET"
fi
echo ""

echo "5. 日志文件"
echo "------------"
if [ -f "$PROJECT_DIR/logs/system.log" ]; then
    echo -e "${GREEN}✓${NC} 系统日志: $PROJECT_DIR/logs/system.log"
else
    echo -e "${YELLOW}!${NC} 系统日志不存在"
fi

if [ -f "$PROJECT_DIR/backend/logs/api.log" ]; then
    echo -e "${GREEN}✓${NC} 后端日志: $PROJECT_DIR/backend/logs/api.log"
    echo "    最后 5 行:"
    tail -5 "$PROJECT_DIR/backend/logs/api.log" | sed 's/^/      /'
else
    echo -e "${YELLOW}!${NC} 后端日志不存在（后端未启动）"
fi
echo ""

echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "快速修复:"
echo "  启动后端: ./start.sh backend"
echo "  启动前端: ./start.sh frontend"
echo "  一键启动: ./start.sh all"
echo ""
