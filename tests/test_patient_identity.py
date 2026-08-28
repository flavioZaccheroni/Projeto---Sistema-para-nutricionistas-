import unittest

from nutri_app.services.patient_identity import (
    digits_only,
    is_valid_cns,
    is_valid_cpf,
    normalize_cns,
    normalize_cpf,
)


class PatientIdentityTest(unittest.TestCase):
    def test_digits_only_remove_caracteres_nao_numericos(self) -> None:
        self.assertEqual(digits_only("529.982.247-25"), "52998224725")
        self.assertEqual(normalize_cpf("529.982.247-25"), "52998224725")
        self.assertEqual(normalize_cns("700 000 000 000005"), "700000000000005")

    def test_cpf_valido_e_aceito(self) -> None:
        self.assertTrue(is_valid_cpf("529.982.247-25"))
        self.assertTrue(is_valid_cpf("52998224725"))

    def test_cpf_com_digitos_verificadores_incorretos_e_rejeitado(self) -> None:
        self.assertFalse(is_valid_cpf("123.456.789-00"))

    def test_cpf_com_todos_digitos_iguais_e_rejeitado(self) -> None:
        self.assertFalse(is_valid_cpf("111.111.111-11"))

    def test_cpf_com_tamanho_invalido_e_rejeitado(self) -> None:
        self.assertFalse(is_valid_cpf("123456"))

    def test_cns_valido_e_aceito(self) -> None:
        self.assertTrue(is_valid_cns("700000000000005"))

    def test_cns_com_todos_digitos_iguais_e_rejeitado(self) -> None:
        self.assertFalse(is_valid_cns("111111111111111"))

    def test_cns_com_tamanho_invalido_e_rejeitado(self) -> None:
        self.assertFalse(is_valid_cns("12345"))


if __name__ == "__main__":
    unittest.main()
