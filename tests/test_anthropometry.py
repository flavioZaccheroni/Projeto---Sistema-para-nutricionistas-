import unittest

from nutri_app.services.anthropometry import AnthropometryService, BmiClassification


class AnthropometryServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = AnthropometryService()

    def test_calcula_imc_adulto(self) -> None:
        bmi = self.service.calculate_bmi(weight_kg=70, height_meters=1.75)

        self.assertAlmostEqual(bmi, 22.86, places=2)

    def test_classifica_baixo_peso_quando_imc_menor_que_18_5(self) -> None:
        self.assertEqual(
            self.service.classify_adult_bmi(18.4),
            BmiClassification.THINNESS,
        )

    def test_identifica_risco_por_perda_de_peso_maior_que_10_por_cento(self) -> None:
        loss = self.service.calculate_weight_loss_percentage(
            usual_weight_kg=80,
            current_weight_kg=70,
        )

        self.assertAlmostEqual(loss, 12.5, places=2)
        self.assertTrue(self.service.has_high_nutritional_risk_by_weight_loss(loss))

    def test_calcula_rcq_e_rcest(self) -> None:
        self.assertAlmostEqual(self.service.calculate_waist_hip_ratio(80, 100), 0.8)
        self.assertAlmostEqual(self.service.calculate_waist_height_ratio(80, 1.75), 0.46, places=2)


if __name__ == "__main__":
    unittest.main()
