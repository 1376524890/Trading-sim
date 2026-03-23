#!/bin/bash
# Stock Investment System - 自动安装脚本
# 一键安装前后端所有依赖

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Stock Investment System - 安装脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查 Python 版本
check_python() {
    echo -e "${YELLOW}[1/4] 检查 Python 环境...${NC}"

    if ! command_exists python3; then
        echo -e "${RED}错误: 未找到 Python3${NC}"
        echo "请安装 Python 3.10 或更高版本:"
        echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip python3-venv"
        echo "  Mac: brew install python3"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
    REQUIRED_VERSION="3.10"

    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        echo -e "${RED}错误: Python 版本需要 >= 3.10, 当前版本: $PYTHON_VERSION${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Python $PYTHON_VERSION 已安装${NC}"
}

# 检查 Node.js 版本
check_nodejs() {
    echo -e "${YELLOW}[2/4] 检查 Node.js 环境...${NC}"

    if ! command_exists node; then
        echo -e "${RED}错误: 未找到 Node.js${NC}"
        echo "请安装 Node.js 18 或更高版本:"
        echo "  访问 https://nodejs.org/ 下载安装"
        echo "  或使用 nvm: nvm install 18"
        exit 1
    fi

    NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d. -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        echo -e "${RED}错误: Node.js 版本需要 >= 18, 当前版本: $(node --version)${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Node.js $(node --version) 已安装${NC}"

    # 检查 npm 或 pnpm
    if command_exists pnpm; then
        PKG_MANAGER="pnpm"
        echo -e "${GREEN}✓ 使用 pnpm 作为包管理器${NC}"
    elif command_exists npm; then
        PKG_MANAGER="npm"
        echo -e "${GREEN}✓ 使用 npm 作为包管理器${NC}"
    else
        echo -e "${RED}错误: 未找到 npm 或 pnpm${NC}"
        exit 1
    fi
}

# 安装后端依赖
install_backend() {
    echo -e "${YELLOW}[3/4] 安装后端依赖...${NC}"

    cd "$PROJECT_ROOT/backend"

    # 创建虚拟环境（如果不存在）
    if [ ! -d "venv" ]; then
        echo "创建 Python 虚拟环境..."
        python3 -m venv venv
    fi

    # 激活虚拟环境
    source venv/bin/activate

    # 升级 pip
    pip install --upgrade pip

    # 安装依赖
    echo "安装 Python 依赖包..."
    pip install -r requirements.txt

    echo -e "${GREEN}✓ 后端依赖安装完成${NC}"
}

# 安装前端依赖
install_frontend() {
    echo -e "${YELLOW}[4/4] 安装前端依赖...${NC}"

    cd "$PROJECT_ROOT/frontend"

    # 安装依赖
    if [ "$PKG_MANAGER" = "pnpm" ]; then
        pnpm install
    else
        npm install
    fi

    echo -e "${GREEN}✓ 前端依赖安装完成${NC}"
}

# 显示完成信息
show_completion() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  安装完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "启动项目:"
    echo ""
    echo "1. 启动后端服务器:"
    echo -e "   ${BLUE}cd backend && source venv/bin/activate && python app/api_server.py${NC}"
    echo ""
    echo "2. 启动前端开发服务器:"
    if [ "$PKG_MANAGER" = "pnpm" ]; then
        echo -e "   ${BLUE}cd frontend && pnpm dev${NC}"
    else
        echo -e "   ${BLUE}cd frontend && npm run dev${NC}"
    fi
    echo ""
    echo "或使用一体化启动脚本:"
    echo -e "   ${BLUE}./start.sh${NC}"
    echo ""
}

# 主流程
main() {
    check_python
    check_nodejs
    install_backend
    install_frontend
    show_completion
}

main "$@"
