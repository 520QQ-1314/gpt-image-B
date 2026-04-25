@echo off
echo ========================================
echo    AI绘画平台 - 一键启动脚本 v1.0
echo ========================================
echo.

:: 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，正在下载安装...
    curl -L https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe -o python_installer.exe
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1
    del python_installer.exe
)

:: 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Node.js，正在下载安装...
    curl -L https://nodejs.org/dist/v18.17.0/node-v18.17.0-x64.msi -o node_installer.msi
    msiexec /i node_installer.msi /quiet
    del node_installer.msi
)

:: 安装Git
git --version >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装Git...
    curl -L https://github.com/git-for-windows/git/releases/download/v2.41.0.windows.1/Git-2.41.0-64-bit.exe -o git_installer.exe
    git_installer.exe /VERYSILENT
    del git_installer.exe
)

echo [信息] 创建虚拟环境...
python -m venv venv
call venv\Scripts\activate.bat

echo [信息] 安装后端依赖...
pip install -r backend\requirements.txt

echo [信息] 安装前端依赖...
cd frontend
npm install
cd ..

echo [信息] 启动后端服务...
start cmd /k "call venv\Scripts\activate.bat && python backend\main.py"

echo [信息] 等待后端启动...
timeout /t 3

echo [信息] 启动前端服务...
start cmd /k "cd frontend && npm start"

echo [信息] 等待前端启动...
timeout /t 5

echo [信息] 正在打开浏览器...
start http://localhost:3000

echo.
echo ✅ AI绘画平台已成功启动！
echo 前端地址: http://localhost:3000
echo 后端地址: http://localhost:8000
echo API文档:  http://localhost:8000/docs
echo.
pause
