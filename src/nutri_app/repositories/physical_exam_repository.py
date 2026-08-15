from __future__ import annotations

import json
from datetime import date, datetime

from nutri_app.domain.physical_exam import NutritionPhysicalExam
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory


class PhysicalExamRepository:
    SEMANTIC_STATES = {
        "Nao avaliado",
        "Ausente",
        "Leve",
        "Moderado",
        "Grave",
        "Nao aplicavel",
        "Preservado",
        "Alterado",
    }
    SEVERITIES = {"Sem alerta", "Leve", "Moderada", "Grave", "Critica"}

    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def add(self, exam: NutritionPhysicalExam) -> int:
        self._validate(exam)
        with self.connection_factory.connect() as connection:
            patient = connection.execute(
                "SELECT 1 FROM pacientes WHERE id = ? AND deleted_at IS NULL",
                (exam.patient_id,),
            ).fetchone()
            if patient is None:
                raise ValueError("Paciente nao encontrado.")
            if exam.diagnosis_id is not None:
                diagnosis = connection.execute(
                    """
                    SELECT 1 FROM diagnosticos_nutricionais
                    WHERE id = ? AND paciente_id = ? AND deleted_at IS NULL
                    """,
                    (exam.diagnosis_id, exam.patient_id),
                ).fetchone()
                if diagnosis is None:
                    raise ValueError("Diagnostico nao pertence ao paciente selecionado.")
            cursor = connection.execute(
                """
                INSERT INTO exames_fisicos_nutricionais (
                    paciente_id, diagnostico_id, data_avaliacao, achados_json,
                    sinais_sintomas, resumo, gravidade, caminho_imagem,
                    consentimento_imagem
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    exam.patient_id,
                    exam.diagnosis_id,
                    exam.assessment_date.isoformat(),
                    json.dumps(exam.findings, ensure_ascii=False, sort_keys=True),
                    exam.signs_symptoms.strip(),
                    exam.summary.strip(),
                    exam.severity,
                    exam.image_path.strip(),
                    1 if exam.image_consent else 0,
                ),
            )
            return int(cursor.lastrowid)

    def get(self, exam_id: int) -> NutritionPhysicalExam | None:
        with self.connection_factory.connect() as connection:
            row = connection.execute(
                """
                SELECT e.*, p.nome AS paciente_nome
                FROM exames_fisicos_nutricionais e
                JOIN pacientes p ON p.id = e.paciente_id
                WHERE e.id = ? AND e.deleted_at IS NULL
                """,
                (exam_id,),
            ).fetchone()
        return self._row_to_exam(row) if row else None

    def list_for_patient(self, patient_id: int) -> list[NutritionPhysicalExam]:
        with self.connection_factory.connect() as connection:
            rows = connection.execute(
                """
                SELECT e.*, p.nome AS paciente_nome
                FROM exames_fisicos_nutricionais e
                JOIN pacientes p ON p.id = e.paciente_id
                WHERE e.paciente_id = ? AND e.deleted_at IS NULL
                ORDER BY e.data_avaliacao DESC, e.id DESC
                """,
                (patient_id,),
            ).fetchall()
        return [self._row_to_exam(row) for row in rows]

    def compare_to_previous(self, exam_id: int) -> list[str]:
        current = self.get(exam_id)
        if current is None:
            raise ValueError("Avaliacao clinica nao encontrada.")
        history = self.list_for_patient(current.patient_id)
        older = next(
            (
                exam
                for exam in history
                if exam.id != current.id
                and (exam.assessment_date, exam.id or 0)
                < (current.assessment_date, current.id or 0)
            ),
            None,
        )
        if older is None:
            return ["Primeira avaliacao registrada; sem comparativo anterior."]
        changes = []
        keys = sorted(set(current.findings) | set(older.findings))
        for key in keys:
            before = older.findings.get(key, "Nao avaliado")
            after = current.findings.get(key, "Nao avaliado")
            if before != after:
                changes.append(f"{key}: {before} -> {after}")
        if current.severity != older.severity:
            changes.append(f"gravidade: {older.severity} -> {current.severity}")
        return changes or ["Sem alteracoes nos achados estruturados."]

    def _validate(self, exam: NutritionPhysicalExam) -> None:
        if not exam.findings:
            raise ValueError("Informe os achados do exame fisico nutricional.")
        invalid = sorted(set(exam.findings.values()) - self.SEMANTIC_STATES)
        if invalid:
            raise ValueError(f"Estados de achados invalidos: {', '.join(invalid)}.")
        if not exam.summary.strip():
            raise ValueError("Resumo dos achados e obrigatorio.")
        if exam.severity not in self.SEVERITIES:
            raise ValueError("Gravidade invalida.")
        if exam.image_path.strip() and not exam.image_consent:
            raise ValueError("A imagem clinica exige consentimento registrado.")

    def _row_to_exam(self, row) -> NutritionPhysicalExam:
        return NutritionPhysicalExam(
            id=row["id"],
            patient_id=row["paciente_id"],
            patient_name=row["paciente_nome"],
            diagnosis_id=row["diagnostico_id"],
            assessment_date=date.fromisoformat(row["data_avaliacao"]),
            findings=json.loads(row["achados_json"]),
            signs_symptoms=row["sinais_sintomas"] or "",
            summary=row["resumo"],
            severity=row["gravidade"],
            image_path=row["caminho_imagem"] or "",
            image_consent=bool(row["consentimento_imagem"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
