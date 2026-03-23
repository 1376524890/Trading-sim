# 依赖文档

本文档列出 Stock Investment System 的所有依赖项及安装说明。

## 依赖文件位置

| 类型 | 文件路径 | 说明 |
|------|---------|------|
| Python 后端 | `backend/requirements.txt` | Python 包依赖 |
| Node.js 前端 | `frontend/package.json` | npm/pnpm 包依赖 |

## 系统要求

- **Python**: 3.10 或更高版本
- **Node.js**: 18 或更高版本
- **包管理器**: npm 7+ 或 pnpm

## Python 后端依赖

### Web 框架
- fastapi>=0.104.0
- uvicorn[standard]>=0.24.0
- pydantic>=2.5.0

### 数据处理
- pandas>=2.0.0
- numpy>=1.24.0

### 数据获取
- akshare>=1.11.0 (A股数据)
- yfinance>=0.2.28 (美股数据)
- requests>=2.31.0
- baostock>=0.8.9 (备选数据源)

### 日志
- loguru>=0.7.0

### 日期/时间
- python-dateutil>=2.8.2
- pytz>=2023.3

### 配置
- python-dotenv>=1.0.0

## Node.js 前端依赖

### 核心框架
- vue: ^3.5.13
- typescript: ^5.7.2
- pinia: ^2.3.0
- vue-router: ^4.5.0

### 图表
- lightweight-charts: ^5.1.0 (K线图)
- chart.js: ^4.4.7
- vue-chartjs: ^5.3.2

### HTTP 客户端
- axios: ^1.7.9

### UI 组件
- @heroicons/vue: ^2.2.0

### 构建工具
- vite: ^6.0.5
- @vitejs/plugin-vue: ^5.2.1

### CSS 框架
- tailwindcss: ^3.4.17
- autoprefixer: ^10.4.20
- postcss: ^8.4.49

## 快速安装

运行项目根目录的启动脚本：

```bash
# 完整安装（检查环境 + 安装依赖）
./start.sh setup

# 或直接启动（会自动安装缺失的依赖）
./start.sh all
```

## 手动安装

### 后端

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 .\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 前端

```bash
cd frontend

# 使用 npm
npm install

# 或使用 pnpm（推荐）
pnpm install
```

## 可选依赖

### TA-Lib (技术分析库)

```bash
# 需要先安装系统库
# Ubuntu/Debian:
sudo apt-get install ta-lib

# macOS:
brew install ta-lib

# 然后安装 Python 包
pip install TA-Lib>=0.4.32
```

### Tushare (备选数据源，需要 API Token)

```bash
pip install tushare>=1.3.0
```

## 验证安装

```bash
# 检查 Python
cd backend
source venv/bin/activate
python -c "import fastapi, pandas, akshare; print('Python 依赖 OK')"

# 检查 Node.js
cd ../frontend
node -e "console.log('Node.js 版本:', process.version)"
npm list vue axios pinia --depth=0 2>/dev/null || echo "npm 依赖已安装"
```

## 常见问题

### Python 版本过低
- 确保 Python >= 3.10
- 使用 pyenv 或 conda 管理多版本

### Node.js 版本过低
- 建议升级到 Node.js 18 LTS 或更高
- 使用 nvm 管理多版本: `nvm install 18 && nvm use 18`

### 安装失败
- 检查网络连接
- 尝试更换镜像源:
  - pip: `pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple`
  - npm: `npm config set registry https://registry.npmmirror.com`
