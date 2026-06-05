# Xiangqi Qt

Xiangqi Qt is a local Chinese chess desktop game built with Python and PySide6.

## Features

- Traditional 9-by-10 Xiangqi board
- Click-to-select and click-to-move interaction
- Legal destination hints
- Core Xiangqi movement rules
- Check warning and captured-general win detection
- Undo, restart, and colored move history
- Two-player mode
- AI mode with red human player moving first
- Five AI difficulty levels: 初窥门径, 小试牛刀, 渐通棋理, 纵横盘间, 弈臻化境
- Background-thread AI calculation to keep the UI responsive

## Requirements

- Python 3.9+
- PySide6

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run From Source

```powershell
python main.py
```

## Run Tests

```powershell
python -m pytest
```

## Build Windows EXE

```powershell
python -m PyInstaller --noconfirm --clean --windowed --onefile --name Xiangqi-Qt main.py
```

The generated executable is written to `dist/Xiangqi-Qt.exe`.
