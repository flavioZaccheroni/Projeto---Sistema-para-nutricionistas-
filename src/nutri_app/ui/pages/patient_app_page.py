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
    QTabWidget,
    QTextEdit,
    QWidget,
)

from nutri_app.domain.patient_app import (
    PatientAppAccess,
    PatientAppAdherence,
    PatientAppPublication,
    PatientPublicationStatus,
    PatientPublicationType,
)
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.meal_plan_repository import MealPlanRepository
from nutri_app.repositories.patient_app_repository import PatientAppRepository
from nutri_app.repositories.patient_repository import PatientRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.services.patient_app import PatientAppService
from nutri_app.ui.date_format import format_date, parse_date, parse_optional_date, today_text
from nutri_app.ui.pages.base import Page


class PatientAppPage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__(
            "Aplicativo Paciente",
            "Acesso do paciente, plano publicado, orientacoes e adesao.",
        )
        self.repository = PatientAppRepository(connection_factory)
        self.patient_repository = PatientRepository(connection_factory)
        self.meal_plan_repository = MealPlanRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = PatientAppService()
        self.patient_ids_by_index: list[int] = []
        self.meal_plan_ids_by_index: list[int | None] = []
        self.publication_ids_by_index: list[int | None] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar pelo nome do paciente")
        self.search.textChanged.connect(self.refresh)
        self.summary = QLineEdit()
        self.summary.setReadOnly(True)

        self.patient = QComboBox()
        self.patient.currentIndexChanged.connect(self._reload_patient_dependents)
        self.email = QLineEdit()
        self.access_code = QLineEdit()
        self.access_notes = QLineEdit()

        self.publication_type = QComboBox()
        self.publication_type.addItems([item.value for item in PatientPublicationType])
        self.meal_plan = QComboBox()
        self.title = QLineEdit()
        self.content = QTextEdit()
        self.content.setFixedHeight(90)
        self.expiration_date = QLineEdit()
        self.expiration_date.setPlaceholderText("mm-dd-aaaa opcional")

        self.publication = QComboBox()
        self.record_date = QLineEdit(today_text())
        self.adherence = QLineEdit()
        self.mood = QLineEdit()
        self.difficulties = QLineEdit()
        self.adherence_notes = QTextEdit()
        self.adherence_notes.setFixedHeight(70)

        root_form = QFormLayout()
        root_form.addRow("Pesquisar", self.search)
        root_form.addRow("Paciente", self.patient)
        root_form.addRow("Resumo", self.summary)

        generate_code = QPushButton("Gerar codigo")
        generate_code.clicked.connect(self._generate_code)
        save_access = QPushButton("Salvar acesso")
        save_access.setObjectName("primaryButton")
        save_access.clicked.connect(self._save_access)

        access_form = QFormLayout()
        access_form.addRow("E-mail login", self.email)
        access_form.addRow("Codigo acesso", self.access_code)
        access_form.addRow("Observacoes", self.access_notes)
        access_actions = QHBoxLayout()
        access_actions.addWidget(generate_code)
        access_actions.addWidget(save_access)
        access_actions.addStretch()
        access_widget = QWidget()
        access_layout = QFormLayout(access_widget)
        access_layout.addRow(access_form)
        access_layout.addRow(access_actions)

        publish = QPushButton("Publicar")
        publish.setObjectName("primaryButton")
        publish.clicked.connect(self._publish_content)
        publication_form = QFormLayout()
        publication_form.addRow("Tipo", self.publication_type)
        publication_form.addRow("Plano vinculado", self.meal_plan)
        publication_form.addRow("Titulo", self.title)
        publication_form.addRow("Conteudo", self.content)
        publication_form.addRow("Expira em", self.expiration_date)
        publication_widget = QWidget()
        publication_layout = QFormLayout(publication_widget)
        publication_layout.addRow(publication_form)
        publication_layout.addRow(publish)

        save_adherence = QPushButton("Registrar adesao")
        save_adherence.setObjectName("primaryButton")
        save_adherence.clicked.connect(self._save_adherence)
        adherence_form = QFormLayout()
        adherence_form.addRow("Publicacao", self.publication)
        adherence_form.addRow("Data", self.record_date)
        adherence_form.addRow("Adesao %", self.adherence)
        adherence_form.addRow("Humor", self.mood)
        adherence_form.addRow("Dificuldades", self.difficulties)
        adherence_form.addRow("Observacoes", self.adherence_notes)
        adherence_widget = QWidget()
        adherence_layout = QFormLayout(adherence_widget)
        adherence_layout.addRow(adherence_form)
        adherence_layout.addRow(save_adherence)

        tabs = QTabWidget()
        tabs.addTab(access_widget, "Acesso")
        tabs.addTab(publication_widget, "Publicacoes")
        tabs.addTab(adherence_widget, "Adesao")

        self.access_table = QTableWidget(0, 5)
        self.access_table.setHorizontalHeaderLabels(
            ["ID", "Paciente", "E-mail", "Codigo", "Ativo"]
        )
        self.publication_table = QTableWidget(0, 6)
        self.publication_table.setHorizontalHeaderLabels(
            ["ID", "Paciente", "Tipo", "Titulo", "Status", "Data"]
        )
        self.adherence_table = QTableWidget(0, 6)
        self.adherence_table.setHorizontalHeaderLabels(
            ["ID", "Paciente", "Publicacao", "Data", "Adesao", "Classificacao"]
        )

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(root_form)
        wrapper_layout.addRow(tabs)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.access_table)
        self.layout.addWidget(self.publication_table)
        self.layout.addWidget(self.adherence_table)
        self.refresh()

    def refresh(self) -> None:
        self._reload_patients()
        self._reload_patient_dependents()
        self._reload_tables()
        self._reload_summary()

    def _generate_code(self) -> None:
        self.access_code.setText(self.service.generate_access_code())

    def _save_access(self) -> None:
        if not self.patient_ids_by_index:
            QMessageBox.warning(self, "Aplicativo Paciente", "Cadastre um paciente primeiro.")
            return
        access = PatientAppAccess(
            patient_id=self.patient_ids_by_index[self.patient.currentIndex()],
            email_login=self.email.text().strip().lower(),
            access_code=self.access_code.text().strip(),
            notes=self.access_notes.text().strip(),
        )
        try:
            self.service.validate_access(access)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc))
            return
        access_id = self.repository.upsert_access(access)
        self._audit("salvou_acesso_app_paciente", access_id, access.email_login)
        self._reload_tables()
        self._reload_summary()

    def _publish_content(self) -> None:
        if not self.patient_ids_by_index:
            QMessageBox.warning(self, "Aplicativo Paciente", "Cadastre um paciente primeiro.")
            return
        publication = PatientAppPublication(
            patient_id=self.patient_ids_by_index[self.patient.currentIndex()],
            meal_plan_id=self.meal_plan_ids_by_index[self.meal_plan.currentIndex()],
            publication_type=PatientPublicationType(self.publication_type.currentText()),
            title=self.title.text().strip(),
            content=self.content.toPlainText().strip(),
            status=PatientPublicationStatus.PUBLISHED,
            expiration_date=self._optional_date(self.expiration_date.text()),
        )
        try:
            self.service.validate_publication(publication)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc))
            return
        publication_id = self.repository.add_publication(publication)
        self._audit("publicou_conteudo_app_paciente", publication_id, publication.title)
        self.title.clear()
        self.content.clear()
        self.expiration_date.clear()
        self._reload_patient_dependents()
        self._reload_tables()
        self._reload_summary()

    def _save_adherence(self) -> None:
        if not self.patient_ids_by_index:
            QMessageBox.warning(self, "Aplicativo Paciente", "Cadastre um paciente primeiro.")
            return
        adherence = PatientAppAdherence(
            patient_id=self.patient_ids_by_index[self.patient.currentIndex()],
            publication_id=self.publication_ids_by_index[self.publication.currentIndex()],
            record_date=parse_date(self.record_date.text()),
            adherence_percent=self._required_float(self.adherence.text(), "Adesao"),
            mood=self.mood.text().strip(),
            difficulties=self.difficulties.text().strip(),
            notes=self.adherence_notes.toPlainText().strip(),
        )
        try:
            self.service.validate_adherence(adherence)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc))
            return
        adherence_id = self.repository.add_adherence(adherence)
        self._audit(
            "registrou_adesao_app_paciente",
            adherence_id,
            f"{adherence.adherence_percent}%",
        )
        self.adherence.clear()
        self.mood.clear()
        self.difficulties.clear()
        self.adherence_notes.clear()
        self._reload_tables()
        self._reload_summary()

    def _reload_patients(self) -> None:
        current_id = (
            self.patient_ids_by_index[self.patient.currentIndex()]
            if self.patient.currentIndex() >= 0 and self.patient_ids_by_index
            else None
        )
        self.patient.blockSignals(True)
        self.patient.clear()
        self.patient_ids_by_index = []
        for patient in self.patient_repository.list_active():
            if patient.id is not None:
                self.patient.addItem(patient.name)
                self.patient_ids_by_index.append(patient.id)
        if current_id in self.patient_ids_by_index:
            self.patient.setCurrentIndex(self.patient_ids_by_index.index(current_id))
        self.patient.blockSignals(False)

    def _reload_patient_dependents(self) -> None:
        patient_id = (
            self.patient_ids_by_index[self.patient.currentIndex()]
            if self.patient.currentIndex() >= 0 and self.patient_ids_by_index
            else None
        )
        self.meal_plan.clear()
        self.meal_plan_ids_by_index = [None]
        self.meal_plan.addItem("Sem plano")
        self.publication.clear()
        self.publication_ids_by_index = [None]
        self.publication.addItem("Sem publicacao")
        if patient_id is None:
            return
        for plan in self.meal_plan_repository.list_active():
            if plan.patient_id == patient_id and plan.id is not None:
                self.meal_plan.addItem(f"{format_date(plan.start_date)} - {plan.objective}")
                self.meal_plan_ids_by_index.append(plan.id)
        for publication in self.repository.list_publications():
            if publication.patient_id == patient_id and publication.id is not None:
                self.publication.addItem(publication.title)
                self.publication_ids_by_index.append(publication.id)

    def _reload_tables(self) -> None:
        query = self.search.text()
        accesses = self.repository.list_accesses(query)
        self.access_table.setRowCount(len(accesses))
        for row, access in enumerate(accesses):
            self.access_table.setItem(row, 0, QTableWidgetItem(str(access.id or "")))
            self.access_table.setItem(row, 1, QTableWidgetItem(access.patient_name))
            self.access_table.setItem(row, 2, QTableWidgetItem(access.email_login))
            self.access_table.setItem(row, 3, QTableWidgetItem(access.access_code))
            self.access_table.setItem(row, 4, QTableWidgetItem("Sim" if access.active else "Nao"))

        publications = self.repository.list_publications(query)
        self.publication_table.setRowCount(len(publications))
        for row, publication in enumerate(publications):
            self.publication_table.setItem(row, 0, QTableWidgetItem(str(publication.id or "")))
            self.publication_table.setItem(row, 1, QTableWidgetItem(publication.patient_name))
            publication_type = publication.publication_type.value
            self.publication_table.setItem(row, 2, QTableWidgetItem(publication_type))
            self.publication_table.setItem(row, 3, QTableWidgetItem(publication.title))
            self.publication_table.setItem(row, 4, QTableWidgetItem(publication.status.value))
            self.publication_table.setItem(
                row,
                5,
                QTableWidgetItem(format_date(publication.publication_date)),
            )

        adherences = self.repository.list_adherences(query)
        self.adherence_table.setRowCount(len(adherences))
        for row, adherence in enumerate(adherences):
            classification = self.service.adherence_classification(adherence.adherence_percent)
            self.adherence_table.setItem(row, 0, QTableWidgetItem(str(adherence.id or "")))
            self.adherence_table.setItem(row, 1, QTableWidgetItem(adherence.patient_name))
            self.adherence_table.setItem(row, 2, QTableWidgetItem(adherence.publication_title))
            record_date = format_date(adherence.record_date)
            adherence_label = f"{adherence.adherence_percent:.0f}%"
            self.adherence_table.setItem(row, 3, QTableWidgetItem(record_date))
            self.adherence_table.setItem(row, 4, QTableWidgetItem(adherence_label))
            self.adherence_table.setItem(row, 5, QTableWidgetItem(classification))

    def _reload_summary(self) -> None:
        summary = self.repository.summary()
        self.summary.setText(
            f"Acessos ativos: {summary.total_accesses} | "
            f"Publicacoes: {summary.total_published} | "
            f"Adesao media: {summary.average_adherence:.1f}%"
        )

    def _optional_date(self, value: str) -> date | None:
        return parse_optional_date(value)

    def _required_float(self, value: str, field: str) -> float:
        try:
            return float(value.replace(",", "."))
        except ValueError as exc:
            raise ValueError(f"{field} deve ser numerico.") from exc

    def _audit(self, action: str, entity_id: int | None, details: str) -> None:
        self.audit_repository.log(
            self.current_user_id,
            action,
            "paciente_app",
            entity_id,
            details,
        )
