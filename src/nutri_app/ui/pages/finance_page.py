from __future__ import annotations

from datetime import date

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

from nutri_app.domain.finance import FinancialEntry, FinancialEntryType, FinancialStatus
from nutri_app.repositories.appointment_repository import AppointmentRepository
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.finance_repository import FinanceRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.finance import FinanceService
from nutri_app.ui.date_format import format_date, format_datetime, parse_date, parse_optional_date
from nutri_app.ui.pages.base import Page


class FinancePage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__(
            "Financeiro",
            "Planos, pagamentos, recebimentos, inadimplencia e relatorio mensal.",
        )
        self.repository = FinanceRepository(connection_factory)
        self.patient_repository = PatientRepository(connection_factory)
        self.appointment_repository = AppointmentRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = FinanceService()
        self.selected_entry_id: int | None = None
        self.patient_ids_by_index: list[int | None] = []
        self.appointment_ids_by_index: list[int | None] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar pelo paciente")
        self.search.textChanged.connect(self._reload_table)
        self.patient = QComboBox()
        self.patient.currentIndexChanged.connect(self._reload_appointments)
        self.appointment = QComboBox()
        self.entry_type = QComboBox()
        self.entry_type.addItems([item.value for item in FinancialEntryType])
        self.category = QLineEdit()
        self.description = QLineEdit()
        self.amount = QLineEdit()
        self.due_date = QLineEdit()
        self.due_date.setPlaceholderText("mm-dd-aaaa")
        self.payment_date = QLineEdit()
        self.payment_date.setPlaceholderText("mm-dd-aaaa opcional")
        self.payment_method = QLineEdit()
        self.status = QComboBox()
        self.status.addItems([item.value for item in FinancialStatus])
        self.notes = QTextEdit()
        self.notes.setFixedHeight(60)

        form = QFormLayout()
        form.addRow("Pesquisar", self.search)
        form.addRow("Paciente", self.patient)
        form.addRow("Consulta vinculada", self.appointment)
        form.addRow("Tipo", self.entry_type)
        form.addRow("Categoria", self.category)
        form.addRow("Descricao", self.description)
        form.addRow("Valor", self.amount)
        form.addRow("Vencimento", self.due_date)
        form.addRow("Pagamento", self.payment_date)
        form.addRow("Forma pagamento", self.payment_method)
        form.addRow("Status", self.status)
        form.addRow("Observacoes", self.notes)

        save = QPushButton("Salvar")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_entry)
        new = QPushButton("Novo")
        new.clicked.connect(self._clear_form)
        mark_paid = QPushButton("Marcar pago")
        mark_paid.clicked.connect(self._mark_paid)
        cancel = QPushButton("Cancelar")
        cancel.clicked.connect(lambda: self._set_status(FinancialStatus.CANCELED))
        delete = QPushButton("Excluir")
        delete.clicked.connect(self._delete_entry)

        actions = QHBoxLayout()
        for button in [save, new, mark_paid, cancel, delete]:
            actions.addWidget(button)
        actions.addStretch()

        self.start_filter = QLineEdit()
        self.start_filter.setPlaceholderText("Inicio mm-dd-aaaa")
        self.end_filter = QLineEdit()
        self.end_filter.setPlaceholderText("Fim mm-dd-aaaa")
        self.status_filter = QComboBox()
        self.status_filter.addItem("Todos")
        self.status_filter.addItems([item.value for item in FinancialStatus])
        filter_button = QPushButton("Filtrar")
        filter_button.clicked.connect(self._reload_table)

        filters = QHBoxLayout()
        filters.addWidget(self.start_filter)
        filters.addWidget(self.end_filter)
        filters.addWidget(self.status_filter)
        filters.addWidget(filter_button)

        self.summary = QLineEdit()
        self.summary.setReadOnly(True)
        summary_button = QPushButton("Resumo mensal")
        summary_button.clicked.connect(self._show_monthly_summary)
        summary_layout = QHBoxLayout()
        summary_layout.addWidget(self.summary)
        summary_layout.addWidget(summary_button)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Paciente", "Tipo", "Categoria", "Descricao", "Valor", "Venc.", "Status"]
        )
        self.table.cellClicked.connect(self._select_entry_from_table)

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)
        wrapper_layout.addRow("Filtros", filters)
        wrapper_layout.addRow("Relatorio mensal", summary_layout)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        self._reload_patients()
        self._reload_appointments()
        self._reload_table()

    def _save_entry(self) -> None:
        try:
            entry = self._build_entry()
            status = self.service.normalize_status(entry)
            entry = FinancialEntry(**{**entry.__dict__, "status": status})
            self.service.validate(entry)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        if entry.id is None:
            entry_id = self.repository.add(entry)
            self._audit("criou_lancamento_financeiro", entry_id, "Lancamento criado.")
        else:
            self.repository.update(entry)
            entry_id = entry.id
            self._audit("atualizou_lancamento_financeiro", entry_id, "Lancamento atualizado.")

        self._clear_form()
        self._reload_table()

    def _build_entry(self) -> FinancialEntry:
        payment_date = self._optional_date(self.payment_date.text())
        return FinancialEntry(
            id=self.selected_entry_id,
            patient_id=self.patient_ids_by_index[self.patient.currentIndex()],
            appointment_id=self.appointment_ids_by_index[self.appointment.currentIndex()],
            entry_type=FinancialEntryType(self.entry_type.currentText()),
            category=self.category.text().strip(),
            description=self.description.text().strip(),
            amount=self._required_float(self.amount.text(), "Valor"),
            due_date=parse_date(self.due_date.text()),
            payment_date=payment_date,
            payment_method=self.payment_method.text().strip(),
            status=FinancialStatus(self.status.currentText()),
            notes=self.notes.toPlainText().strip(),
        )

    def _mark_paid(self) -> None:
        if self.selected_entry_id is None:
            QMessageBox.warning(self, "Financeiro", "Selecione um lancamento.")
            return
        if not self.payment_date.text().strip():
            self.payment_date.setText(format_date(date.today()))
        self.status.setCurrentText(FinancialStatus.PAID.value)
        self._save_entry()

    def _set_status(self, status: FinancialStatus) -> None:
        if self.selected_entry_id is None:
            QMessageBox.warning(self, "Financeiro", "Selecione um lancamento.")
            return
        self.status.setCurrentText(status.value)
        self._save_entry()

    def _delete_entry(self) -> None:
        if self.selected_entry_id is None:
            QMessageBox.warning(self, "Financeiro", "Selecione um lancamento para excluir.")
            return

        confirmation = QMessageBox.question(
            self,
            "Excluir lancamento",
            "Deseja excluir este lancamento? O registro sera preservado por exclusao logica.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        entry_id = self.selected_entry_id
        self.repository.soft_delete(entry_id)
        self._audit("excluiu_lancamento_financeiro", entry_id, "Lancamento removido.")
        self._clear_form()
        self._reload_table()

    def _clear_form(self) -> None:
        self.selected_entry_id = None
        if self.patient.count() > 0:
            self.patient.setCurrentIndex(0)
        self.entry_type.setCurrentIndex(0)
        self.status.setCurrentText(FinancialStatus.OPEN.value)
        for field in [
            self.category,
            self.description,
            self.amount,
            self.due_date,
            self.payment_date,
            self.payment_method,
        ]:
            field.clear()
        self.notes.clear()

    def _reload_patients(self) -> None:
        current_id = (
            self.patient_ids_by_index[self.patient.currentIndex()]
            if self.patient.currentIndex() >= 0 and self.patient_ids_by_index
            else None
        )
        self.patient.blockSignals(True)
        self.patient.clear()
        self.patient_ids_by_index = [None]
        self.patient.addItem("Sem paciente")
        for patient in self.patient_repository.list_active():
            if patient.id is not None:
                self.patient.addItem(patient.name)
                self.patient_ids_by_index.append(patient.id)
        if current_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(current_id))
        self.patient.blockSignals(False)

    def _reload_appointments(self) -> None:
        current_id = (
            self.appointment_ids_by_index[self.appointment.currentIndex()]
            if self.appointment.currentIndex() >= 0 and self.appointment_ids_by_index
            else None
        )
        patient_id = self.patient_ids_by_index[self.patient.currentIndex()]
        self.appointment.clear()
        self.appointment_ids_by_index = [None]
        self.appointment.addItem("Sem consulta")
        if patient_id is not None:
            for appointment in self.appointment_repository.list_by_period():
                if appointment.patient_id == patient_id and appointment.id is not None:
                    label = format_datetime(appointment.scheduled_at)
                    self.appointment.addItem(f"{label} - {appointment.kind.value}")
                    self.appointment_ids_by_index.append(appointment.id)
        if current_id in self.appointment_ids_by_index:
            self.appointment.setCurrentIndex(self.appointment_ids_by_index.index(current_id))

    def _reload_table(self) -> None:
        records = self.repository.list_active(
            patient_query=self.search.text(),
            status=self._filter_status(),
            start=self._optional_date(self.start_filter.text()),
            end=self._optional_date(self.end_filter.text()),
        )
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(str(record.id or "")))
            self.table.setItem(row, 1, QTableWidgetItem(record.patient_name))
            self.table.setItem(row, 2, QTableWidgetItem(record.entry_type.value))
            self.table.setItem(row, 3, QTableWidgetItem(record.category))
            self.table.setItem(row, 4, QTableWidgetItem(record.description))
            self.table.setItem(row, 5, QTableWidgetItem(f"R$ {record.amount:.2f}"))
            self.table.setItem(row, 6, QTableWidgetItem(format_date(record.due_date)))
            self.table.setItem(row, 7, QTableWidgetItem(record.status.value))

    def _select_entry_from_table(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return
        entry = self.repository.get(int(item.text()))
        if entry is None:
            QMessageBox.warning(self, "Financeiro", "Lancamento nao encontrado.")
            self._reload_table()
            return
        self.selected_entry_id = entry.id
        if entry.patient_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(entry.patient_id))
        self._reload_appointments()
        if entry.appointment_id in self.appointment_ids_by_index:
            self.appointment.setCurrentIndex(
                self.appointment_ids_by_index.index(entry.appointment_id)
            )
        self.entry_type.setCurrentText(entry.entry_type.value)
        self.category.setText(entry.category)
        self.description.setText(entry.description)
        self.amount.setText(f"{entry.amount:.2f}")
        self.due_date.setText(format_date(entry.due_date))
        self.payment_date.setText(format_date(entry.payment_date))
        self.payment_method.setText(entry.payment_method)
        self.status.setCurrentText(entry.status.value)
        self.notes.setPlainText(entry.notes)

    def _show_monthly_summary(self) -> None:
        reference = self._optional_date(self.start_filter.text()) or date.today()
        summary = self.repository.monthly_summary(reference.year, reference.month)
        self.summary.setText(
            f"Receber R$ {summary.total_receivable:.2f} | "
            f"Recebido R$ {summary.total_received:.2f} | "
            f"Pagar R$ {summary.total_payable:.2f} | "
            f"Pago R$ {summary.total_paid:.2f} | "
            f"Vencido R$ {summary.total_overdue:.2f} | "
            f"Saldo R$ {summary.open_balance:.2f}"
        )

    def _filter_status(self) -> FinancialStatus | None:
        if self.status_filter.currentText() == "Todos":
            return None
        return FinancialStatus(self.status_filter.currentText())

    def _optional_date(self, value: str) -> date | None:
        return parse_optional_date(value)

    def _required_float(self, value: str, field: str) -> float:
        try:
            return float(value.replace(",", "."))
        except ValueError as exc:
            raise ValueError(f"{field} deve ser numerico.") from exc

    def _audit(self, action: str, entity_id: int | None, details: str) -> None:
        self.audit_repository.log(self.current_user_id, action, "financeiro", entity_id, details)
