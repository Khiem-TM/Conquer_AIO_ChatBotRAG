from __future__ import annotations

import unittest

from app.shared.configs.settings import Settings


class SettingsTestCase(unittest.TestCase):
    def test_parse_cors_json(self) -> None:
        cfg = Settings(cors_origins='["http://localhost:3000","http://localhost:5173"]')
        self.assertEqual(cfg.cors_origins, ['http://localhost:3000', 'http://localhost:5173'])

    def test_invalid_weight_sum_fails(self) -> None:
        with self.assertRaises(ValueError):
            Settings(retrieval_keyword_weight=0.6, retrieval_vector_weight=0.5)


if __name__ == '__main__':
    unittest.main()
