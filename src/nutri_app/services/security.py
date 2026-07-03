from __future__ import annotations

import hashlib
import hmac
import secrets


class PasswordHasher:
    algorithm = "pbkdf2_sha256"
    iterations = 210_000
    salt_bytes = 16

    def hash_password(self, password: str) -> str:
        self._validate_password(password)
        salt = secrets.token_hex(self.salt_bytes)
        digest = self._digest(password, salt, self.iterations)
        return f"{self.algorithm}${self.iterations}${salt}${digest}"

    def verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            algorithm, iterations_text, salt, expected = stored_hash.split("$", 3)
            iterations = int(iterations_text)
        except ValueError:
            return False

        if algorithm != self.algorithm:
            return False

        actual = self._digest(password, salt, iterations)
        return hmac.compare_digest(actual, expected)

    def _digest(self, password: str, salt: str, iterations: int) -> str:
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        ).hex()

    def _validate_password(self, password: str) -> None:
        if len(password) < 8:
            raise ValueError("A senha deve possuir pelo menos 8 caracteres.")
