import unittest
from datetime import date, datetime

from nutri_app.ui.date_format import format_date, format_datetime, parse_date, parse_datetime


class DateFormatTest(unittest.TestCase):
    def test_formata_datas_no_padrao_brasileiro(self) -> None:
        self.assertEqual(format_date(date(2026, 8, 12)), "12/08/2026")
        self.assertEqual(format_datetime(datetime(2026, 8, 12, 14, 30)), "12/08/2026 14:30")

    def test_parse_mantem_compatibilidade_com_formatos_antigos(self) -> None:
        self.assertEqual(parse_date("12/08/2026"), date(2026, 8, 12))
        self.assertEqual(parse_date("12-08-2026"), date(2026, 8, 12))
        self.assertEqual(parse_datetime("12/08/2026 14:30"), datetime(2026, 8, 12, 14, 30))


if __name__ == "__main__":
    unittest.main()
