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

from nutri_app.domain.supplement import Supplement, SupplementType
from nutri_app.repositories.audit_repository import AuditRepository
from nutri_app.repositories.sqlite_connection import SQLiteConnectionFactory
from nutri_app.repositories.supplement_repository import SupplementRepository
from nutri_app.services.supplement import SupplementService
from nutri_app.ui.pages.base import Page


class SupplementsPage(Page):
    def __init__(
        self,
        connection_factory: SQLiteConnectionFactory,
        audit_repository: AuditRepository,
        current_user_id: int,
    ) -> None:
        super().__init__("Suplementos", "Suplementos, formulas enterais e modulos.")
        self.repository = SupplementRepository(connection_factory)
        self.audit_repository = audit_repository
        self.current_user_id = current_user_id
        self.service = SupplementService()
        self.selected_supplement_id: int | None = None

        self.search = QLineEdit()
        self.search.setPlaceholderText("Pesquisar por nome, tipo ou fabricante")
        self.search.textChanged.connect(self._reload_table)
        self.name = QLineEdit()
        self.supplement_type = QComboBox()
        self.supplement_type.addItems([item.value for item in SupplementType])
        self.manufacturer = QLineEdit()
        self.presentation = QLineEdit()
        self.base_portion = QLineEdit("100")
        self.portion_unit = QLineEdit("ml")
        self.caloric_density = QLineEdit()
        self.osmolarity = QLineEdit()
        self.energy = QLineEdit()
        self.protein = QLineEdit()
        self.carbohydrate = QLineEdit()
        self.fat = QLineEdit()
        self.fiber = QLineEdit()
        self.sodium = QLineEdit()
        self.dose = QLineEdit("100")
        self.dose_result = QLineEdit()
        self.dose_result.setReadOnly(True)
        self.composition = QTextEdit()
        self.composition.setFixedHeight(55)
        self.indications = QTextEdit()
        self.indications.setFixedHeight(55)
        self.contraindications = QTextEdit()
        self.contraindications.setFixedHeight(55)
        self.notes = QTextEdit()
        self.notes.setFixedHeight(55)

        form = QFormLayout()
        form.addRow("Pesquisar", self.search)
        form.addRow("Nome", self.name)
        form.addRow("Tipo", self.supplement_type)
        form.addRow("Fabricante", self.manufacturer)
        form.addRow("Apresentacao", self.presentation)
        form.addRow("Porcao base", self.base_portion)
        form.addRow("Unidade porcao", self.portion_unit)
        form.addRow("Densidade kcal/ml", self.caloric_density)
        form.addRow("Osmolaridade mOsm/L", self.osmolarity)
        form.addRow("Energia (kcal)", self.energy)
        form.addRow("Proteina (g)", self.protein)
        form.addRow("Carboidrato (g)", self.carbohydrate)
        form.addRow("Lipidios (g)", self.fat)
        form.addRow("Fibras (g)", self.fiber)
        form.addRow("Sodio (mg)", self.sodium)
        form.addRow("Dose para calculo", self.dose)
        form.addRow("Resultado dose", self.dose_result)
        form.addRow("Composicao", self.composition)
        form.addRow("Indicacoes", self.indications)
        form.addRow("Contraindicacoes", self.contraindications)
        form.addRow("Observacoes", self.notes)

        calculate = QPushButton("Calcular dose")
        calculate.clicked.connect(self._calculate_dose)
        save = QPushButton("Salvar")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_supplement)
        new = QPushButton("Novo")
        new.clicked.connect(self._clear_form)
        delete = QPushButton("Excluir")
        delete.clicked.connect(self._delete_supplement)

        actions = QHBoxLayout()
        for button in [calculate, save, new, delete]:
            actions.addWidget(button)
        actions.addStretch()

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nome", "Tipo", "Fabricante", "Porcao", "Kcal", "Proteina", "Densidade"]
        )
        self.table.cellClicked.connect(self._select_supplement_from_table)

        wrapper = QWidget()
        wrapper_layout = QFormLayout(wrapper)
        wrapper_layout.addRow(form)
        wrapper_layout.addRow(actions)

        self.layout.addWidget(wrapper)
        self.layout.addWidget(self.table)
        self.refresh()

    def refresh(self) -> None:
        self._reload_table()

    def _save_supplement(self) -> None:
        try:
            supplement = self._build_supplement()
            self.service.validate(supplement)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        if supplement.id is None:
            supplement_id = self.repository.add(supplement)
            self._audit("criou_suplemento", supplement_id, "Suplemento criado.")
        else:
            self.repository.update(supplement)
            supplement_id = supplement.id
            self._audit("atualizou_suplemento", supplement_id, "Suplemento atualizado.")

        self._clear_form()
        self._reload_table()

    def _build_supplement(self) -> Supplement:
        return Supplement(
            id=self.selected_supplement_id,
            name=self.name.text().strip(),
            supplement_type=SupplementType(self.supplement_type.currentText()),
            manufacturer=self.manufacturer.text().strip(),
            presentation=self.presentation.text().strip(),
            base_portion=self._required_float(self.base_portion.text(), "Porcao base"),
            portion_unit=self.portion_unit.text().strip(),
            caloric_density=self._optional_float(self.caloric_density.text(), "Densidade calorica"),
            osmolarity=self._optional_float(self.osmolarity.text(), "Osmolaridade"),
            energy_kcal=self._optional_float(self.energy.text(), "Energia") or 0,
            protein_g=self._optional_float(self.protein.text(), "Proteina") or 0,
            carbohydrate_g=self._optional_float(self.carbohydrate.text(), "Carboidrato") or 0,
            fat_g=self._optional_float(self.fat.text(), "Lipidios") or 0,
            fiber_g=self._optional_float(self.fiber.text(), "Fibras") or 0,
            sodium_mg=self._optional_float(self.sodium.text(), "Sodio") or 0,
            composition=self.composition.toPlainText().strip(),
            indications=self.indications.toPlainText().strip(),
            contraindications=self.contraindications.toPlainText().strip(),
            notes=self.notes.toPlainText().strip(),
        )

    def _calculate_dose(self) -> None:
        try:
            supplement = self._build_supplement()
            dose = self._required_float(self.dose.text(), "Dose")
            result = self.service.calculate_dose(supplement, dose)
        except ValueError as exc:
            QMessageBox.warning(self, "Validacao", str(exc) or "Valores invalidos.")
            return

        self.dose_result.setText(
            f"{result.energy_kcal:.0f} kcal | "
            f"P {result.protein_g:.1f}g | "
            f"C {result.carbohydrate_g:.1f}g | "
            f"L {result.fat_g:.1f}g"
        )

    def _delete_supplement(self) -> None:
        if self.selected_supplement_id is None:
            QMessageBox.warning(self, "Suplementos", "Selecione um suplemento para excluir.")
            return

        confirmation = QMessageBox.question(
            self,
            "Excluir suplemento",
            "Deseja excluir este suplemento? O registro sera preservado por exclusao logica.",
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        supplement_id = self.selected_supplement_id
        self.repository.soft_delete(supplement_id)
        self._audit("excluiu_suplemento", supplement_id, "Suplemento removido por exclusao logica.")
        self._clear_form()
        self._reload_table()

    def _clear_form(self) -> None:
        self.selected_supplement_id = None
        self.supplement_type.setCurrentIndex(0)
        self.base_portion.setText("100")
        self.portion_unit.setText("ml")
        self.dose.setText("100")
        for field in [
            self.name,
            self.manufacturer,
            self.presentation,
            self.caloric_density,
            self.osmolarity,
            self.energy,
            self.protein,
            self.carbohydrate,
            self.fat,
            self.fiber,
            self.sodium,
            self.dose_result,
        ]:
            field.clear()
        self.composition.clear()
        self.indications.clear()
        self.contraindications.clear()
        self.notes.clear()

    def _reload_table(self) -> None:
        records = self.repository.list_active(self.search.text())
        self.table.setRowCount(len(records))
        for row, record in enumerate(records):
            self.table.setItem(row, 0, QTableWidgetItem(str(record.id or "")))
            self.table.setItem(row, 1, QTableWidgetItem(record.name))
            self.table.setItem(row, 2, QTableWidgetItem(record.supplement_type.value))
            self.table.setItem(row, 3, QTableWidgetItem(record.manufacturer))
            portion_label = f"{record.base_portion:g} {record.portion_unit}"
            self.table.setItem(row, 4, QTableWidgetItem(portion_label))
            self.table.setItem(row, 5, QTableWidgetItem(f"{record.energy_kcal:.0f}"))
            self.table.setItem(row, 6, QTableWidgetItem(f"{record.protein_g:.1f}"))
            caloric_density = self._format_optional(record.caloric_density)
            self.table.setItem(row, 7, QTableWidgetItem(caloric_density))

    def _select_supplement_from_table(self, row: int, _column: int) -> None:
        item = self.table.item(row, 0)
        if item is None:
            return

        record = self.repository.get(int(item.text()))
        if record is None:
            QMessageBox.warning(self, "Suplementos", "Suplemento nao encontrado.")
            self._reload_table()
            return

        self.selected_supplement_id = record.id
        self.name.setText(record.name)
        self.supplement_type.setCurrentText(record.supplement_type.value)
        self.manufacturer.setText(record.manufacturer)
        self.presentation.setText(record.presentation)
        self.base_portion.setText(f"{record.base_portion:g}")
        self.portion_unit.setText(record.portion_unit)
        self.caloric_density.setText(self._format_optional(record.caloric_density))
        self.osmolarity.setText(self._format_optional(record.osmolarity))
        self.energy.setText(f"{record.energy_kcal:g}")
        self.protein.setText(f"{record.protein_g:g}")
        self.carbohydrate.setText(f"{record.carbohydrate_g:g}")
        self.fat.setText(f"{record.fat_g:g}")
        self.fiber.setText(f"{record.fiber_g:g}")
        self.sodium.setText(f"{record.sodium_mg:g}")
        self.composition.setPlainText(record.composition)
        self.indications.setPlainText(record.indications)
        self.contraindications.setPlainText(record.contraindications)
        self.notes.setPlainText(record.notes)
        self.dose_result.clear()

    def _required_float(self, value: str, label: str) -> float:
        parsed = self._optional_float(value, label)
        if parsed is None or parsed <= 0:
            raise ValueError(f"{label} deve ser maior que zero.")
        return parsed

    def _optional_float(self, value: str, label: str) -> float | None:
        if not value.strip():
            return None
        try:
            parsed = float(value.replace(",", "."))
        except ValueError as exc:
            raise ValueError(f"{label} deve ser numerico.") from exc
        if parsed < 0:
            raise ValueError(f"{label} nao pode ser negativo.")
        return parsed

    def _format_optional(self, value: float | None) -> str:
        return "" if value is None else f"{value:g}"

    def _audit(self, action: str, supplement_id: int, details: str) -> None:
        self.audit_repository.log(
            user_id=self.current_user_id,
            action=action,
            entity="suplementos",
            entity_id=supplement_id,
            details=details,
        )
