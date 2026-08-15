from __future__ import annotations

import json
import secrets
import threading
from datetime import date, datetime
from http import HTTPStatus
from pathlib import Path
from wsgiref.simple_server import WSGIServer, make_server

from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class PatientPortalApplication:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory
        self.sessions: dict[str, tuple[int, datetime]] = {}

    def authenticate(self, email: str, access_code: str) -> str:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                """
                SELECT id, paciente_id FROM paciente_app_acessos
                WHERE lower(email_login) = lower(?) AND codigo_acesso = ?
                  AND ativo = 1 AND deleted_at IS NULL
                """,
                (email.strip(), access_code.strip()),
            ).fetchone()
            if row is None:
                raise ValueError("Credenciais invalidas.")
            connection.execute(
                """
                UPDATE paciente_app_acessos
                SET ultimo_acesso = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (row["id"],),
            )
        token = secrets.token_urlsafe(32)
        self.sessions[token] = (int(row["paciente_id"]), datetime.now())
        return token

    def list_publications(self, token: str) -> list[dict[str, object]]:
        patient_id = self._patient_id(token)
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, tipo, titulo, conteudo, data_publicacao, data_expiracao
                FROM paciente_app_publicacoes
                WHERE paciente_id = ? AND status = 'Publicado' AND deleted_at IS NULL
                  AND (data_expiracao IS NULL OR data_expiracao >= ?)
                ORDER BY data_publicacao DESC, id DESC
                """,
                (patient_id, date.today().isoformat()),
            ).fetchall()
        return [dict(row) for row in rows]

    def record_adherence(
        self,
        token: str,
        publication_id: int | None,
        percentage: float,
        mood: str = "",
        difficulties: str = "",
    ) -> int:
        patient_id = self._patient_id(token)
        if not 0 <= percentage <= 100:
            raise ValueError("Adesao deve estar entre 0 e 100%.")
        with self.connection_factory.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO paciente_app_adesoes (
                    paciente_id, publicacao_id, data_registro, percentual_adesao,
                    humor, dificuldades, observacoes
                ) VALUES (?, ?, ?, ?, ?, ?, 'Registrado pelo portal do paciente')
                """,
                (
                    patient_id,
                    publication_id,
                    date.today().isoformat(),
                    percentage,
                    mood.strip(),
                    difficulties.strip(),
                ),
            )
            return int(cursor.lastrowid)

    def __call__(self, environ, start_response):
        try:
            status, headers, body = self._dispatch(environ)
        except ValueError as exc:
            status = HTTPStatus.BAD_REQUEST
            headers = [("Content-Type", "application/json; charset=utf-8")]
            body = json.dumps({"error": str(exc)}, ensure_ascii=False).encode("utf-8")
        start_response(f"{status.value} {status.phrase}", headers)
        return [body]

    def _dispatch(self, environ):
        path = environ.get("PATH_INFO", "/")
        method = environ.get("REQUEST_METHOD", "GET")
        if path == "/" and method == "GET":
            return self._response(HTTPStatus.OK, "text/html; charset=utf-8", self._html())
        payload = self._json_body(environ) if method == "POST" else {}
        if path == "/api/login" and method == "POST":
            token = self.authenticate(str(payload.get("email", "")), str(payload.get("code", "")))
            return self._json_response({"token": token})
        token = self._bearer_token(environ)
        if path == "/api/publications" and method == "GET":
            return self._json_response({"publications": self.list_publications(token)})
        if path == "/api/adherence" and method == "POST":
            record_id = self.record_adherence(
                token,
                int(payload["publication_id"]) if payload.get("publication_id") else None,
                float(payload.get("percentage", -1)),
                str(payload.get("mood", "")),
                str(payload.get("difficulties", "")),
            )
            return self._json_response({"id": record_id}, HTTPStatus.CREATED)
        return self._json_response({"error": "Rota nao encontrada"}, HTTPStatus.NOT_FOUND)

    def _patient_id(self, token: str) -> int:
        session = self.sessions.get(token)
        if session is None:
            raise ValueError("Sessao invalida ou expirada.")
        return session[0]

    def _bearer_token(self, environ) -> str:
        authorization = environ.get("HTTP_AUTHORIZATION", "")
        if not authorization.startswith("Bearer "):
            raise ValueError("Token de acesso obrigatorio.")
        return authorization.removeprefix("Bearer ").strip()

    def _json_body(self, environ) -> dict:
        length = int(environ.get("CONTENT_LENGTH") or 0)
        raw = environ["wsgi.input"].read(length)
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError("JSON invalido.") from exc

    def _json_response(self, payload: object, status: HTTPStatus = HTTPStatus.OK):
        return self._response(
            status,
            "application/json; charset=utf-8",
            json.dumps(payload, ensure_ascii=False, default=str),
        )

    def _response(self, status: HTTPStatus, content_type: str, content: str):
        body = content.encode("utf-8")
        return status, [("Content-Type", content_type), ("Content-Length", str(len(body)))], body

    def _html(self) -> str:
        path = Path(__file__).resolve().parents[1] / "ui" / "resources" / "patient_portal.html"
        return path.read_text(encoding="utf-8")


class PatientPortalServer:
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        host: str = "127.0.0.1",
        port: int = 8765,
    ) -> None:
        self.application = PatientPortalApplication(connection_factory)
        self.host = host
        self.port = port
        self.server: WSGIServer | None = None
        self.thread: threading.Thread | None = None
        self.url = f"http://{host}:{port}"

    def start(self) -> str:
        if self.thread and self.thread.is_alive():
            return self.url
        self.server = make_server(self.host, self.port, self.application)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self.url

    def stop(self) -> None:
        if self.thread and self.thread.is_alive():
            if self.server is not None:
                self.server.shutdown()
            self.thread.join(timeout=3)
        if self.server is not None:
            self.server.server_close()
            self.server = None
