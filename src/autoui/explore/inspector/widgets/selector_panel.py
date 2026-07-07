"""
SelectorPanel — Generated/Custom режим, Test, Copy.
"""

from __future__ import annotations

from enum import Enum, auto

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class SelectorMode(Enum):
    GENERATED = auto()
    CUSTOM = auto()


class SelectorPanel(QWidget):
    test_requested = Signal()
    copy_requested = Signal()
    mode_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._mode = SelectorMode.GENERATED
        self._generated_text = ""
        self._custom_dirty = False

        mode_row = QHBoxLayout()
        self._radio_generated = QRadioButton("Generated")
        self._radio_custom = QRadioButton("Custom")
        self._radio_generated.setChecked(True)
        self._radio_generated.toggled.connect(self._on_mode_toggled)
        self._btn_test = QPushButton("Test")
        self._btn_copy = QPushButton("Copy")
        self._btn_test.clicked.connect(self.test_requested.emit)
        self._btn_copy.clicked.connect(self.copy_requested.emit)
        mode_row.addWidget(self._radio_generated)
        mode_row.addWidget(self._radio_custom)
        mode_row.addStretch()
        mode_row.addWidget(self._btn_test)
        mode_row.addWidget(self._btn_copy)

        self._editor = QTextEdit(self)
        font = QFont("Consolas")
        if not font.exactMatch():
            font = QFont("Courier New")
        self._editor.setFont(font)
        self._editor.textChanged.connect(self._on_text_changed)

        layout = QVBoxLayout(self)
        layout.addLayout(mode_row)
        layout.addWidget(QLabel("Locator (Python):"))
        layout.addWidget(self._editor)

    def mode(self) -> SelectorMode:
        return self._mode

    def set_generated_text(self, text: str) -> None:
        self._generated_text = text
        if self._mode == SelectorMode.GENERATED:
            self._editor.blockSignals(True)
            self._editor.setPlainText(text)
            self._editor.blockSignals(False)

    def editor_text(self) -> str:
        return self._editor.toPlainText()

    def _on_mode_toggled(self, generated_checked: bool) -> None:
        if generated_checked:
            if self._mode == SelectorMode.CUSTOM and self._custom_dirty:
                from PySide6.QtWidgets import QMessageBox

                answer = QMessageBox.question(
                    self,
                    "Переключить режим",
                    "Потерять правки Custom и вернуться к Generated?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if answer != QMessageBox.StandardButton.Yes:
                    self._radio_custom.setChecked(True)
                    return
            self._mode = SelectorMode.GENERATED
            self._editor.setReadOnly(False)
            self._editor.setPlainText(self._generated_text)
            self._custom_dirty = False
        else:
            self._mode = SelectorMode.CUSTOM
            if not self._custom_dirty:
                self._editor.setPlainText(self._generated_text)
            self._editor.setReadOnly(False)
        self.mode_changed.emit()

    def _on_text_changed(self) -> None:
        if self._mode == SelectorMode.CUSTOM:
            self._custom_dirty = True
