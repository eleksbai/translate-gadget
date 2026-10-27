# Translate Gadget

一个基于 PySide6 的桌面翻译小工具，支持 Windows 和 Ubuntu（Wayland）。

## 功能特性

- **透明背景**：窗口背景完全透明，融入桌面环境
- **固定置顶**：始终显示在屏幕最上层
- **鼠标穿透**：非输入状态下鼠标事件透传到底层应用，不阻挡正常操作
- **快捷键聚焦**：通过全局热键激活输入焦点，无需鼠标点击（快捷键可在设置中自定义）
- **翻译能力**：支持中→英、英→中双向翻译，自动检测输入语言方向
- **翻译历史**：内存缓存最近 1000 条翻译记录（程序退出后清空）
- **结果展示**：翻译结果在输入框下方展开显示，点击可复制
- **系统托盘**：托盘图标 + 右键菜单（打开设置、退出程序）
- **设置页面**：可视化配置翻译 API 地址、App ID、密钥、快捷键等参数，设置持久化存储

## 技术方案

### 技术栈

| 组件 | 选型 | 说明 |
|------|------|------|
| GUI 框架 | PySide6 (Qt 6) | 跨平台原生渲染 |
| 全局热键 | pynput | 跨平台热键监听 |
| 翻译 API | 待定 | 先搭框架，实现细节待定 |
| 配置持久化 | QSettings | Qt 内置配置存储，跨平台自动选择后端（Windows: 注册表，Linux: INI 文件） |
| 打包分发 | Nuitka | Python 编译为 C 再编译为机器码，启动快、代码保护强 |

### 窗口属性

```
FramelessWindowHint          → 无边框
WindowStaysOnTopHint         → 始终置顶
WA_TranslucentBackground     → 背景透明
WA_ShowWithoutActivating     → 显示时不抢夺焦点
```

### 鼠标穿透实现

穿透是本项目的核心技术难点。采用分层策略：默认使用 Qt 属性穿透，Wayland 下以 layer-shell 协议作为备选方案。

#### 默认方案：Qt 属性穿透（跨平台通用）

通过 Qt 的 `WA_TransparentForMouseEvents` 属性控制窗口是否接收鼠标事件：

```python
from PySide6.QtCore import Qt

# 开启穿透：鼠标事件透传到底层应用
window.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

# 关闭穿透：窗口正常接收鼠标事件（输入状态）
window.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
```

- 非输入状态时开启穿透，输入状态时关闭穿透
- 优点：跨平台通用，Windows 和 Linux 均可用
- 缺点：穿透状态下窗口完全不可交互，切换依赖状态控制逻辑

#### 备选方案：Wayland layer-shell 协议

当 Qt 属性穿透在 Wayland 下表现不佳时，使用 `layer-shell-qt` 库通过 layer-shell 协议实现更精细的控制：

```python
# 需额外依赖：layer-shell-qt
# 通过 layer-shell 将窗口设为 overlay layer，控制输入区域
```

> 注意：X11 不再支持。Ubuntu 环境需使用 Wayland 会话。

### 全局热键

使用 `pynput` 监听全局按键，触发时激活窗口并聚焦输入框。默认快捷键 `Ctrl+Alt+T`，用户可在设置页面自定义修改。

```python
from pynput import keyboard

def on_activate():
    """热键触发：显示窗口 + 聚焦输入框"""
    window.show_and_focus()

hotkey = keyboard.GlobalHotKeys({'<ctrl>+<alt>+t': on_activate})
hotkey.start()
```

**快捷键冲突检测：**

设置页面修改快捷键时，需进行系统级冲突检测：

- **格式校验**：必须为修饰键（Ctrl/Alt/Shift/Meta）+ 字母/数字 的组合
- **系统冲突检测**：检查是否与系统或常见应用的快捷键冲突（如 `Ctrl+C`、`Ctrl+V`、`Alt+F4` 等），冲突时给出警告提示
- 用户确认后可强制使用冲突快捷键

### 翻译 API

预留统一接口，后续对接具体翻译服务：

```python
class TranslatorBase:
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        raise NotImplementedError
```

### 语言检测

支持中→英、英→中双向翻译，自动检测输入语言方向：

- **检测规则**：按字符比例判定——统计输入中的中文字符与英文字符占比，中文字符多则判定为中文（翻译为英文），反之判定为英文（翻译为中文）
- **适用场景**：短文本，单次翻译内容为两三句话
- **混合文本处理**：中英文混合输入（如"这个feature不错"）时，按字符比例自动判定主语言方向

### 翻译历史

翻译结果缓存在内存中，程序退出后清空：

- **缓存上限**：默认 1000 条
- **存储方式**：仅内存，不持久化到文件
- **展示方式**：翻译结果在输入框下方展开显示，点击可复制

### 系统托盘

提供系统托盘图标和右键菜单：

- **托盘图标**：使用占位图标（后续替换为正式设计）
- **右键菜单项**：
  - 「设置」—— 打开设置对话框
  - 「退出」—— 退出程序

### 窗口位置

- **默认位置**：屏幕底部居中
- **可拖拽**：用户可拖拽窗口到任意位置，位置在会话内保持

### 设置页面

提供独立的设置对话框，用于配置翻译 API 连接参数和快捷键：

**可配置项：**

| 字段 | 说明 | 示例 |
|------|------|------|
| API 地址 | 翻译服务的 Base URL | `https://api.example.com/v1` |
| App ID | 服务分配的应用标识 | `my-app-id` |
| 密钥 | 服务分配的认证密钥 | `sk-xxxxxxxxxxxx` |
| 快捷键 | 全局激活热键（含冲突检测） | `Ctrl+Alt+T` |

**交互设计：**

- 通过系统托盘菜单打开设置对话框
- 对话框为模态窗口，包含 API 配置字段和快捷键设置
- 快捷键字段提供「录入」按钮，点击后按下目标组合键自动捕获（如 `Ctrl+Alt+T`）
- 提供「测试连接」按钮，验证 API 配置是否可用
- 点击「保存」后配置立即生效并持久化
- 点击「取消」丢弃未保存的修改

**持久化方案：**

使用 `QSettings` 存储配置，自动适配平台后端：

```python
from PySide6.QtCore import QSettings

class ConfigManager:
    SETTINGS_ORG = "TranslateGadget"
    SETTINGS_APP = "TranslateGadget"

    def __init__(self):
        self.settings = QSettings(self.SETTINGS_ORG, self.SETTINGS_APP)

    def save_api_config(self, api_url: str, app_id: str, secret_key: str):
        self.settings.setValue("api/url", api_url)
        self.settings.setValue("api/app_id", app_id)
        self.settings.setValue("api/secret_key", secret_key)
        self.settings.sync()

    def save_hotkey(self, hotkey_str: str):
        self.settings.setValue("hotkey", hotkey_str)
        self.settings.sync()

    def load_api_config(self) -> dict:
        return {
            "url": self.settings.value("api/url", ""),
            "app_id": self.settings.value("api/app_id", ""),
            "secret_key": self.settings.value("api/secret_key", ""),
        }

    def load_hotkey(self) -> str:
        return self.settings.value("hotkey", "<ctrl>+<alt>+t")
```

存储位置：
- **Windows**：注册表 `HKEY_CURRENT_USER\TranslateGadget\TranslateGadget`
- **Linux**：`~/.config/TranslateGadget/TranslateGadget.conf`（XDG 标准 INI 文件）

## 项目结构

采用 Python 主流 src layout，包名与项目名一致（`translate_gadget`）：

```
translate-gadget/
├── pyproject.toml                  # 项目元数据 + 依赖声明（uv 管理）
├── README.md
├── src/
│   └── translate_gadget/
│       ├── __init__.py             # 包初始化 + 版本信息
│       ├── __main__.py             # 入口（python -m translate_gadget）
│       ├── window.py               # 主窗口（透明、置顶、穿透、可拖拽）
│       ├── hotkey.py               # 全局热键管理（含冲突检测）
│       ├── translator.py           # 翻译 API 接口（框架）
│       ├── history.py              # 翻译历史管理（内存缓存，1000 条上限）
│       ├── config.py               # 配置管理（QSettings 持久化）
│       ├── tray.py                 # 系统托盘图标与右键菜单
│       ├── settings_dialog.py      # 设置对话框（API 配置、快捷键）
│       └── utils.py                # 工具函数（语言检测等）
├── assets/
│   └── icon.png                    # 应用图标（占位）
└── tests/
    └── ...
```

**设计说明：**

| 决策 | 理由 |
|------|------|
| `src/` layout | 防止开发时意外导入未安装的包，Python 社区推荐实践 |
| `__main__.py` 入口 | 支持 `python -m translate_gadget` 运行；同时通过 `pyproject.toml` 的 `[project.scripts]` 注册 `translate-gadget` 命令，安装后可直接在终端执行 |
| 语言检测放入 `utils.py` | 函数逻辑简单（统计字符比例），不值得独立模块 |
| `tests/` 与 `src/` 平级 | pytest 默认发现模式，测试代码不会被打入生产包 |
| 依赖用 `pyproject.toml` 管理 | 已有 uv 构建配置，无需额外 `requirements.txt` |

## 运行环境

- Python 3.10+
- Windows 10/11 或 Ubuntu 22.04+（Wayland 会话）

## 安装与运行

```bash
# 安装依赖（使用 uv）
uv sync

# 运行
uv run python -m translate_gadget

# 或者安装后直接运行
uv run translate-gadget
```

## 打包构建

使用 Nuitka 将 Python 代码编译为 C 再编译为原生机器码，获得更快的启动速度和更强的代码保护。

### 环境要求

- C 编译器：Windows 需安装 [MinGW64](https://www.mingw-w64.org/) 或 MSVC；Linux 需安装 `gcc`
- Nuitka 及依赖：

```bash
pip install nuitka ordered-set
```

### 打包命令

#### Windows

```bash
python -m nuitka ^
    --standalone ^
    --onefile ^
    --enable-plugin=pyside6 ^
    --windows-icon-from-ico=assets/icon.ico ^
    --windows-console-mode=disable ^
    --output-filename=translate-gadget.exe ^
    src/translate_gadget/__main__.py
```

#### Linux

```bash
python -m nuitka \
    --standalone \
    --onefile \
    --enable-plugin=pyside6 \
    --output-filename=translate-gadget \
    src/translate_gadget/__main__.py
```

### 关键参数说明

| 参数 | 说明 |
|------|------|
| `--standalone` | 打包所有依赖，不依赖目标机器的 Python 环境 |
| `--onefile` | 输出单文件可执行程序 |
| `--enable-plugin=pyside6` | 启用 PySide6 插件，自动收集 Qt 运行时资源 |
| `--windows-icon-from-ico` | 设置 Windows 可执行文件图标 |
| `--windows-console-mode=disable` | 禁用控制台窗口（GUI 程序不需要） |

### 注意事项

- 首次编译需要 C 编译器，Nuitka 会自动检测或使用 `ccache` 加速后续编译
- PySide6 体积较大，打包后文件约 60-100 MB，属正常范围
- 若遇到 Qt 插件缺失（如样式、图片格式），需手动添加 `--include-qt-plugins` 指定

## 待决事项

- [x] ~~翻译 API 选型~~ → 改为由用户在设置页面自行配置 API 地址与凭证
- [x] ~~语言方向~~ → 中→英 / 英→中，自动检测输入语言（按字符比例判定）
- [x] ~~窗口位置~~ → 默认底部居中，允许用户拖拽
- [x] ~~历史记录~~ → 内存缓存，上限 1000 条，重启丢失
- [x] ~~系统托盘~~ → 托盘图标 + 右键菜单（设置、退出）
- [x] ~~快捷键自定义~~ → 设置页可修改，含系统级冲突检测
- [x] ~~鼠标穿透方案~~ → Qt 属性穿透（默认）+ layer-shell（备选）
- [x] ~~平台支持~~ → 仅 Wayland，不支持 X11
