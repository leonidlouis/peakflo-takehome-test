import unittest
import os
from unittest.mock import patch
import main


class TestMainScript(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
