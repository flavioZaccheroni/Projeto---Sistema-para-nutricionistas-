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
    QTextEdit,
    QWidget,
)

from nutri_app.domain.laboratory_exam import LaboratoryExam, LaboratoryExamItem
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.laboratory_exam_repository import LaboratoryExamRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.laboratory_exam import LaboratoryExamService
from nutri_app.ui.date_format import format_date, format_datetime, parse_date
from nutri_app.ui.pages.base import Page


class LaboratoryExamsPage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__("Exames Laboratoriais", "Cadastro de exames, itens e alertas clinicos.")
        self.repository = LaboratoryExamRepository(connection_factory)
        self.patient_repository = PatientRepository(connection_factory)
        self.appointment_repository = AppointmentRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = LaboratoryExamService()
        self.selected_exam_id: int | None = None
        self.selected_item_index: int | None = None
        self.patient_ids_by_index: list[int] = []
        self.appointment_ids_by_index: list[int | None] = []
        self.items: list[LaboratoryExamItem] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar pelo nome do paciente")
        self.search.textChanged.connect(self._reload_exam_table)
        self.patient = QComboBox()
        self.patient.currentIndexChanged.connect(self._reload_appointments)
        self.appointment = QComboBox()
        self.exam_date = QLineEdit()
        self.exam_date.setPlaceholderText("mm-dd-aaaa")
        self.laboratory = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setFixedHeight(60)

        self.item_name = QLineEdit()
        self.item_value = QLineEdit()
        self.item_unit = QLineEdit()
        self.item_min = QLineEdit()
        self.item_max = QLineEdit()
        self.item_alert = QLineEdit()
        self.item_alert.setReadOnly(True)

        exam_form = QFormLayout()
        exam_form.addRow("Pesquisar", self.search)
        exam_form.addRow("Paciente", self.patient)
        exam_form.addRow("Consulta vinculada", self.appointment)
        exam_form.addRow("Data do exame", self.exam_date)
        exam_form.addRow("Laboratorio", self.laboratory)
        exam_form.addRow("Observacoes", self.notes)

        item_form = QFormLayout()
        item_form.addRow("Exame/item", self.item_name)
        item_form.addRow("Valor", self.item_value)
        item_form.addRow("Unidade", self.item_unit)
        item_form.addRow("Referencia minima", self.item_min)
        item_form.addRow("Referencia maxima", self.item_max)
        item_form.addRow("Alerta", self.item_alert)

        add_item = QPushButton("Adicionar item")
        add_item.clicked.connect(self._add_or_update_item)
        clear_item = QPushButton("Limpar item")
        clear_item.clicked.connect(self._clear_item_form)
        remove_item = QPushButton("Remover item")
        remove_item.clicked.connect(self._remove_item)

        item_actions = QHBoxLayout()
        for button in [add_item, clear_item, remove_item]:
            item_actions.addWidget(button)
        item_actions.addStretch()

        save = QPushButton("Salvar")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_exam)
        new = QPushButton("Novo")
        new.clicked.connect(self._clear_exam_form)
        delete = QPushButton("Excluir")
        delete.clicked.connect(self._delete_exam)

        exam_actions = QHBoxLayout()
        for button in [save, new, delete]:
            exam_actions.addWidget(button)
        exam_actions.addStretch()

        self.item_table = QTableWidget(0, 6)
        self.item_table.setHorizontalHeaderLabels(
            ["Item", "Valor", "Unidade", "Referencia", "Alerta", "Status"]
        )
        self.item_table.cellClicked.connect(self._select_item_from_table)

        self.exam_table = QTableWidget(0, 6)
        self.exam_table.setHorizontalHeaderLabels(
            ["ID", "Paciente", "Data", "Laboratorio", "Itens", "Alertas"]
        )
        self.exam_table.cellClicked.connect(self._select_exam_from_table)

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(exam_form)
        wrapper_layout.addRow(item_form)
        wrapper_layout.addRow(item_actions)
        wrapper_layout.addRow(self.item_table)
        wrapper_layout.addRow(exam_actions)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.exam_table)
        self.refresh()

    def refresh(self) -> None:
        self._reload_patients()
        self._reload_exam_table()

    def _save_exam(self) -> None:
        if self.patient.currentIndex() < 0 or not self.patient_ids_by_index:
            QMessageBox.warning(self, "Exames", "Cadastre um paciente antes do exame.")
            return
        if not self.items:
            QMessageBox.warning(self, "Exames", "Adicione pelo menos um item de exame.")
            return

        try:
            exam = self._build_exam()
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        if exam.id is None:
            exam_id = self.repository.add(exam)
            self._audit("criou_exame_laboratorial", exam_id, "Exame laboratorial criado.")
        else:
            self.repository.update(exam)
            exam_id = exam.id
            self._audit("atualizou_exame_laboratorial", exam_id, "Exame laboratorial atualizado.")

        self._clear_exam_form()
        self._reload_exam_table()

    def _build_exam(self) -> LaboratoryExam:
        return LaboratoryExam(
            id=self.selected_exam_id,
            patient_id=self.patient_ids_by_index[self.patient.currentIndex()],
            appointment_id=self.appointment_ids_by_index[self.appointment.currentIndex()],
            exam_date=parse_date(self.exam_date.text()),
            laboratory=self.laboratory.text().strip(),
            notes=self.notes.toPlainText().strip(),
            items=list(self.items),
        )

    def _delete_exam(self) -> None:
        if self.selected_exam_id is None:
            QMessageBox.warning(self, "Exames", "Selecione um exame para excluir.")
            return

        confirmation = QMessageBox.question(
            self,
            "Excluir exame",
            "Deseja excluir este exame? Os itens serao preservados por exclusao logica.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        exam_id = self.selected_exam_id
        self.repository.soft_delete(exam_id)
        self._audit("excluiu_exame_laboratorial", exam_id, "Exame removido por exclusao logica.")
        self._clear_exam_form()
        self._reload_exam_table()

    def _add_or_update_item(self) -> None:
        try:
            item = self._build_item()
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        if self.selected_item_index is None:
            self.items.append(item)
        else:
            self.items[self.selected_item_index] = item
        self._clear_item_form()
        self._reload_item_table()

    def _build_item(self) -> LaboratoryExamItem:
        name = self.item_name.text().strip()
        self.service.validate_item_name(name)
        value = self._optional_float(self.item_value.text(), "Valor")
        minimum = self._optional_float(self.item_min.text(), "Referencia minima")
        maximum = self._optional_float(self.item_max.text(), "Referencia maxima")
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError("Referencia minima nao pode ser maior que a maxima.")

        reference = self.service.build_reference(minimum, maximum)
        alert = self.service.classify_alert(value, minimum, maximum)
        self.item_alert.setText(alert)
        return LaboratoryExamItem(
            name=name,
            value=value,
            unit=self.item_unit.text().strip(),
            reference=reference,
            alert=alert,
        )

    def _remove_item(self) -> None:
        if self.selected_item_index is None:
            QMessageBox.warning(self, "Exames", "Selecione um item para remover.")
            return
        self.items.pop(self.selected_item_index)
        self._clear_item_form()
        self._reload_item_table()

    def _clear_exam_form(self) -> None:
        self.selected_exam_id = None
        if self.patient.count() > 0:
            self.patient.setCurrentIndex(0)
        for field in [self.exam_date, self.laboratory]:
            field.clear()
        self.notes.clear()
        self.items = []
        self._clear_item_form()
        self._reload_item_table()

    def _clear_item_form(self) -> None:
        self.selected_item_index = None
        for field in [
            self.item_name,
            self.item_value,
            self.item_unit,
            self.item_min,
            self.item_max,
            self.item_alert,
        ]:
            field.clear()

    def _reload_patients(self) -> None:
        current_patient_id = None
        if self.patient.currentIndex() >= 0 and self.patient_ids_by_index:
            current_patient_id = self.patient_ids_by_index[self.patient.currentIndex()]

        self.patient.blockSignals(True)
        self.patient.clear()
        self.patient_ids_by_index = []
        for patient in self.patient_repository.list_active():
            if patient.id is None:
                continue
            self.patient.addItem(patient.name)
            self.patient_ids_by_index.append(patient.id)
        if current_patient_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(current_patient_id))
        self.patient.blockSignals(False)
        self._reload_appointments()

    def _reload_appointments(self) -> None:
        self.appointment.clear()
        self.appointment.addItem("Sem consulta vinculada")
        self.appointment_ids_by_index = [None]
        if self.patient.currentIndex() < 0 or not self.patient_ids_by_index:
            return

        patient_id = self.patient_ids_by_index[self.patient.currentIndex()]
        for appointment in self.appointment_repository.list_by_period():
            if appointment.patient_id != patient_id or appointment.id is None:
                continue
            self.appointment.addItem(
                f"{format_datetime(appointment.scheduled_at)} - {appointment.kind.value}"
            )
            self.appointment_ids_by_index.append(appointment.id)

    def _reload_item_table(self) -> None:
        self.item_table.setRowCount(len(self.items))
        for row, item in enumerate(self.items):
            self.item_table.setItem(row, 0, QTableWidgetItem(item.name))
            self.item_table.setItem(row, 1, QTableWidgetItem(self._format_optional(item.value)))
            self.item_table.setItem(row, 2, QTableWidgetItem(item.unit))
            self.item_table.setItem(row, 3, QTableWidgetItem(item.reference))
            self.item_table.setItem(row, 4, QTableWidgetItem(item.alert))
            self.item_table.setItem(row, 5, QTableWidgetItem("alerta" if item.alert else "ok"))

    def _reload_exam_table(self) -> None:
        records = self.repository.list_active(self.search.text())
        self.exam_table.setRowCount(len(records))
        for row, record in enumerate(records):
            full = self.repository.get(record.id or 0)
            items = full.items if full is not None else []
            alerts = sum(1 for item in items if item.alert)
            self.exam_table.setItem(row, 0, QTableWidgetItem(str(record.id or "")))
            self.exam_table.setItem(row, 1, QTableWidgetItem(record.patient_name))
            self.exam_table.setItem(row, 2, QTableWidgetItem(format_date(record.exam_date)))
            self.exam_table.setItem(row, 3, QTableWidgetItem(record.laboratory))
            self.exam_table.setItem(row, 4, QTableWidgetItem(str(len(items))))
            self.exam_table.setItem(row, 5, QTableWidgetItem(str(alerts)))

    def _select_exam_from_table(self, row: int, _column: int) -> None:
        item = self.exam_table.item(row, 0)
        if item is None:
            return

        record = self.repository.get(int(item.text()))
        if record is None:
            QMessageBox.warning(self, "Exames", "Exame nao encontrado.")
            self._reload_exam_table()
            return

        self.selected_exam_id = record.id
        if record.patient_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(record.patient_id))
        self._reload_appointments()
        if record.appointment_id in self.appointment_ids_by_index:
            self.appointment.setCurrentIndex(self.appointment_ids_by_index.index(record.appointment_id))
        self.exam_date.setText(format_date(record.exam_date))
        self.laboratory.setText(record.laboratory)
        self.notes.setPlainText(record.notes)
        self.items = list(record.items)
        self._clear_item_form()
        self._reload_item_table()

    def _select_item_from_table(self, row: int, _column: int) -> None:
        if row < 0 or row >= len(self.items):
            return
        self.selected_item_index = row
        item = self.items[row]
        self.item_name.setText(item.name)
        self.item_value.setText(self._format_optional(item.value))
        self.item_unit.setText(item.unit)
        self.item_min.clear()
        self.item_max.clear()
        self.item_alert.setText(item.alert)

    def _optional_float(self, value: str, label: str) -> float | None:
        if not value.strip():
            return None
        try:
            return float(value.replace(",", "."))
        except ValueError as exc:
            raise ValueError(f"{label} deve ser numerico.") from exc

    def _format_optional(self, value: float | None) -> str:
        return "" if value is None else f"{value:g}"

    def _audit(self, action: str, exam_id: int, details: str) -> None:
        self.audit_repository.log(
            user_id=self.current_user_id,
            action=action,
            entity="exames_laboratoriais",
            entity_id=exam_id,
            details=details,
        )
