from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from nutri_app.domain.user import AuthenticatedUser
from nutri_app.services.auth import AuthService


class LoginDialog(QDialog):
    def __init__(self, auth_service: AuthService) -> None:
        super().__init__()
        self.auth_service = auth_service
        self.user: AuthenticatedUser | None = None

        self.setWindowTitle("Login")
        self.setModal(True)
        self.setMinimumWidth(420)

        title = QLabel("Acesso ao Sistema")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Entre com seu e-mail e senha para continuar.")
        subtitle.setObjectName("pageSubtitle")

        self.email = QLineEdit()
        self.email.setPlaceholderText("admin@nutricionistas.local")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("Admin@123")

        form = QFormLayout()
        form.addRow("E-mail", self.email)
        form.addRow("Senha", self.password)

        login = QPushButton("Entrar")
        login.setObjectName("primaryButton")
        login.clicked.connect(self._login)
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(cancel)
        actions.addWidget(login)

        help_label = QLabel("Primeiro acesso: admin@nutricionistas.local / Admin@123")
        help_label.setObjectName("pageSubtitle")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(form)
        layout.addWidget(help_label)
        layout.addLayout(actions)

    def _login(self) -> None:
        result = self.auth_service.login(self.email.text(), self.password.text())
        if result.user is None:
            QMessageBox.warning(self, "Login", result.message)
            return

        self.user = result.user
        self.accept()
