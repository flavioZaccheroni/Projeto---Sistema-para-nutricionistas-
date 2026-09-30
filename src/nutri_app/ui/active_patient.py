from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class ActivePatientContext(QObject):
    """Paciente atualmente em atendimento, compartilhado entre as telas
    clinicas para que trocar de tela nao exija reselecionar o paciente.
    """

    changed = Signal(object)  # int | None

    def __init__(self) -> None:
        super().__init__()
        self._patient_id: int | None = None

    @property
    def patient_id(self) -> int | None:
        return self._patient_id

    def set_patient(self, patient_id: int | None) -> None:
        if patient_id is None or patient_id == self._patient_id:
            return
        self._patient_id = patient_id
        self.changed.emit(patient_id)
