import unittest

import pandas as pd

from modules.gsheets_db import DatabaseManager


class FailingSheets:
    def worksheet(self, title):
        raise RuntimeError("simulated Google Sheets API failure")


class DatabaseSmokeTests(unittest.TestCase):
    def test_auxiliary_sheet_failure_returns_empty_dataframe(self):
        db = DatabaseManager.__new__(DatabaseManager)
        db.spreadsheet_inventario = FailingSheets()
        db.is_connected_gsheets = True

        result = db.get_responsables()

        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(list(result.columns), ["nombre", "pin"])
        self.assertFalse(result.empty)

    def test_product_stock_is_numeric(self):
        db = DatabaseManager.__new__(DatabaseManager)
        db._sheet_dataframe = lambda title, headers: pd.DataFrame([
            {"ID": "BAT-1", "Stock_Actual": "0", "Stock_Minimo": "2"}
        ])

        result = db.get_productos()

        self.assertEqual(result.iloc[0]["Stock_Actual"], 0)
        self.assertEqual(result.iloc[0]["Stock_Minimo"], 2)


if __name__ == "__main__":
    unittest.main()