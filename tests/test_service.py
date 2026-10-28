from pathlib import Path
import unittest
from history_checks import verify, verify_documentation


class ServiceTests(unittest.TestCase):
    def test_http_contract(self):
        cases = verify(Path(__file__).resolve().parents[1] / 'server.py')
        cases += verify_documentation(Path(__file__).resolve().parents[1] / 'server.py',
                                      Path(__file__).resolve().parents[1] / 'README.md')
        self.assertEqual(len(cases), 122)
        for case in cases:
            with self.subTest(case=case['case']):
                self.assertTrue(case['passed'], case)


if __name__ == '__main__':
    unittest.main()
