import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from nutri_app.database.schema import initialize_database
from nutri_app.domain.user import User, UserRole
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.repositories.user_repository import UserRepository


class UserRepositoryProfessionalRegistrationTest(unittest.TestCase):
    def _repository(self) -> tuple[UserRepository, TemporaryDirectory]:
        tmp = TemporaryDirectory()
        factory = SQLiteConnectionFactory(Path(tmp.name) / "test.sqlite")
        initialize_database(factory)
        return UserRepository(factory), tmp

    def test_persiste_e_recupera_registro_profissional(self) -> None:
        repository, tmp = self._repository()
        with tmp:
            user_id = repository.add(
                User(
                    name="Nutricionista Teste",
                    email="nutri@teste.com",
                    password_hash="hash",
                    role=UserRole.NUTRICIONISTA,
                    professional_registration="CRN-3 12345",
                )
            )

            loaded = repository.get(user_id)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.professional_registration, "CRN-3 12345")

    def test_registro_profissional_opcional(self) -> None:
        repository, tmp = self._repository()
        with tmp:
            user_id = repository.add(
                User(
                    name="Sem CRN",
                    email="semcrn@teste.com",
                    password_hash="hash",
                    role=UserRole.RECEPCIONISTA,
                )
            )

            loaded = repository.get(user_id)

        self.assertIsNotNone(loaded)
        self.assertIsNone(loaded.professional_registration)

    def test_get_retorna_none_para_usuario_inexistente(self) -> None:
        repository, tmp = self._repository()
        with tmp:
            self.assertIsNone(repository.get(999))


if __name__ == "__main__":
    unittest.main()
