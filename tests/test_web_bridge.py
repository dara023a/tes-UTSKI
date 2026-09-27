import unittest

from app.watermark import CapacityError
from web_bridge import _user_error


class TestBridgeErrors(unittest.TestCase):
    def test_capacity_error_keeps_actionable_engine_counts(self):
        engine_message = (
            "Watermark membutuhkan 155236 bit, tetapi gambar hanya menyediakan "
            "24576 blok 8x8 yang tersedia untuk embedding."
        )

        response = _user_error(CapacityError(engine_message))

        self.assertEqual(response["type"], "CapacityError")
        self.assertIn("155236 bit", response["error"])
        self.assertIn("24576 blok", response["error"])


if __name__ == "__main__":
    unittest.main()
