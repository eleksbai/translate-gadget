# Translate Gadget

一个基于 PySide6 的桌面翻译小工具，支持动态背景色适配，让翻译窗口自然融入桌面环境。

## 功能特性

- **动态背景色**：自动采样窗口周围背景色，输入框背景与桌面环境融为一体
- **透明窗口**：窗口背景完全透明，无边框设计
- **始终置顶**：翻译窗口始终显示在屏幕最上层
- **自动翻译**：输入文本后按 Enter 自动翻译，支持中→英、英→中双向翻译
- **智能语言检测**：自动识别输入语言，无需手动切换
- **快捷键操作**：
  - `Enter` - 触发翻译
  - `Ctrl+Enter` - 清空输入框和翻译结果
  - `F4` - 打开设置页面
  - `双击输入框` - 清空输入框
  - `Ctrl+左键拖拽` - 移动窗口位置
- **系统托盘**：托盘图标 + 右键菜单（设置、退出）
- **设置页面**：配置翻译 API 凭证，设置持久化存储

## 快速开始

### 环境要求

- Python 3.10+
- Windows 10/11 或 Ubuntu 22.04+

### 安装运行

```bash
# 克隆项目
git clone <repository-url>
cd translate-gadget

# 安装依赖
uv sync

# 运行程序
uv run python -m translate_gadget
```

### 配置翻译 API

> **注意**：目前仅支持阿里云翻译 API。注册阿里云账号后，可获得免费翻译额度。

1. 按 `F4` 或右键托盘图标选择「设置」
2. 填写阿里云翻译 API 配置：
   - **API 地址**：`https://mt.aliyuncs.com`
   - **App ID**：阿里云 AccessKey ID
   - **密钥**：阿里云 AccessKey Secret
3. 点击「保存」，配置立即生效

**获取阿里云 API 凭证**：

1. 访问 [阿里云官网](https://www.aliyun.com/) 注册账号
2. 开通「机器翻译」服务（[定价说明](https://help.aliyun.com/zh/machine-translation/product-overview/pricing-of-machine-translation)）
3. 在 [AccessKey 管理页面](https://ram.console.aliyun.com/manage/ak) 创建 AccessKey
4. 新用户享有免费翻译额度，详见阿里云官方说明

## 使用说明

### 基本操作

1. **激活窗口**：通过全局热键或点击托盘图标显示翻译窗口
2. **输入文本**：在输入框中输入要翻译的文本
3. **执行翻译**：按 `Enter` 键触发翻译
4. **查看结果**：翻译结果显示在输入框下方
5. **清空内容**：按 `Ctrl+Enter` 或双击输入框清空

### 窗口移动

- 按住 `Ctrl` + 鼠标左键拖拽输入框，可移动窗口到任意位置
- 窗口默认位于屏幕底部居中

### 动态背景色

窗口会自动采样周围 20 像素边距区域的背景色：

- **采样频率**：每秒 1 次
- **智能过滤**：按颜色出现频率取前 70% 数据，过滤文字、图标等干扰
- **性能优化**：自动调整采样密度，确保采样点数不超过 1 万

### 翻译历史

- 内存缓存最近 1000 条翻译记录
- 程序退出后历史记录清空

## 项目结构

```
translate-gadget/
├── src/translate_gadget/
│   ├── __main__.py          # 程序入口
│   ├── window.py            # 主窗口（动态取色、翻译界面）
│   ├── translator.py        # 翻译 API 接口
│   ├── config.py            # 配置管理
│   ├── hotkey.py            # 全局热键
│   ├── tray.py              # 系统托盘
│   ├── settings_dialog.py   # 设置对话框
│   ├── history.py           # 翻译历史
│   └── utils.py             # 工具函数（语言检测）
├── assets/                  # 资源文件（图标等）
├── tests/                   # 测试代码
└── pyproject.toml           # 项目配置
```

## 技术栈

| 组件 | 技术 |
|------|------|
| GUI 框架 | PySide6 (Qt 6) |
| 全局热键 | pynput |
| 配置存储 | QSettings |
| 依赖管理 | uv |

## 开发

```bash
# 运行测试
uv run pytest

# 代码格式化
uv run black src/ tests/
```

## 许可证

MIT License
