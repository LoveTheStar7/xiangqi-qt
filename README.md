# Xiangqi Qt

Xiangqi Qt 是一个使用 Python 与 PySide6 开发的本地中国象棋桌面程序。项目提供双人对弈与 AI 对弈两种模式，支持走法记录、悔棋、重开、将军提示和多档 AI 难度。

> 项目名中的 Xiangqi 是“中国象棋”的英文常用写法，Qt 表示图形界面基于 Qt/PySide6。

## 功能特性

- 传统 9 x 10 中国象棋棋盘
- 红黑双方棋子显示，保留“帅/将”“兵/卒”“仕/士”“相/象”等差异
- 鼠标点击选子，再点击目标位置行棋
- 合法落点提示
- 基本象棋行棋规则：
  - 车、马、相/象、仕/士、帅/将、炮、兵/卒
  - 马腿、象眼、九宫限制、兵卒过河、炮隔子吃子
  - 帅将照面
- 将军状态提示
- 吃掉帅/将后判定胜负
- 悔棋与重开
- 走法记录：
  - 走法内容使用中文数字
  - 红方走法红色显示
  - 黑方走法黑色显示
  - 序号保留 `1.`、`2.` 这类格式
- 启动时选择对弈模式
- 支持双人对弈
- 支持 AI 对弈，玩家执红先手，AI 执黑后手
- AI 计算放在后台线程中，避免高难度思考时卡住界面

## AI 难度

程序内置五档 AI 难度，整体从随机、吃子倾向、位置判断逐步提升到搜索型策略。

| 难度 | 行为特点 |
| --- | --- |
| 初窥门径 | 随机选择合法走法，适合熟悉规则 |
| 小试牛刀 | 优先吃高价值棋子 |
| 渐通棋理 | 在吃子基础上考虑棋子位置，例如兵卒过河、车马炮靠中 |
| 纵横盘间 | 使用较浅搜索，考虑对手下一步回应 |
| 弈臻化境 | 使用更深一层的 alpha-beta 搜索，结合局面价值评估 |

当前 AI 不是专业象棋引擎，主要目标是在本地桌面小游戏中提供循序渐进的对弈体验。

## 下载与运行

Windows 用户可以在 GitHub Release 页面下载打包好的版本：

[下载 Xiangqi Qt v1.0.0](https://github.com/LoveTheStar7/xiangqi-qt/releases/tag/v1.0.0)

下载 `Xiangqi-Qt-v1.0.0-win64.zip` 后解压，运行其中的 `Xiangqi-Qt.exe`。

打包版本已包含 Python、PySide6 和项目依赖，用户不需要额外安装 Python 或 PySide6。

## 从源码运行

### 环境要求

- Windows 10/11
- Python 3.9 或更新版本
- PySide6

开发和发布时使用的环境：

- Python 3.9.10
- PySide6 6.9.1
- pytest 8.4.2
- PyInstaller 6.14.2

### 安装依赖

```powershell
python -m pip install -r requirements.txt
```

### 启动程序

```powershell
python main.py
```

## 测试

项目使用 pytest 覆盖核心棋规、AI 选择和主要 UI 流程。

```powershell
python -m pytest
```

当前测试覆盖内容包括：

- 初始棋盘布局
- 各类棋子的基本走法
- 悔棋、重开、胜负判定
- AI 合法走法和难度行为
- AI 后台线程计算
- 走法记录显示
- 启动对话框关闭行为

## 打包 Windows EXE

本项目使用 PyInstaller 打包 Windows 单文件可执行程序。

```powershell
python -m PyInstaller --noconfirm --clean --windowed --onefile --name Xiangqi-Qt main.py
```

打包完成后，文件会生成在：

```text
dist/Xiangqi-Qt.exe
```

说明：

- `--windowed` 用于隐藏控制台窗口
- `--onefile` 用于生成单文件 exe
- PyInstaller 会把 Python 解释器、PySide6 和相关依赖打包进 exe
- exe 仍依赖 Windows 系统本身提供的基础运行环境

## 项目结构

```text
xiangqi-qt/
├── main.py                 # 程序入口
├── xiangqi/
│   ├── engine.py           # 棋盘状态、行棋规则、胜负状态、走法格式
│   ├── ai.py               # AI 难度、评分、搜索逻辑
│   └── ui.py               # PySide6 图形界面和交互流程
├── tests/
│   ├── test_engine.py      # 棋规与引擎测试
│   ├── test_ai.py          # AI 测试
│   └── test_ui_flow.py     # UI 流程测试
├── requirements.txt        # 运行、测试和打包依赖
├── RELEASE_NOTES.md        # 发布说明
├── LICENSE                 # MIT 开源许可证
└── README.md
```

## 许可证

本项目基于 MIT License 开源，详见 [LICENSE](LICENSE)。
