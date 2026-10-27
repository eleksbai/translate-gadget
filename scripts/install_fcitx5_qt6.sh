#!/usr/bin/env bash
# =============================================================
# fcitx5-qt Qt6 输入法插件安装脚本
#
# 背景：Ubuntu 22.04 仓库只提供 fcitx5-frontend-qt5，缺少 Qt6 版
# 插件，导致 PySide6 (Qt6) 程序无法使用 fcitx5 输入中文。
# 本脚本从源码编译 fcitx5-qt（仅 Qt6），并安装到：
#   1. 系统 Qt6 插件目录 (/usr/lib/.../qt6/plugins/platforminputcontexts)
#   2. PySide6 venv 自带插件目录 (可选，默认执行)
#
# 用法：
#   ./install_fcitx5_qt6.sh              # 使用默认 venv 路径
#   VENV=/path/to/.venv ./install_fcitx5_qt6.sh
#   SKIP_SYSTEM_INSTALL=1 ./install_fcitx5_qt6.sh   # 不装到系统目录
# =============================================================
set -euo pipefail

# ---------- 配置 ----------
SRC_DIR="${SRC_DIR:-$HOME/fcitx5-qt-src}"
VENV="${VENV:-/home/ubuntu/code/translate-gadget/.venv}"
GIT_URL="https://github.com/fcitx/fcitx5-qt.git"
QT6_PLUGIN_SYS_DIR="/usr/lib/x86_64-linux-gnu/qt6/plugins/platforminputcontexts"

log() { echo -e "\033[1;32m[install]\033[0m $*"; }
err() { echo -e "\033[1;31m[error]\033[0m $*" >&2; }

# ---------- 1. 安装构建依赖 ----------
log "步骤 1/4: 安装构建依赖 (需要 sudo)"
sudo apt update
sudo apt install -y git cmake extra-cmake-modules \
    fcitx5-dev libdbus-1-dev qt6-base-dev libxcb-cursor-dev

# ---------- 2. 获取源码 ----------
log "步骤 2/4: 获取 fcitx5-qt 源码 -> ${SRC_DIR}"
if [ -d "${SRC_DIR}/.git" ]; then
    git -C "${SRC_DIR}" fetch --all
    git -C "${SRC_DIR}" checkout main
    git -C "${SRC_DIR}" pull
else
    git clone "${GIT_URL}" "${SRC_DIR}"
fi

# ---------- 3. 编译（仅启用 Qt6，关闭 Qt5/GTK 加速构建） ----------
log "步骤 3/4: 编译 fcitx5-qt (Qt6 only)"
cd "${SRC_DIR}"
cmake -B build \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr \
    -DENABLE_QT5=OFF \
    -DENABLE_QT6=ON \
    -DENABLE_GTK2=OFF \
    -DENABLE_GTK3=OFF \
    -DENABLE_GTK4=OFF
cmake --build build -j"$(nproc)"

PLUGIN_SO="${SRC_DIR}/build/qt6/platforminputcontexts/libfcitx5platforminputcontextplugin.so"
if [ ! -f "${PLUGIN_SO}" ]; then
    err "未找到编译产物: ${PLUGIN_SO}"
    err "请检查编译输出，或确认该版本仓库的 Qt6 构建目录结构"
    exit 1
fi

# ---------- 4. 安装 ----------
log "步骤 4/4: 安装插件"

# 4a. 系统目录（同时安装依赖库 libFcitx5Qt6*Addons，插件运行需要）
if [ "${SKIP_SYSTEM_INSTALL:-0}" != "1" ]; then
    log "安装到系统目录 ${QT6_PLUGIN_SYS_DIR} (需要 sudo)"
    sudo mkdir -p "${QT6_PLUGIN_SYS_DIR}"
    sudo cmake --install build
else
    log "SKIP_SYSTEM_INSTALL=1，跳过系统安装（插件可能因缺少依赖库无法加载）"
fi

# 4b. PySide6 venv 目录（如果存在）
if [ -d "${VENV}" ]; then
    PYSIDE_PLUGIN_DIR="$(find "${VENV}" -type d -name platforminputcontexts 2>/dev/null | head -1)"
    if [ -n "${PYSIDE_PLUGIN_DIR}" ] && [ -d "${PYSIDE_PLUGIN_DIR}" ]; then
        cp "${PLUGIN_SO}" "${PYSIDE_PLUGIN_DIR}/"
        log "已复制到 PySide6 插件目录: ${PYSIDE_PLUGIN_DIR}"
    else
        err "在 ${VENV} 中未找到 PySide6 platforminputcontexts 目录"
    fi
else
    log "venv 不存在 (${VENV})，跳过 venv 安装"
fi

# ---------- 验证提示 ----------
cat <<EOF

=============================================================
安装完成！验证步骤：
  1. 确认环境变量:   echo \$QT_IM_MODULE     # 应为 fcitx
  2. 确认 fcitx5 在运行:  pgrep fcitx5 || fcitx5 &
  3. 运行测试脚本:
     ${VENV}/bin/python scripts/test_ime.py
  4. 若加载失败，检查插件依赖:
     ldd ${PLUGIN_SO} | grep "not found"
=============================================================
EOF
