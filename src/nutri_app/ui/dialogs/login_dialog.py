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
from nutri_app.ui.input_masks import apply_email_validator


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
        apply_email_validator(self.email)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setPlaceholderText("Nutri1!")

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

        help_label = QLabel("Acesso local: admin@local.com / Nutri1!")
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

        if result.password_change_required:
            dialog = PasswordChangeDialog(self.auth_service, result.user.id, self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                QMessageBox.information(
                    self,
                    "Primeiro acesso",
                    "A troca da senha inicial e obrigatoria para continuar.",
                )
                return
            result = self.auth_service.login(self.email.text(), dialog.new_password)
            if result.user is None:
                QMessageBox.warning(self, "Login", result.message)
                return
        self.user = result.user
        self.accept()


class PasswordChangeDialog(QDialog):
    def __init__(self, auth_service: AuthService, user_id: int, parent=None) -> None:
        super().__init__(parent)
        self.auth_service = auth_service
        self.user_id = user_id
        self.new_password = ""
        self.setWindowTitle("Troca obrigatoria de senha")
        self.setMinimumWidth(420)

        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirmation = QLineEdit()
        self.confirmation.setEchoMode(QLineEdit.EchoMode.Password)
        form = QFormLayout()
        form.addRow("Nova senha", self.password)
        form.addRow("Confirmar senha", self.confirmation)
        guidance = QLabel(
            "Use pelo menos 7 caracteres, com maiuscula, minuscula, numero e simbolo."
        )
        guidance.setWordWrap(True)
        save = QPushButton("Alterar senha")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save)
        layout = QVBoxLayout(self)
        layout.addWidget(guidance)
        layout.addLayout(form)
        layout.addWidget(save)

    def _save(self) -> None:
        password = self.password.text()
        if password != self.confirmation.text():
            QMessageBox.warning(self, "Senha", "As senhas informadas nao conferem.")
            return
        try:
            self.auth_service.change_password(self.user_id, password)
        except ValueError as exc:
            QMessageBox.warning(self, "Senha", str(exc))
            return
        self.new_password = password
        self.accept()
