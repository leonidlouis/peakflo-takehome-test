import unittest
import logging
import os
from unittest.mock import patch, mock_open
import main


class TestMainScript(unittest.TestCase):
    def setUp(self):
        # Clear handlers before every test
        for handler in logging.getLogger().handlers[:]:
            logging.getLogger().removeHandler(handler)
        logging.disable(logging.NOTSET)  # Re-enable logging

    @patch("argparse.ArgumentParser.parse_args")
    def test_parse_args(self, mock_parse_args):
        # Set up the mock behavior for parse_args
        mock_args = main.parse_args()
        mock_args.filepath = "test.csv"
        mock_args.log_level = "DEBUG"
        mock_args.config_filepath = "test_config.json"
        mock_parse_args.return_value = mock_args

        # Call the parse_args function and get the result
        args = main.parse_args()

        # Check if the returned arguments match the expected values
        self.assertEqual(args.filepath, "test.csv")
        self.assertEqual(args.log_level, "DEBUG")
        self.assertEqual(args.config_filepath, "test_config.json")

    def test_validate_csv_data_valid(self):
        # Valid journey data
        journey = ["line1", "line2", "2023-09-14T12:00:00"]
        valid_combinations = {"line1,line2"}

        # Ensure no exceptions are raised for valid data
        try:
            main.validate_csv_data(journey, valid_combinations)
        except Exception as e:
            self.fail(f"validate_csv_data raised an unexpected exception: {e}")

    def test_validate_csv_data_invalid_combination(self):
        # Invalid journey data with an invalid line combination
        journey = ["line1", "line3", "2023-09-14T12:00:00"]
        valid_combinations = {"line1,line2"}

        # Ensure a ValueError is raised for an invalid line combination
        with self.assertRaises(ValueError) as context:
            main.validate_csv_data(journey, valid_combinations)

        self.assertEqual(
            str(context.exception), "Invalid journey combination: line1 to line3"
        )

    def test_validate_csv_data_invalid_date_format(self):
        # Invalid journey data with an invalid date format
        journey = ["line1", "line2", "2023-09-14 12:00:00"]
        valid_combinations = {"line1,line2"}

        # Ensure a ValueError is raised for an invalid date format
        with self.assertRaises(ValueError) as context:
            main.validate_csv_data(journey, valid_combinations)

        self.assertEqual(
            str(context.exception), "Invalid 'date_time' format: 2023-09-14 12:00:00"
        )

    def test_read_csv_valid(self):
        # Valid CSV file with one valid journey
        file_path = "valid_test.csv"
        valid_line_combinations = {"line1,line2"}
        content = "from_line,to_line,date_time\nline1,line2,2023-09-14T12:00:00"

        # Create a temporary valid CSV file
        with open(file_path, "w") as file:
            file.write(content)

        # Ensure no exceptions are raised for a valid CSV file
        try:
            journeys = main.read_csv(file_path, valid_line_combinations)
        except Exception as e:
            self.fail(f"read_csv raised an unexpected exception: {e}")
        finally:
            # Clean up: Remove the temporary CSV file
            os.remove(file_path)

        # Ensure the journeys list contains the expected data
        self.assertEqual(len(journeys), 1)
        self.assertEqual(journeys[0], ["line1", "line2", "2023-09-14T12:00:00"])

    def test_read_csv_invalid_header(self):
        # CSV file with an invalid header
        file_path = "invalid_header_test.csv"
        valid_line_combinations = {"line1,line2"}
        content = "invalid1,invalid2,invalid3\nline1,line2,2023-09-14T12:00:00"

        # Create a temporary CSV file with an invalid header
        with open(file_path, "w") as file:
            file.write(content)

        # Ensure a ValueError is raised for an invalid CSV header
        with self.assertRaises(ValueError) as context:
            main.read_csv(file_path, valid_line_combinations)

        self.assertEqual(str(context.exception), "Unexpected CSV header format.")

        # Clean up: Remove the temporary CSV file
        os.remove(file_path)

    def test_read_csv_invalid_data(self):
        # CSV file with invalid journey data
        file_path = "invalid_data_test.csv"
        valid_line_combinations = {"line1,line2"}
        content = "from_line,to_line,date_time\nline1,line3,2023-09-14T12:00:00"

        # Create a temporary CSV file with invalid data
        with open(file_path, "w") as file:
            file.write(content)

        # Ensure a ValueError is raised for invalid journey data
        with self.assertRaises(ValueError) as context:
            main.read_csv(file_path, valid_line_combinations)

        self.assertEqual(
            str(context.exception), "Invalid journey combination: line1 to line3"
        )

        # Clean up: Remove the temporary CSV file
        os.remove(file_path)

    def test_read_csv_file_not_found(self):
        # Attempt to read a non-existent CSV file
        file_path = "non_existent.csv"
        valid_line_combinations = {"line1,line2"}

        # Ensure a FileNotFoundError is raised for a non-existent file
        with self.assertRaises(FileNotFoundError) as context:
            main.read_csv(file_path, valid_line_combinations)

    def test_calculate_user_total_fare_valid(self):
        config = {
            "peak_hours": {
                "monday": [["08:00", "10:00"], ["16:30", "19:00"]],
                "tuesday": [["08:00", "10:00"], ["16:30", "19:00"]],
                "wednesday": [["08:00", "10:00"], ["16:30", "19:00"]],
                "thursday": [["08:00", "10:00"], ["16:30", "19:00"]],
                "friday": [["08:00", "10:00"], ["16:30", "19:00"]],
                "saturday": [["10:00", "14:00"], ["18:00", "23:00"]],
                "sunday": [["18:00", "23:00"]],
            },
            "fare_chart": {
                "green,green": {"peak": 2, "non_peak": 1},
                "red,red": {"peak": 3, "non_peak": 2},
                "green,red": {"peak": 4, "non_peak": 3},
                "red,green": {"peak": 3, "non_peak": 2},
            },
            "cap_chart": {
                "green,green": {"daily": 8, "weekly": 55},
                "red,red": {"daily": 12, "weekly": 70},
                "green,red": {"daily": 15, "weekly": 90},
                "red,green": {"daily": 15, "weekly": 90},
            },
        }

        journeys = [
            ["green", "green", "2023-09-14T08:30:00"],  # peak hour
            ["green", "red", "2023-09-14T12:00:00"],  # non-peak hour
            ["red", "green", "2023-09-14T19:30:00"],  # non-peak hour
            ["red", "red", "2023-09-14T19:45:00"],  # non-peak hour
        ]

        expected_fare = (
            config["fare_chart"]["green,green"]["peak"]
            + config["fare_chart"]["green,red"]["non_peak"]
            + config["fare_chart"]["red,green"]["non_peak"]
            + config["fare_chart"]["red,red"]["non_peak"]
        )

        with patch.object(main.logging, "info"), patch.object(main.logging, "critical"):
            total_fare = main.calculate_user_total_fare(config, journeys)

        self.assertEqual(total_fare, expected_fare)

    def test_log_level_none(self):
        main.configure_log("NONE")
        with self.assertRaises(
            AssertionError
        ):  # Because if `logging` is properly disabled, calling self.assertLogs will throw an AssertionError
            with self.assertLogs() as cm:
                logging.critical("This log should not appear.")

    def test_invalid_log_level(self):
        with self.assertRaises(ValueError):
            main.configure_log("INVALID_LOG_LEVEL")

    def test_debug_log_file_creation(self):
        m = mock_open()
        with patch("builtins.open", m), patch("os.makedirs", return_value=None):
            main.configure_log("DEBUG")
            m.assert_called_once()  # Ensure that the log file was created

    def test_log_level_control(self):
        main.configure_log("WARNING")
        with self.assertLogs(level="WARNING") as cm:
            logging.debug("This debug log should not appear.")
            logging.warning("This warning log should appear.")
            logging.error("This error log should appear.")
        self.assertEqual(len(cm.records), 2)
        self.assertIn(
            "This warning log should appear.", [rec.message for rec in cm.records]
        )
        self.assertIn(
            "This error log should appear.", [rec.message for rec in cm.records]
        )


if __name__ == "__main__":
    unittest.main()
