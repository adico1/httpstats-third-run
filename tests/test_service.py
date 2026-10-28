from pathlib import Path
import unittest
from word_frequency_checks import verify


class ServiceTests(unittest.TestCase):
    def test_http_contract(self):
        cases = verify(Path(__file__).resolve().parents[1] / 'server.py')
        self.assertEqual(len(cases), 63)
        for case in cases:
            with self.subTest(case=case['case']):
                self.assertTrue(case['passed'], case)


if __name__ == '__main__':
    unittest.main()
