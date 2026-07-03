from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from nutri_app.domain.user import User, UserRole
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.user_repository import UserRepository
from nutri_app.services.security import PasswordHasher
from nutri_app.ui.pages.base import Page


class UsersPage(Page):
    def __init__(
        self,
        user_repository: UserRepository,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__("Usuarios e Permissoes", "Login, perfis, permissoes e seguranca.")
        self.user_repository = user_repository
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.password_hasher = PasswordHasher()

        self.name = QLineEdit()
        self.email = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.role = QComboBox()
        self.role.addItems([role.value for role in UserRole])

        form = QFormLayout()
        form.addRow("Nome", self.name)
        form.addRow("E-mail", self.email)
        form.addRow("Senha inicial", self.password)
        form.addRow("Perfil", self.role)

        save = QPushButton("Criar usuario")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._create_user)
        clear = QPushButton("Novo")
        clear.clicked.connect(self._clear_form)

        actions = QHBoxLayout()
        actions.addWidget(save)
        actions.addWidget(clear)
        actions.addStretch()

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "E-mail", "Perfil", "Ativo"])

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.table)
        self._reload_table()

    def _create_user(self) -> None:
        name = self.name.text().strip()
        email = self.email.text().strip().lower()
        password = self.password.text()

        if not name or not email:
            QMessageBox.warning(self, "Validacao", "Nome e e-mail sao obrigatorios.")
            return

        try:
            password_hash = self.password_hasher.hash_password(password)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc))
            return

        try:
            user_id = self.user_repository.add(
                User(
                    name=name,
                    email=email,
                    password_hash=password_hash,
                    role=UserRole(self.role.currentText()),
                )
            )
        except Exception as exc:
            QMessageBox.warning(self, "Usuario", f"Nao foi possivel criar usuario: {exc}")
            return

        self.audit_repository.log(
            user_id=self.current_user_id,
            action="criou_usuario",
            entity="usuarios",
            entity_id=user_id,
            details=f"Usuario criado: {email}",
        )
        self._clear_form()
        self._reload_table()

    def _clear_form(self) -> None:
        self.name.clear()
        self.email.clear()
        self.password.clear()
        self.role.setCurrentIndex(0)

    def _reload_table(self) -> None:
        users = self.user_repository.list_active()
        self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(str(user.id or "")))
            self.table.setItem(row, 1, QTableWidgetItem(user.name))
            self.table.setItem(row, 2, QTableWidgetItem(user.email))
            self.table.setItem(row, 3, QTableWidgetItem(user.role.value))
            self.table.setItem(row, 4, QTableWidgetItem("Sim" if user.active else "Nao"))
