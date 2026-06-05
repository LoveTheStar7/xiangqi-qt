import sys

from PySide6.QtWidgets import QApplication

from xiangqi.ui import XiangqiWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = XiangqiWindow()
    if window.startup_cancelled:
        return 0
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
