from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from nutri_app.domain.user import AuthenticatedUser, User, UserRole
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.user_repository import UserRepository
from nutri_app.services.security import PasswordHasher


@dataclass(frozen=True)
class LoginResult:
    user: AuthenticatedUser | None
    message: str
    password_change_required: bool = False


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        audit_repository: AuditRepository,
        password_hasher: PasswordHasher | None = None,
    ) -> None:
        self.user_repository = user_repository
        self.audit_repository = audit_repository
        self.password_hasher = password_hasher or PasswordHasher()

    def ensure_default_admin(self) -> None:
        if self.user_repository.count_users() > 0:
            return

        admin = User(
            name="Administrador",
            email="admin@local.com",
            password_hash=self.password_hasher.hash_password("Nutri1!"),
            role=UserRole.ADMINISTRADOR,
            must_change_password=False,
        )
        user_id = self.user_repository.add(admin)
        self.audit_repository.log(
            user_id=user_id,
            action="criou_usuario_padrao",
            entity="usuarios",
            entity_id=user_id,
            details="Usuario administrador inicial criado automaticamente.",
        )

    def login(self, email: str, password: str) -> LoginResult:
        normalized_email = email.strip().lower()
        user = self.user_repository.get_active_by_email(normalized_email)
        if user is None or user.id is None:
            self.audit_repository.log(
                user_id=None,
                action="falha_login",
                entity="usuarios",
                entity_id=None,
                details=f"E-mail nao encontrado ou inativo: {normalized_email}",
            )
            return LoginResult(user=None, message="E-mail ou senha invalidos.")

        if user.locked_until and user.locked_until > datetime.now():
            self.audit_repository.log(
                user_id=user.id,
                action="login_bloqueado",
                entity="usuarios",
                entity_id=user.id,
                details=f"Acesso bloqueado ate {user.locked_until.isoformat()}.",
            )
            return LoginResult(
                user=None,
                message="Acesso temporariamente bloqueado por tentativas invalidas.",
            )

        if not self.password_hasher.verify_password(password, user.password_hash):
            self.user_repository.register_failed_login(user.id, max_attempts=5, lock_minutes=15)
            self.audit_repository.log(
                user_id=user.id,
                action="falha_login",
                entity="usuarios",
                entity_id=user.id,
                details="Senha invalida.",
            )
            return LoginResult(user=None, message="E-mail ou senha invalidos.")

        self.user_repository.clear_login_failures(user.id)

        authenticated = AuthenticatedUser(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            must_change_password=user.must_change_password,
        )
        self.audit_repository.log(
            user_id=user.id,
            action="login",
            entity="usuarios",
            entity_id=user.id,
            details="Login realizado com sucesso.",
        )
        return LoginResult(
            user=authenticated,
            message="Login realizado com sucesso.",
            password_change_required=user.must_change_password,
        )

    def change_password(self, user_id: int, new_password: str) -> None:
        password_hash = self.password_hasher.hash_password(new_password)
        self.user_repository.change_password(user_id, password_hash)
        self.audit_repository.log(
            user_id=user_id,
            action="alterou_senha",
            entity="usuarios",
            entity_id=user_id,
            details="Senha alterada pelo proprio usuario.",
        )
