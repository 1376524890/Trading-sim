#!/bin/bash

# Stock Investment System - Start Script
# 用法: ./start.sh [backend|frontend|all|setup|status]

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Dependency files location
REQUIREMENTS_FILE="$SCRIPT_DIR/backend/requirements.txt"
PACKAGE_FILE="$SCRIPT_DIR/frontend/package.json"
DEPENDENCY_DOC="$SCRIPT_DIR/docs/Dependencies.md"

# Ensure logs directory exists
mkdir -p "$SCRIPT_DIR/backend/logs"
mkdir -p "$SCRIPT_DIR/logs"

# ==================== 环境检查函数 ====================

# 检查 Python 版本 (需要 >= 3.10)
check_python() {
    echo -e "${YELLOW}🔍 检查 Python 环境...${NC}"

    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ 错误: 未找到 python3${NC}"
        echo "请安装 Python 3.10 或更高版本:"
        echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
        echo "  Mac: brew install python3"
        return 1
    fi

    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
        echo -e "${RED}❌ 错误: Python 版本需要 >= 3.10, 当前版本: $PYTHON_VERSION${NC}"
        return 1
    fi

    echo -e "${GREEN}✓ Python $PYTHON_VERSION${NC}"
    return 0
}

# 检查 Node.js 版本 (需要 >= 18)
check_nodejs() {
    echo -e "${YELLOW}🔍 检查 Node.js 环境...${NC}"

    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ 错误: 未找到 Node.js${NC}"
        echo "请安装 Node.js 18 或更高版本:"
        echo "  访问 https://nodejs.org/ 下载安装"
        echo "  或使用 nvm: nvm install 18"
        return 1
    fi

    NODE_VERSION=$(node --version | cut -d'v' -f2)
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)

    if [ "$NODE_MAJOR" -lt 18 ]; then
        echo -e "${RED}❌ 错误: Node.js 版本需要 >= 18, 当前版本: $NODE_VERSION${NC}"
        return 1
    fi

    echo -e "${GREEN}✓ Node.js $NODE_VERSION${NC}"

    if command -v pnpm &> /dev/null; then
        echo -e "${GREEN}✓ 使用 pnpm 作为包管理器${NC}"
        PKG_MANAGER="pnpm"
    elif command -v npm &> /dev/null; then
        echo -e "${GREEN}✓ 使用 npm 作为包管理器${NC}"
        PKG_MANAGER="npm"
    else
        echo -e "${RED}❌ 错误: 未找到 npm 或 pnpm${NC}"
        return 1
    fi

    return 0
}

# 显示依赖文档位置
show_dependency_info() {
    echo ""
    echo -e "${BLUE}📋 依赖文档:${NC}"
    echo "   $DEPENDENCY_DOC"
    echo ""
    echo -e "${BLUE}📦 依赖文件位置:${NC}"
    echo "   后端: $REQUIREMENTS_FILE"
    echo "   前端: $PACKAGE_FILE"
    echo ""

    if [ -f "$REQUIREMENTS_FILE" ]; then
        echo -e "${BLUE}Python 后端依赖 (requirements.txt):${NC}"
        grep -E "^[a-zA-Z]" "$REQUIREMENTS_FILE" | grep -v "^#" | head -8 | sed 's/^/   - /'
        echo ""
    fi

    if [ -f "$PACKAGE_FILE" ]; then
        echo -e "${BLUE}Node.js 前端依赖 (package.json):${NC}"
        node -e "const pkg=require('$PACKAGE_FILE'); Object.keys(pkg.dependencies).slice(0,6).forEach(k=>console.log('   -',k+':',pkg.dependencies[k]))" 2>/dev/null || echo "   (请查看 package.json)"
        echo ""
    fi
}

# ==================== Setup 函数 ====================

# 设置 Python 虚拟环境
setup_venv() {
    local backend_dir="$SCRIPT_DIR/backend"
    local venv_dir="$backend_dir/venv"

    # Check backend directory exists
    if [ ! -d "$backend_dir" ]; then
        echo -e "${RED}❌ 错误: 后端目录不存在${NC}"
        echo -e "${RED}   期望路径: $backend_dir${NC}"
        return 1
    fi

    # Check requirements.txt exists
    if [ ! -f "$backend_dir/requirements.txt" ]; then
        echo -e "${RED}❌ 错误: requirements.txt 不存在${NC}"
        echo -e "${RED}   期望路径: $backend_dir/requirements.txt${NC}"
        return 1
    fi

    # Check if already in a virtual environment
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo -e "${BLUE}ℹ 已在虚拟环境中: $VIRTUAL_ENV${NC}"
        return 0
    fi

    cd "$backend_dir"

    # Check if venv exists
    if [ ! -d "$venv_dir" ]; then
        echo -e "${YELLOW}📦 创建虚拟环境...${NC}"

        if ! python3 -m venv venv 2>&1; then
            echo -e "${RED}❌ 错误: 创建虚拟环境失败${NC}"
            echo -e "${YELLOW}   可能原因:${NC}"
            echo -e "     - Python 3 未安装或版本过低"
            echo -e "     - python3-venv 包未安装 (Ubuntu/Debian: sudo apt install python3-venv)"
            return 1
        fi
        echo -e "${GREEN}✓ 虚拟环境已创建${NC}"
    else
        echo -e "${BLUE}ℹ 虚拟环境已存在${NC}"
    fi

    # Activate venv
    if [ ! -f "$venv_dir/bin/activate" ]; then
        echo -e "${RED}❌ 错误: 虚拟环境激活脚本不存在${NC}"
        return 1
    fi

    source "$venv_dir/bin/activate"
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 错误: 激活虚拟环境失败${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ 虚拟环境已激活${NC}"

    # Upgrade pip
    echo -e "${BLUE}   升级 pip...${NC}"
    pip install --upgrade pip -q 2>&1 > /dev/null

    # Install dependencies
    echo -e "${YELLOW}📦 安装 Python 依赖...${NC}"
    echo -e "${BLUE}   依赖文件: requirements.txt${NC}"
    pip install -r requirements.txt 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Python 依赖安装完成${NC}"
    else
        echo -e "${RED}❌ 错误: 安装 Python 依赖失败${NC}"
        echo -e "${YELLOW}   可能原因:${NC}"
        echo -e "     - 网络连接问题"
        echo -e "     - 依赖版本冲突"
        echo -e "     - 缺少系统依赖 (如 gcc, python3-dev)"
        return 1
    fi
}

# 安装前端依赖
setup_frontend() {
    cd "$SCRIPT_DIR/frontend"

    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 安装前端依赖...${NC}"
        echo -e "${BLUE}   依赖文件: package.json${NC}"

        if [ "$PKG_MANAGER" = "pnpm" ]; then
            pnpm install
        else
            npm install
        fi

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ 前端依赖安装完成${NC}"
        else
            echo -e "${RED}❌ 错误: 安装前端依赖失败${NC}"
            return 1
        fi
    else
        echo -e "${BLUE}ℹ 前端依赖已安装${NC}"
    fi
}

# Setup 命令 - 完整环境设置
setup_all() {
    echo "=========================================="
    echo "  Stock Investment System - 环境安装"
    echo "=========================================="
    echo ""

    # 环境检查
    check_python || exit 1
    echo ""
    check_nodejs || exit 1
    echo ""

    # 显示依赖信息
    show_dependency_info

    # 安装依赖
    echo -e "${YELLOW}📦 开始安装依赖...${NC}"
    echo ""

    setup_venv || exit 1
    echo ""
    setup_frontend || exit 1
    echo ""

    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}  ✓ 安装完成！${NC}"
    echo -e "${GREEN}==========================================${NC}"
    echo ""
    echo "启动项目:"
    echo "  ./start.sh backend   - 启动后端"
    echo "  ./start.sh frontend  - 启动前端"
    echo "  ./start.sh all       - 启动全部"
    echo ""
}

# ==================== 停止函数 ====================

# 停止后端服务
stop_backend() {
    echo -e "${YELLOW}🔄 正在停止后端服务...${NC}"

    # 方法1: 通过端口查找进程
    local backend_pid=$(lsof -ti:8080 2>/dev/null || true)

    if [ -n "$backend_pid" ]; then
        echo -e "${BLUE}   找到后端进程 (PID: $backend_pid)${NC}"
        kill $backend_pid 2>/dev/null
        sleep 1

        # 检查是否成功停止
        if ps -p $backend_pid > /dev/null 2>&1; then
            echo -e "${YELLOW}   强制终止后端进程...${NC}"
            kill -9 $backend_pid 2>/dev/null
            sleep 1
        fi
    fi

    # 方法2: 通过进程名查找
    local api_pids=$(pgrep -f "api_server.py" 2>/dev/null || true)
    if [ -n "$api_pids" ]; then
        for pid in $api_pids; do
            echo -e "${BLUE}   终止 api_server.py 进程 (PID: $pid)${NC}"
            kill $pid 2>/dev/null
        done
        sleep 1
    fi

    # 验证端口已释放
    if lsof -ti:8080 &>/dev/null; then
        echo -e "${RED}❌ 警告: 端口 8080 仍被占用${NC}"
        return 1
    else
        echo -e "${GREEN}✓ 后端服务已停止${NC}"
        return 0
    fi
}

# 停止前端服务
stop_frontend() {
    echo -e "${YELLOW}🔄 正在停止前端服务...${NC}"

    # 方法1: 通过端口查找进程
    local frontend_pid=$(lsof -ti:3000 2>/dev/null || true)

    if [ -n "$frontend_pid" ]; then
        echo -e "${BLUE}   找到前端进程 (PID: $frontend_pid)${NC}"
        kill $frontend_pid 2>/dev/null
        sleep 1

        # 检查是否成功停止
        if ps -p $frontend_pid > /dev/null 2>&1; then
            echo -e "${YELLOW}   强制终止前端进程...${NC}"
            kill -9 $frontend_pid 2>/dev/null
            sleep 1
        fi
    fi

    # 方法2: 通过进程名查找 (node/vite)
    local node_pids=$(pgrep -f "vite|npm.*dev" 2>/dev/null | head -5 || true)
    if [ -n "$node_pids" ]; then
        for pid in $node_pids; do
            # 检查是否是前端相关进程
            if ps -p $pid -o cmd= 2>/dev/null | grep -q "frontend"; then
                echo -e "${BLUE}   终止前端进程 (PID: $pid)${NC}"
                kill $pid 2>/dev/null
            fi
        done
        sleep 1
    fi

    # 验证端口已释放
    if lsof -ti:3000 &>/dev/null; then
        echo -e "${RED}❌ 警告: 端口 3000 仍被占用${NC}"
        return 1
    else
        echo -e "${GREEN}✓ 前端服务已停止${NC}"
        return 0
    fi
}

# 停止所有服务
stop_all_services() {
    stop_frontend
    stop_backend
    echo -e "${GREEN}✓ 所有服务已停止${NC}"
}

# 查看服务状态
status() {
    echo "=========================================="
    echo "  Stock Investment System - 服务状态"
    echo "=========================================="
    echo ""

    # 检查后端
    echo -e "${BLUE}后端服务 (端口 8080):${NC}"
    if lsof -ti:8080 &>/dev/null; then
        local backend_pid=$(lsof -ti:8080)
        echo -e "  ${GREEN}● 运行中${NC} (PID: $backend_pid)"
        ps -p $backend_pid -o pid,etime,cmd --no-headers 2>/dev/null | while read line; do
            echo -e "     $line"
        done
    else
        echo -e "  ${RED}○ 未运行${NC}"
    fi
    echo ""

    # 检查前端
    echo -e "${BLUE}前端服务 (端口 3000):${NC}"
    if lsof -ti:3000 &>/dev/null; then
        local frontend_pid=$(lsof -ti:3000)
        echo -e "  ${GREEN}● 运行中${NC} (PID: $frontend_pid)"
        ps -p $frontend_pid -o pid,etime,cmd --no-headers 2>/dev/null | while read line; do
            echo -e "     $line"
        done
    else
        echo -e "  ${RED}○ 未运行${NC}"
    fi
    echo ""
}

# ==================== 启动函数 ====================

# Function to start backend in background
start_backend_daemon() {
    echo -e "${YELLOW}🚀 Starting Backend (daemon mode)...${NC}"

    # 停止现有后端进程
    if lsof -ti:8080 &>/dev/null; then
        echo -e "${BLUE}   停止现有后端进程...${NC}"
        stop_backend
        sleep 1
    fi

    # Setup and activate venv
    setup_venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 错误: 虚拟环境设置失败${NC}"
        return 1
    fi

    # Check if Python file exists
    local api_server="$SCRIPT_DIR/backend/app/api_server.py"
    if [ ! -f "$api_server" ]; then
        echo -e "${RED}❌ 错误: 未找到后端启动文件${NC}"
        echo -e "${RED}   期望路径: $api_server${NC}"
        return 1
    fi

    # Create log file with timestamp
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backend_log="$SCRIPT_DIR/backend/logs/backend_${timestamp}.log"
    echo -e "${BLUE}   后端日志: $backend_log${NC}"

    # Start server in background
    echo -e "${GREEN}✓ 启动后端服务...${NC}"
    nohup python "$api_server" > "$backend_log" 2>&1 &
    BACKEND_PID=$!

    # Save PID to file
    echo $BACKEND_PID > "$SCRIPT_DIR/backend/.backend.pid"
    echo -e "${GREEN}✓ 后端 PID: $BACKEND_PID${NC}"

    # Wait for backend to start
    echo -e "${BLUE}   等待后端启动...${NC}"
    local max_wait=30
    local waited=0
    while [ $waited -lt $max_wait ]; do
        if curl -s http://localhost:8080/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ 后端健康检查通过${NC}"
            echo -e "${GREEN}✓ Backend running at http://localhost:8080${NC}"
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
        printf "\r${BLUE}   等待中... %ds/${max_wait}s${NC}" $waited
    done
    echo ""

    # Check if process is still running
    if ! ps -p $BACKEND_PID > /dev/null; then
        echo -e "${RED}❌ 错误: 后端启动失败${NC}"
        echo -e "${YELLOW}========== 后端错误日志 ==========${NC}"
        if [ -f "$backend_log" ]; then
            tail -30 "$backend_log" | while read line; do
                echo -e "${RED}   $line${NC}"
            done
        fi
        echo -e "${YELLOW}===================================${NC}"
        return 1
    fi

    echo -e "${YELLOW}⚠ 后端进程运行中，但健康检查未通过${NC}"
    echo -e "${YELLOW}   请稍后检查: curl http://localhost:8080/health${NC}"
    return 0
}

# Function to start frontend in background
start_frontend_daemon() {
    echo -e "${YELLOW}🚀 Starting Frontend (daemon mode)...${NC}"

    # 停止现有前端进程
    if lsof -ti:3000 &>/dev/null; then
        echo -e "${BLUE}   停止现有前端进程...${NC}"
        stop_frontend
        sleep 1
    fi

    cd "$SCRIPT_DIR/frontend"

    # Check if node is available
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Error: Node.js is not installed${NC}"
        return 1
    fi

    # Check node_modules
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
        npm install
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Error: Failed to install frontend dependencies${NC}"
            return 1
        fi
        echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
    else
        echo -e "${BLUE}ℹ Frontend dependencies already installed${NC}"
    fi

    # Create log file with timestamp
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local frontend_log="$SCRIPT_DIR/frontend/logs/frontend_${timestamp}.log"
    mkdir -p "$SCRIPT_DIR/frontend/logs"
    echo -e "${BLUE}   前端日志: $frontend_log${NC}"

    # Start dev server in background
    nohup npm run dev > "$frontend_log" 2>&1 &
    FRONTEND_PID=$!

    # Save PID to file
    echo $FRONTEND_PID > "$SCRIPT_DIR/frontend/.frontend.pid"
    echo -e "${GREEN}✓ 前端 PID: $FRONTEND_PID${NC}"

    # Wait for frontend to start
    echo -e "${BLUE}   等待前端启动...${NC}"
    local max_wait=15
    local waited=0
    while [ $waited -lt $max_wait ]; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Frontend running at http://localhost:3000${NC}"
            return 0
        fi
        sleep 1
        waited=$((waited + 1))
        printf "\r${BLUE}   等待中... %ds/${max_wait}s${NC}" $waited
    done
    echo ""

    # Check if process is still running
    if ! ps -p $FRONTEND_PID > /dev/null; then
        echo -e "${RED}❌ 前端启动失败${NC}"
        echo -e "${YELLOW}========== 前端错误日志 ==========${NC}"
        if [ -f "$frontend_log" ]; then
            tail -30 "$frontend_log"
        fi
        echo -e "${YELLOW}===================================${NC}"
        return 1
    fi

    echo -e "${YELLOW}⚠ 前端进程运行中，但端口未响应${NC}"
    echo -e "${YELLOW}   请稍后检查: curl http://localhost:3000${NC}"
    return 0
}

# Function to start backend (foreground mode - kept for compatibility)
start_backend() {
    echo -e "${YELLOW}🚀 Starting Backend (foreground mode)...${NC}"

    # 停止现有后端进程
    if lsof -ti:8080 &>/dev/null; then
        echo -e "${BLUE}   停止现有后端进程...${NC}"
        stop_backend
        sleep 1
    fi

    # Setup and activate venv
    setup_venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 错误: 虚拟环境设置失败${NC}"
        return 1
    fi

    # Check if Python file exists
    local api_server="$SCRIPT_DIR/backend/app/api_server.py"
    if [ ! -f "$api_server" ]; then
        echo -e "${RED}❌ 错误: 未找到后端启动文件${NC}"
        echo -e "${RED}   期望路径: $api_server${NC}"
        return 1
    fi

    # Create log file with timestamp
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backend_log="$SCRIPT_DIR/backend/logs/backend_${timestamp}.log"
    echo -e "${BLUE}   后端日志: $backend_log${NC}"

    # Start server in foreground
    echo -e "${GREEN}✓ 启动后端服务...${NC}"
    python "$api_server" 2>&1 | tee "$backend_log"
}

# Function to start frontend (foreground mode - kept for compatibility)
start_frontend() {
    echo -e "${YELLOW}🚀 Starting Frontend...${NC}"

    # 停止现有前端进程
    if lsof -ti:3000 &>/dev/null; then
        echo -e "${BLUE}   停止现有前端进程...${NC}"
        stop_frontend
        sleep 1
    fi

    cd "$SCRIPT_DIR/frontend"

    # Check if node is available
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Error: Node.js is not installed${NC}"
        exit 1
    fi

    # Check node_modules
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
        npm install
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Error: Failed to install frontend dependencies${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
    else
        echo -e "${BLUE}ℹ Frontend dependencies already installed${NC}"
    fi

    # Start dev server
    echo -e "${GREEN}✓ Frontend running at http://localhost:3000${NC}"
    npm run dev
}

# Function to start both (daemon mode)
start_all() {
    echo -e "${YELLOW}🚀 Starting both services (daemon mode)...${NC}"

    # 停止现有服务进程
    echo -e "${BLUE}   停止现有服务进程...${NC}"
    stop_all_services
    sleep 1
    echo ""

    # Start backend in background
    start_backend_daemon
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 后端启动失败${NC}"
        return 1
    fi
    echo ""

    # Start frontend in background
    start_frontend_daemon
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 前端启动失败${NC}"
        return 1
    fi
    echo ""

    echo -e "${GREEN}==========================================${NC}"
    echo -e "${GREEN}  ✓ 所有服务已启动${NC}"
    echo -e "${GREEN}==========================================${NC}"
    echo ""
    echo -e "${BLUE}访问地址:${NC}"
    echo -e "  前端: ${CYAN}http://localhost:3000${NC}"
    echo -e "  后端: ${CYAN}http://localhost:8080${NC}"
    echo ""
    echo -e "${BLUE}管理命令:${NC}"
    echo "  ./start.sh status     - 查看服务状态"
    echo "  ./start.sh stop       - 停止所有服务"
    echo "  ./start.sh restart    - 重启所有服务"
    echo ""
}

# ==================== 重启函数 ====================

# 重启后端
restart_backend() {
    echo -e "${CYAN}🔄 正在重启后端服务...${NC}"
    stop_backend
    echo ""
    sleep 1
    start_backend_daemon
}

# 重启前端
restart_frontend() {
    echo -e "${CYAN}🔄 正在重启前端服务...${NC}"
    stop_frontend
    echo ""
    sleep 1
    start_frontend_daemon
}

# 重启所有服务
restart_all() {
    echo -e "${CYAN}🔄 正在重启所有服务...${NC}"
    stop_all_services
    echo ""
    sleep 1
    start_all
}

# Main
case "$1" in
    setup)
        setup_all
        ;;
    backend)
        start_backend_daemon
        ;;
    backend-fg)
        start_backend
        ;;
    frontend)
        start_frontend_daemon
        ;;
    frontend-fg)
        start_frontend
        ;;
    all)
        start_all
        ;;
    restart)
        restart_all
        ;;
    restart-backend)
        restart_backend
        ;;
    restart-frontend)
        restart_frontend
        ;;
    stop)
        stop_all_services
        ;;
    stop-backend)
        stop_backend
        ;;
    stop-frontend)
        stop_frontend
        ;;
    status)
        status
        ;;
    *)
        echo "Stock Investment System - 启动脚本"
        echo ""
        echo "用法: $0 {setup|backend|frontend|all|restart|stop|status}"
        echo ""
        echo "  setup           - 完整环境设置（检查 + 安装所有依赖）"
        echo "  backend         - 启动后端 API 服务 (后台运行)"
        echo "  backend-fg      - 启动后端服务 (前台运行)"
        echo "  frontend        - 启动前端开发服务器 (后台运行)"
        echo "  frontend-fg     - 启动前端服务 (前台运行)"
        echo "  all             - 启动全部服务 (后台运行)"
        echo "  restart         - 重启所有服务"
        echo "  restart-backend - 重启后端服务"
        echo "  restart-frontend- 重启前端服务"
        echo "  stop            - 停止所有服务"
        echo "  stop-backend    - 停止后端服务"
        echo "  stop-frontend   - 停止前端服务"
        echo "  status          - 查看服务状态"
        echo ""
        echo "依赖文档: docs/Dependencies.md"
        echo ""
        exit 1
        ;;
esac