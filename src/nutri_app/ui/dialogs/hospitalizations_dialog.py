from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from nutri_app.domain.hospitalization import Hospitalization
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.hospitalization_repository import HospitalizationRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.ui.date_format import format_date, parse_date, parse_optional_date, today_text
from nutri_app.ui.input_masks import apply_date_mask


class HospitalizationsDialog(QDialog):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
        patient_id: int,
        patient_name: str,
        default_health_insurance: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.repository = HospitalizationRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.default_health_insurance = default_health_insurance
        self.selected_hospitalization_id: int | None = None

        self.setWindowTitle(f"Internacoes - {patient_name}")
        self.resize(1050, 720)

        self.admission_date = QLineEdit(today_text())
        self.discharge_date = QLineEdit()
        apply_date_mask(self.admission_date)
        apply_date_mask(self.discharge_date)
        self.unit = QLineEdit()
        self.ward = QLineEdit()
        self.bed = QLineEdit()
        self.health_insurance = QLineEdit(default_health_insurance)
        self.responsible_team = QLineEdit()
        self.status = QComboBox()
        self.status.addItems(["Ativa", "Alta", "Transferida", "Cancelada"])
        self.discharge_condition = QLineEdit()
        self.diagnoses = QTextEdit()
        self.diagnoses.setFixedHeight(60)
        self.notes = QTextEdit()
        self.notes.setFixedHeight(60)

        form = QGridLayout()
        self._field(form, 0, 0, "Admissao", self.admission_date)
        self._field(form, 0, 1, "Alta", self.discharge_date)
        self._field(form, 0, 2, "Status", self.status)
        self._field(form, 2, 0, "Unidade", self.unit)
        self._field(form, 2, 1, "Ala/setor", self.ward)
        self._field(form, 2, 2, "Leito", self.bed)
        self._field(form, 4, 0, "Convenio", self.health_insurance)
        self._field(form, 4, 1, "Equipe responsavel", self.responsible_team, column_span=2)
        self._field(form, 6, 0, "Condicao de alta", self.discharge_condition, column_span=3)
        self._field(form, 8, 0, "Diagnosticos", self.diagnoses, column_span=3)
        self._field(form, 10, 0, "Observacoes", self.notes, column_span=3)
        for column in range(3):
            form.setColumnStretch(column, 1)

        save = QPushButton("Salvar internacao")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save)
        new = QPushButton("Nova")
        new.clicked.connect(self._clear)
        delete = QPushButton("Excluir")
        delete.clicked.connect(self._delete)
        close = QPushButton("Fechar")
        close.clicked.connect(self.accept)
        actions = QHBoxLayout()
        actions.addWidget(save)
        actions.addWidget(new)
        actions.addWidget(delete)
        actions.addStretch()
        actions.addWidget(close)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Admissao", "Alta", "Status", "Unidade", "Ala", "Leito", "Equipe"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellClicked.connect(self._select)

        layout = QVBoxLayout(self)
        title = QLabel(f"Episodios de internacao de {patient_name}")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        layout.addLayout(form)
        layout.addLayout(actions)
        layout.addWidget(self.table)
        self._reload()

    def _field(
        self,
        layout: QGridLayout,
        row: int,
        column: int,
        label: str,
        widget,
        column_span: int = 1,
    ) -> None:
        caption = QLabel(label)
        caption.setObjectName("miniHeader")
        layout.addWidget(caption, row, column, 1, column_span)
        layout.addWidget(widget, row + 1, column, 1, column_span)

    def _save(self) -> None:
        try:
            hospitalization = Hospitalization(
                id=self.selected_hospitalization_id,
                patient_id=self.patient_id,
                admission_date=parse_date(self.admission_date.text()),
                discharge_date=parse_optional_date(self.discharge_date.text()),
                unit=self.unit.text(),
                ward=self.ward.text(),
                bed=self.bed.text(),
                health_insurance=self.health_insurance.text(),
                responsible_team=self.responsible_team.text(),
                diagnoses=self.diagnoses.toPlainText(),
                discharge_condition=self.discharge_condition.text(),
                status=self.status.currentText(),
                notes=self.notes.toPlainText(),
            )
            if hospitalization.id is None:
                hospitalization_id = self.repository.add(hospitalization)
                action = "criou_internacao"
            else:
                hospitalization_id = hospitalization.id
                self.repository.update(hospitalization)
                action = "atualizou_internacao"
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc))
            return

        self.audit_repository.log(
            self.current_user_id,
            action,
            "internacoes",
            hospitalization_id,
            f"Paciente {self.patient_id}; status {hospitalization.status}.",
        )
        self._clear()
        self._reload()

    def _reload(self) -> None:
        hospitalizations = self.repository.list_for_patient(self.patient_id)
        self.table.setRowCount(len(hospitalizations))
        for row, hospitalization in enumerate(hospitalizations):
            values = [
                str(hospitalization.id or ""),
                format_date(hospitalization.admission_date),
                format_date(hospitalization.discharge_date),
                hospitalization.status,
                hospitalization.unit,
                hospitalization.ward or "-",
                hospitalization.bed or "-",
                hospitalization.responsible_team or "-",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, column, item)

    def _select(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        hospitalization = self.repository.get(int(item.text())) if item else None
        if hospitalization is None:
            return
        self.selected_hospitalization_id = hospitalization.id
        self.admission_date.setText(format_date(hospitalization.admission_date))
        self.discharge_date.setText(format_date(hospitalization.discharge_date))
        self.unit.setText(hospitalization.unit)
        self.ward.setText(hospitalization.ward)
        self.bed.setText(hospitalization.bed)
        self.health_insurance.setText(hospitalization.health_insurance)
        self.responsible_team.setText(hospitalization.responsible_team)
        self.diagnoses.setPlainText(hospitalization.diagnoses)
        self.discharge_condition.setText(hospitalization.discharge_condition)
        self.status.setCurrentText(hospitalization.status)
        self.notes.setPlainText(hospitalization.notes)

    def _clear(self) -> None:
        self.selected_hospitalization_id = None
        self.admission_date.setText(today_text())
        self.discharge_date.clear()
        self.unit.clear()
        self.ward.clear()
        self.bed.clear()
        self.health_insurance.setText(self.default_health_insurance)
        self.responsible_team.clear()
        self.diagnoses.clear()
        self.discharge_condition.clear()
        self.status.setCurrentText("Ativa")
        self.notes.clear()

    def _delete(self) -> None:
        if self.selected_hospitalization_id is None:
            QMessageBox.warning(self, "Internacao", "Selecione uma internacao.")
            return
        if (
            QMessageBox.question(self, "Excluir internacao", "Confirma a exclusao logica?")
            != QMessageBox.StandardButton.Yes
        ):
            return
        hospitalization_id = self.selected_hospitalization_id
        self.repository.soft_delete(hospitalization_id, self.patient_id)
        self.audit_repository.log(
            self.current_user_id,
            "excluiu_internacao",
            "internacoes",
            hospitalization_id,
            f"Paciente {self.patient_id}.",
        )
        self._clear()
        self._reload()
