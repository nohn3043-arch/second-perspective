#!/bin/bash
# =============================================================================
# GCAE Security Engine - APK 一键打包脚本
# 用法：
#   bash build_apk.sh          # 默认 debug 模式
#   bash build_apk.sh debug    # Debug 模式打包
#   bash build_apk.sh release  # Release 模式打包
#   bash build_apk.sh clean    # 清理构建缓存后打包
# =============================================================================

set -e

# 构建模式（默认 debug）
BUILD_MODE="${1:-debug}"

# 如果第一个参数是 clean，则清理后再构建
if [ "$BUILD_MODE" = "clean" ]; then
    echo "[INFO] 清理构建缓存..."
    rm -rf .buildozer bin build.log
    BUILD_MODE="debug"
fi

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_info "============================================"
print_info "  GCAE Security Engine - APK 打包工具"
print_info "  构建模式: $BUILD_MODE"
print_info "============================================"
echo ""

# =============================================================================
# 第一步：检查环境
# =============================================================================
print_info "检查运行环境..."

# 检查是否在 WSL 中
if ! grep -qi microsoft /proc/version; then
    print_warning "未检测到 WSL 环境，如果是原生 Linux 可以继续"
fi

# 检查是否为 root
if [ "$EUID" -eq 0 ]; then
    print_warning "检测到 root 用户，建议使用普通用户运行"
    SUDO=""
else
    SUDO="sudo"
fi

# 检查磁盘空间（至少需要 10GB）
AVAIL_SPACE=$(df -h . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$(echo "$AVAIL_SPACE < 10" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
    print_warning "磁盘空间不足 10GB，可能导致构建失败"
    print_info "可用空间: ${AVAIL_SPACE}GB"
fi

# 检查代理设置
if [ -n "$HTTP_PROXY" ] || [ -n "$HTTPS_PROXY" ]; then
    print_info "检测到代理设置"
fi

print_success "环境检查完成"
echo ""

# =============================================================================
# 第二步：安装系统依赖
# =============================================================================
print_info "安装系统依赖（首次运行需要几分钟）..."

$SUDO apt update -qq

# 基础编译工具
print_info "安装基础编译工具..."
$SUDO apt install -y -qq build-essential git python3 python3-dev python3-pip > /dev/null 2>&1

# Java
print_info "安装 Java 17..."
$SUDO apt install -y -qq openjdk-17-jdk openjdk-17-jre > /dev/null 2>&1

# 开发库
print_info "安装开发库..."
$SUDO apt install -y -qq libffi-dev libssl-dev > /dev/null 2>&1
$SUDO apt install -y -qq libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev > /dev/null 2>&1
$SUDO apt install -y -qq libjpeg-dev libpng-dev zlib1g-dev > /dev/null 2>&1
$SUDO apt install -y -qq autoconf libtool pkg-config > /dev/null 2>&1
$SUDO apt install -y -qq zip unzip wget curl > /dev/null 2>&1

print_success "系统依赖安装完成"
echo ""

# =============================================================================
# 第三步：配置 Java 环境
# =============================================================================
print_info "配置 Java 环境..."

export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# 检查 Java
if java -version 2>&1 | grep -q "17"; then
    print_success "Java 17 配置成功"
else
    print_error "Java 配置失败"
    exit 1
fi

echo ""

# =============================================================================
# 第四步：安装 Python 依赖
# =============================================================================
print_info "安装 Python 依赖..."

python3 -m pip install --upgrade pip setuptools wheel -q

print_info "安装 Cython..."
python3 -m pip install cython==0.29.37 -q

print_info "安装 Buildozer..."
python3 -m pip install buildozer==1.5.0 -q

print_success "Python 依赖安装完成"
echo ""

# =============================================================================
# 第五步：检查项目文件
# =============================================================================
print_info "检查项目文件..."

if [ ! -f "main.py" ]; then
    print_error "找不到 main.py，请确认在正确的项目目录中"
    exit 1
fi

if [ ! -f "buildozer.spec" ]; then
    print_error "找不到 buildozer.spec"
    exit 1
fi

print_success "项目文件检查通过"
echo ""

# =============================================================================
# 第六步：开始打包
# =============================================================================
print_info "============================================"
print_info "  开始打包 APK"
print_info "============================================"
print_warning "首次运行会下载 Android SDK/NDK（约 2GB），请耐心等待..."
print_warning "编译过程可能需要 10-30 分钟，取决于机器性能"
echo ""

# 确保 bin 目录存在
mkdir -p bin

# 运行 buildozer
print_info "执行 buildozer android $BUILD_MODE..."
echo ""

buildozer android "$BUILD_MODE" 2>&1 | tee build.log

BUILD_EXIT_CODE=${PIPESTATUS[0]}

echo ""

# =============================================================================
# 第七步：检查结果
# =============================================================================
if [ $BUILD_EXIT_CODE -eq 0 ]; then
    print_success "编译成功！"
    
    # 查找生成的 APK
    APK_FILE=$(ls -t bin/*.apk 2>/dev/null | head -1)
    
    if [ -n "$APK_FILE" ]; then
        print_success "APK 文件: $APK_FILE"
        
        APK_SIZE=$(du -h "$APK_FILE" | cut -f1)
        print_info "文件大小: $APK_SIZE"
        
        # 尝试复制到 Windows 桌面
        WIN_USERNAME=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r')
        if [ -n "$WIN_USERNAME" ]; then
            DESKTOP_PATH="/mnt/c/Users/$WIN_USERNAME/Desktop"
            if [ -d "$DESKTOP_PATH" ]; then
                cp "$APK_FILE" "$DESKTOP_PATH/"
                print_success "已复制到 Windows 桌面"
            fi
        fi
        
        echo ""
        print_info "============================================"
        print_success "  APK 打包完成！"
        print_info "============================================"
        print_info "APK 位置: $APK_FILE"
        print_info "如果在 WSL 中，文件也已复制到 Windows 桌面"
        print_info "将 APK 传到手机上即可安装"
        echo ""
    else
        print_error "编译成功但找不到 APK 文件"
        print_info "请检查 bin/ 目录"
    fi
else
    print_error "编译失败，退出码: $BUILD_EXIT_CODE"
    print_info "查看 build.log 获取详细错误信息"
    echo ""
    print_info "常见问题："
    print_info "1. 网络问题 - 检查网络连接或使用代理"
    print_info "2. 内存不足 - 增加 swap 空间"
    print_info "3. 依赖缺失 - 确认所有依赖已安装"
    exit 1
fi
