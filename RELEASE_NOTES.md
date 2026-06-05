# Xiangqi Qt v1.0.0

这是 Xiangqi Qt 的首个公开版本。

## 主要内容

- 本地中国象棋桌面程序，基于 Python 和 PySide6 开发。
- 支持双人对弈。
- 支持 AI 对弈，玩家执红先手，AI 执黑后手。
- 内置五档 AI 难度：初窥门径、小试牛刀、渐通棋理、纵横盘间、弈臻化境。
- AI 计算使用后台线程，减少高难度思考时的界面卡顿。
- 支持走法记录，红方走法红色显示，黑方走法黑色显示。
- 走法内容使用中文数字，并保留帅/将、兵/卒等红黑棋名差异。
- 支持悔棋、重开、将军提示和胜负判定。

## 下载说明

Windows 用户下载并解压：

- `Xiangqi-Qt-v1.0.0-win64.zip`

解压后运行：

- `Xiangqi-Qt.exe`

该 exe 由 PyInstaller 打包，已包含 Python、PySide6 和项目依赖。用户不需要单独安装 Python 或 PySide6。

## 源码

源码压缩包：

- `Xiangqi-Qt-v1.0.0-source.zip`

也可以直接从仓库 tag `v1.0.0` 获取源码。
