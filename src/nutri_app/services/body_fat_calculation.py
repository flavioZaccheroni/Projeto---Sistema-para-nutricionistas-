from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from nutri_app.domain.energy_expenditure import BiologicalSex
from nutri_app.services.clinical_validation import ClinicalValidationMatrix


class SkinfoldSite(StrEnum):
    CHEST = "Peitoral"
    MIDAXILLARY = "Axilar media"
    TRICEPS = "Triceps"
    SUBSCAPULAR = "Subescapular"
    ABDOMEN = "Abdominal"
    SUPRAILIAC = "Supra-iliaca"
    THIGH = "Coxa"
    BICEPS = "Biceps"


class SkinfoldProtocol(StrEnum):
    POLLOCK_3 = "Pollock 3 dobras"
    POLLOCK_7 = "Pollock 7 dobras"
    DURNIN_WOMERSLEY = "Durnin & Womersley"
    FAULKNER = "Faulkner"


@dataclass(frozen=True)
class CalculationTrace:
    formula: str
    reference: str
    details: str


class BodyFatCalculationService:
    REFERENCE_KEYS = {
        SkinfoldProtocol.POLLOCK_3: "Pollock 3 dobras",
        SkinfoldProtocol.POLLOCK_7: "Pollock 7 dobras",
        SkinfoldProtocol.DURNIN_WOMERSLEY: "Durnin & Womersley",
        SkinfoldProtocol.FAULKNER: "Faulkner",
    }

    REQUIRED_SITES = {
        SkinfoldProtocol.POLLOCK_3: {
            BiologicalSex.MALE: (SkinfoldSite.CHEST, SkinfoldSite.ABDOMEN, SkinfoldSite.THIGH),
            BiologicalSex.FEMALE: (
                SkinfoldSite.TRICEPS,
                SkinfoldSite.SUPRAILIAC,
                SkinfoldSite.THIGH,
            ),
        },
        SkinfoldProtocol.POLLOCK_7: {
            BiologicalSex.MALE: (
                SkinfoldSite.CHEST,
                SkinfoldSite.MIDAXILLARY,
                SkinfoldSite.TRICEPS,
                SkinfoldSite.SUBSCAPULAR,
                SkinfoldSite.ABDOMEN,
                SkinfoldSite.SUPRAILIAC,
                SkinfoldSite.THIGH,
            ),
            BiologicalSex.FEMALE: (
                SkinfoldSite.CHEST,
                SkinfoldSite.MIDAXILLARY,
                SkinfoldSite.TRICEPS,
                SkinfoldSite.SUBSCAPULAR,
                SkinfoldSite.ABDOMEN,
                SkinfoldSite.SUPRAILIAC,
                SkinfoldSite.THIGH,
            ),
        },
        SkinfoldProtocol.DURNIN_WOMERSLEY: {
            BiologicalSex.MALE: (
                SkinfoldSite.BICEPS,
                SkinfoldSite.TRICEPS,
                SkinfoldSite.SUBSCAPULAR,
                SkinfoldSite.SUPRAILIAC,
            ),
            BiologicalSex.FEMALE: (
                SkinfoldSite.BICEPS,
                SkinfoldSite.TRICEPS,
                SkinfoldSite.SUBSCAPULAR,
                SkinfoldSite.SUPRAILIAC,
            ),
        },
        SkinfoldProtocol.FAULKNER: {
            BiologicalSex.MALE: (
                SkinfoldSite.TRICEPS,
                SkinfoldSite.SUBSCAPULAR,
                SkinfoldSite.SUPRAILIAC,
                SkinfoldSite.ABDOMEN,
            ),
            BiologicalSex.FEMALE: (
                SkinfoldSite.TRICEPS,
                SkinfoldSite.SUBSCAPULAR,
                SkinfoldSite.SUPRAILIAC,
                SkinfoldSite.ABDOMEN,
            ),
        },
    }

    DURNIN_MALE = (
        (19, (1.1620, 0.0630)),
        (29, (1.1631, 0.0632)),
        (39, (1.1422, 0.0544)),
        (49, (1.1620, 0.0700)),
        (200, (1.1715, 0.0779)),
    )
    DURNIN_FEMALE = (
        (19, (1.1549, 0.0678)),
        (29, (1.1599, 0.0717)),
        (39, (1.1423, 0.0632)),
        (49, (1.1333, 0.0612)),
        (200, (1.1339, 0.0645)),
    )

    def required_sites(
        self, protocol: SkinfoldProtocol, sex: BiologicalSex
    ) -> tuple[SkinfoldSite, ...]:
        return self.REQUIRED_SITES[protocol][sex]

    def calculate_body_fat_percentage(
        self,
        protocol: SkinfoldProtocol,
        sex: BiologicalSex,
        age_years: int,
        folds_mm: dict[SkinfoldSite, float],
    ) -> float:
        if age_years <= 0:
            raise ValueError("Idade deve ser maior que zero.")

        sites = self.required_sites(protocol, sex)
        missing = [
            site.value for site in sites if not folds_mm.get(site) or folds_mm[site] <= 0
        ]
        if missing:
            raise ValueError(f"Informe as dobras cutaneas: {', '.join(missing)}.")

        total_mm = sum(folds_mm[site] for site in sites)

        if protocol == SkinfoldProtocol.POLLOCK_3:
            return self._siri(self._pollock_density(sex, total_mm, age_years, seven_site=False))
        if protocol == SkinfoldProtocol.POLLOCK_7:
            return self._siri(self._pollock_density(sex, total_mm, age_years, seven_site=True))
        if protocol == SkinfoldProtocol.DURNIN_WOMERSLEY:
            return self._siri(self._durnin_womersley_density(sex, total_mm, age_years))
        if protocol == SkinfoldProtocol.FAULKNER:
            return (0.153 * total_mm) + 5.783

        raise ValueError("Protocolo de dobras cutaneas nao suportado.")

    def reference_for(self, protocol: SkinfoldProtocol) -> str:
        key = self.REFERENCE_KEYS.get(protocol)
        return ClinicalValidationMatrix.summary_for(key) if key else protocol.value

    def build_trace(
        self,
        protocol: SkinfoldProtocol,
        sex: BiologicalSex,
        age_years: int,
        folds_mm: dict[SkinfoldSite, float],
        percentage: float,
    ) -> CalculationTrace:
        sites = self.required_sites(protocol, sex)
        folds_text = "; ".join(f"{site.value}: {folds_mm[site]:g} mm" for site in sites)
        formula = f"Percentual de gordura estimado por dobras cutaneas ({protocol.value})"
        details = (
            f"Sexo: {sex.value}. Idade: {age_years} anos. Dobras: {folds_text}. "
            f"Percentual de gordura estimado: {percentage:.1f}%."
        )
        return CalculationTrace(
            formula=formula,
            reference=self.reference_for(protocol),
            details=details,
        )

    def _siri(self, density: float) -> float:
        if density <= 0:
            raise ValueError("Densidade corporal calculada e invalida.")
        return (4.95 / density - 4.50) * 100

    def _pollock_density(
        self,
        sex: BiologicalSex,
        total_mm: float,
        age_years: int,
        seven_site: bool,
    ) -> float:
        if seven_site:
            if sex == BiologicalSex.MALE:
                return (
                    1.112
                    - (0.00043499 * total_mm)
                    + (0.00000055 * total_mm**2)
                    - (0.00028826 * age_years)
                )
            return (
                1.097
                - (0.00046971 * total_mm)
                + (0.00000056 * total_mm**2)
                - (0.00012828 * age_years)
            )
        if sex == BiologicalSex.MALE:
            return (
                1.10938
                - (0.0008267 * total_mm)
                + (0.0000016 * total_mm**2)
                - (0.0002574 * age_years)
            )
        return (
            1.0994921
            - (0.0009929 * total_mm)
            + (0.0000023 * total_mm**2)
            - (0.0001392 * age_years)
        )

    def _durnin_womersley_density(
        self, sex: BiologicalSex, total_mm: float, age_years: int
    ) -> float:
        table = self.DURNIN_MALE if sex == BiologicalSex.MALE else self.DURNIN_FEMALE
        constant, slope = table[-1][1]
        for max_age, coefficients in table:
            if age_years <= max_age:
                constant, slope = coefficients
                break
        return constant - (slope * math.log10(total_mm))
