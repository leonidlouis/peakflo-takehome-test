import unittest
import subprocess
import sys
import os

current_directory = os.path.dirname(os.path.abspath(__file__))

parent_directory = os.path.join(current_directory, "..")
sys.path.append(parent_directory)


class TestIntegration(unittest.TestCase):
    test_cases = [
        {
            "name": "simulate 2 week cap restart",
            "filepath": "tests/data/simulate_2_week_cap_restart_115.csv",
            "expected_result": "Total Fare: $115",
        },
        {
            "name": "simulate 2 day cap restart",
            "filepath": "tests/data/simulate_2_day_cap_restart_13.csv",
            "expected_result": "Total Fare: $13",
        },
        {
            "name": "simulate multiple day cap restart",
            "filepath": "tests/data/simulate_multiple_day_cap_restart_298.csv",
            "expected_result": "Total Fare: $298",
        },
        {
            "name": "invalid filepath",
            "filepath": "asdasd.csv",
            "expected_result_contains": "An error occurred:",
        },
    ]

    def run_script_and_assert(
        self, command, expected_result=None, expected_result_contains=None
    ):
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, cwd=parent_directory
            )
        except subprocess.CalledProcessError as e:
            self.fail(f"Script execution failed with error: {e}")

        if expected_result:
            self.assertEqual(result.stdout.strip(), expected_result)
        elif expected_result_contains:
            self.assertIn(expected_result_contains, result.stderr)

    def test_run_main_script(self):
        for test_case in self.test_cases:
            with self.subTest(test_case["name"]):
                command = [
                    "python3",
                    "main.py",
                    "--config-filepath=tests/data/test_config.json",
                    f"--filepath={test_case['filepath']}",
                    "--log-level=CRITICAL",
                ]
                self.run_script_and_assert(
                    command,
                    expected_result=test_case.get("expected_result"),
                    expected_result_contains=test_case.get("expected_result_contains"),
                )


if __name__ == "__main__":
    unittest.main()
