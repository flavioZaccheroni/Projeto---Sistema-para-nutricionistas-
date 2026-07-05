from __future__ import annotations

from nutri_app.domain.release import ReleaseCheck, ReleaseCheckStatus, ReleaseReadiness


class ReleaseService:
    def evaluate(self, metrics: dict[str, object], version: str) -> ReleaseReadiness:
        checks = [
            self._check_minimum("Migrations aplicadas", metrics.get("migrations", 0), 18),
            self._check_minimum("Testes automatizados", metrics.get("tests", 0), 66),
            self._check_minimum("Documentacao de fases", metrics.get("phase_docs", 0), 24),
            self._check_minimum("Permissoes configuradas", metrics.get("permissions", 0), 1),
            self._check_flag("Usuario administrador", bool(metrics.get("has_admin"))),
            self._check_flag("Icone do aplicativo", bool(metrics.get("has_icon"))),
            self._check_flag("Backup configurado", bool(metrics.get("has_backup_config"))),
            self._check_flag("Portal Web preparado", bool(metrics.get("has_web_portal"))),
        ]
        ready = all(check.status == ReleaseCheckStatus.PASSED for check in checks)
        return ReleaseReadiness(version=version, ready=ready, checks=checks)

    def release_summary(self, readiness: ReleaseReadiness) -> str:
        status = "pronto" if readiness.ready else "com pendencias"
        return (
            f"Nutri Clinic Pro v{readiness.version} {status}. "
            f"{readiness.total_passed}/{len(readiness.checks)} checks aprovados."
        )

    def _check_minimum(self, name: str, value: object, minimum: int) -> ReleaseCheck:
        number = int(value or 0)
        if number >= minimum:
            return ReleaseCheck(name, ReleaseCheckStatus.PASSED, f"{number} encontrado(s).")
        return ReleaseCheck(
            name,
            ReleaseCheckStatus.FAILED,
            f"Esperado minimo {minimum}, encontrado {number}.",
        )

    def _check_flag(self, name: str, passed: bool) -> ReleaseCheck:
        if passed:
            return ReleaseCheck(name, ReleaseCheckStatus.PASSED, "Validado.")
        return ReleaseCheck(name, ReleaseCheckStatus.FAILED, "Pendente.")
