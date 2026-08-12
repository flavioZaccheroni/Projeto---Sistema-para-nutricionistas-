import unittest

from nutri_app.services.clinical_validation import ClinicalValidationMatrix


class ClinicalValidationMatrixTest(unittest.TestCase):
    def test_retorna_resumo_com_limites_e_revisao_profissional(self) -> None:
        summary = ClinicalValidationMatrix.summary_for("GLIM")

        self.assertIn("Referencia", summary)
        self.assertIn("criterio fenotipico", summary)
        self.assertIn("nutricionista", summary)

    def test_rejeita_referencia_nao_cadastrada(self) -> None:
        with self.assertRaises(ValueError):
            ClinicalValidationMatrix.summary_for("PROTOCOLO-X")


if __name__ == "__main__":
    unittest.main()
