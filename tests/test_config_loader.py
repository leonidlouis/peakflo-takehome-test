import unittest
from unittest.mock import patch, mock_open
from config_loader import (
    ConfigLoader,
    InvalidStructureError,
    InvalidLineToLineCombinationError,
)
import json


class TestConfigLoader(unittest.TestCase):
    @patch(
        "builtins.open", mock_open(read_data=json.dumps({"valid_key": "valid_value"}))
    )
    @patch.object(ConfigLoader, "_validate_config")
    def test_load_config(self, mock_validate_config):
        # Create a ConfigLoader instance
        config_loader = ConfigLoader()

        # Call the load_config method
        config = config_loader.load_config()

        # Assertions
        self.assertEqual(
            config, {"valid_key": "valid_value"}
        )  # Ensure the config is returned correctly
        mock_validate_config.assert_called_once()  # Ensure _validate_config was called

    @patch("builtins.open", mock_open(read_data='{"valid_key": "valid_value"}'))
    def test_read_config_from_file_valid(self):
        # Create a ConfigLoader instance
        config_loader = ConfigLoader()

        # Call the _read_config_from_file method
        config = config_loader._read_config_from_file()

        # Assertions
        self.assertEqual(
            config, {"valid_key": "valid_value"}
        )  # Ensure the config is read correctly

    def test_validate_config_sample(self):
        # Sample config data
        sample_config = {
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

        # Create a ConfigLoader instance
        config_loader = ConfigLoader()

        # Call the _validate_config method with the sample config
        try:
            config_loader._validate_config(sample_config)
        except (InvalidStructureError, InvalidLineToLineCombinationError) as e:
            self.fail(f"Validation failed: {e}")

    def test_validate_config_invalid_structure(self):
        # Invalid structure: Missing 'peak_hours'
        invalid_config = {
            "fare_chart": {
                "green,green": {"peak": 2, "non_peak": 1},
                "red,red": {"peak": 3, "non_peak": 2},
            },
            "cap_chart": {
                "green,green": {"daily": 8, "weekly": 55},
                "red,red": {"daily": 12, "weekly": 70},
            },
        }

        # Create a ConfigLoader instance
        config_loader = ConfigLoader()

        # Call the _validate_config method with the invalid config
        with self.assertRaises(InvalidStructureError):
            config_loader._validate_config(invalid_config)

    def test_validate_config_invalid_peak_hours_structure(self):
        # Invalid 'peak_hours' structure: Missing day name
        invalid_config = {
            "peak_hours": {
                "monday": [["08:00", "10:00"], ["16:30", "19:00"]],
                "tuesday": [["08:00", "10:00"], ["16:30", "19:00"]],
                "wednesday": [["08:00", "10:00"], ["16:30", "19:00"]],
                "thursday": [["08:00", "10:00"], ["16:30", "19:00"]],
                "friday": [["08:00", "10:00"], ["16:30", "19:00"]],
                "saturday": [["10:00", "14:00"], ["18:00", "23:00"]],
                "sunday": [["18:00", "23:00"]],
                123: [["09:00", "12:00"]],
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

        # Create a ConfigLoader instance
        config_loader = ConfigLoader()

        # Call the _validate_config method with the invalid config
        with self.assertRaises(InvalidStructureError):
            config_loader._validate_config(invalid_config)

    def test_validate_config_missing_keys(self):
        # Missing 'fare_chart' key
        missing_fare_chart = {
            "peak_hours": {
                "monday": [["08:00", "10:00"]],
                "tuesday": [["08:00", "10:00"]],
            },
            "cap_chart": {
                "green,green": {"daily": 8, "weekly": 55},
            },
        }

        # Missing 'cap_chart' key
        missing_cap_chart = {
            "peak_hours": {
                "monday": [["08:00", "10:00"]],
                "tuesday": [["08:00", "10:00"]],
            },
            "fare_chart": {
                "green,green": {"peak": 2, "non_peak": 1},
            },
        }

        # Create a ConfigLoader instance
        config_loader = ConfigLoader()

        # Test missing 'fare_chart'
        with self.assertRaises(InvalidStructureError):
            config_loader._validate_config(missing_fare_chart)

        # Test missing 'cap_chart'
        with self.assertRaises(InvalidStructureError):
            config_loader._validate_config(missing_cap_chart)

    def test_validate_config_invalid_data_types_in_fare_chart(self):
        # Invalid data types for values in 'fare_chart'
        invalid_fare_chart = {
            "peak_hours": {
                "monday": [["08:00", "10:00"]],
                "tuesday": [["08:00", "10:00"]],
            },
            "fare_chart": {
                "green,green": {"peak": 2, "non_peak": "1"},  # 'non_peak' should be int
                "red,red": {"peak": 3, "non_peak": 2},
            },
            "cap_chart": {
                "green,green": {"daily": 8, "weekly": 55},
            },
        }

        # Create a ConfigLoader instance
        config_loader = ConfigLoader()

        # Test invalid data types in 'fare_chart'
        with self.assertRaises(InvalidStructureError):
            config_loader._validate_config(invalid_fare_chart)

    def test_validate_config_invalid_data_types_in_cap_chart(self):
        # Invalid data types for values in 'cap_chart'
        invalid_cap_chart = {
            "peak_hours": {
                "monday": [["08:00", "10:00"]],
                "tuesday": [["08:00", "10:00"]],
            },
            "fare_chart": {
                "green,green": {"peak": 2, "non_peak": 1},
            },
            "cap_chart": {
                "green,green": {"daily": 8, "weekly": "55"},  # 'weekly' should be int
            },
        }

        # Create a ConfigLoader instance
        config_loader = ConfigLoader()

        # Test invalid data types in 'cap_chart'
        with self.assertRaises(InvalidStructureError):
            config_loader._validate_config(invalid_cap_chart)

    def test_validate_config_time_overlap(self):
        # Overlapping time slots on Monday
        overlapping_time = {
            "peak_hours": {
                "monday": [["08:00", "10:00"], ["09:30", "11:00"]],
            },
            "fare_chart": {
                "green,green": {"peak": 2, "non_peak": 1},
            },
            "cap_chart": {
                "green,green": {"daily": 8, "weekly": 55},
            },
        }

        # Create a ConfigLoader instance
        config_loader = ConfigLoader()

        # Test overlapping time slots
        with self.assertRaises(InvalidStructureError):
            config_loader._validate_config(overlapping_time)

    def test_validate_config_missing_peak_hours_and_fare_chart(self):
        # Missing both 'peak_hours' and 'fare_chart'
        missing_keys_config = {
            "cap_chart": {
                "green,green": {"daily": 8, "weekly": 55},
            }
        }

        # Create a ConfigLoader instance
        config_loader = ConfigLoader()

        # Test missing 'peak_hours' and 'fare_chart'
        with self.assertRaises(InvalidStructureError):
            config_loader._validate_config(missing_keys_config)

    def test_validate_config_missing_peak_hours(self):
        # Missing 'peak_hours'
        missing_peak_hours_config = {
            "fare_chart": {
                "green,green": {"peak": 2, "non_peak": 1},
            },
            "cap_chart": {
                "green,green": {"daily": 8, "weekly": 55},
            },
        }

        # Create a ConfigLoader instance
        config_loader = ConfigLoader()

        # Test missing 'peak_hours'
        with self.assertRaises(InvalidStructureError):
            config_loader._validate_config(missing_peak_hours_config)

    def test_validate_config_invalid_time_format(self):
        # Invalid time format: Incorrect separator
        invalid_time_format_config = {
            "peak_hours": {
                "monday": [["08-00", "10:00"]],
            },
            "fare_chart": {
                "green,green": {"peak": 2, "non_peak": 1},
            },
            "cap_chart": {
                "green,green": {"daily": 8, "weekly": 55},
            },
        }

        # Create a ConfigLoader instance
        config_loader = ConfigLoader()

        # Test invalid time format
        with self.assertRaises(InvalidStructureError):
            config_loader._validate_config(invalid_time_format_config)

    def test_validate_time_format_edge_cases(self):
        valid_edge_cases = ["00:00", "23:59", "01:30", "12:01"]
        config_loader = ConfigLoader()

        for time_str in valid_edge_cases:
            try:
                config_loader._validate_time_format(time_str)
            except InvalidStructureError:
                self.fail(f"Validation failed for valid time format: {time_str}")

    def test_validate_invalid_characters_in_keys(self):
        invalid_characters = {
            "fare_chart": {
                "green,green$": {"peak": 2, "non_peak": 1},
                "red_red": {"peak": 3, "non_peak": 2},
            },
            "cap_chart": {
                "green,green!": {"daily": 8, "weekly": 55},
                "red-red": {"daily": 12, "weekly": 70},
            },
        }
        config_loader = ConfigLoader()

        for key, config_data in invalid_characters.items():
            with self.assertRaises(InvalidStructureError):
                config_loader._validate_config({key: config_data})

    def test_validate_multiple_errors(self):
        multiple_errors_config = {
            "fare_chart": {
                "green,green$": {"peak": 2, "non_peak": "1"},
                "red_red": {"peak": 3, "non_peak": "two"},
            },
            "cap_chart": {
                "green,green!": {"daily": 8, "weekly": "55"},
                "red-red": {"daily": 12, "weekly": "seventy"},
            },
        }
        config_loader = ConfigLoader()

        with self.assertRaises(InvalidStructureError):
            config_loader._validate_config(multiple_errors_config)

    def test_validate_invalid_values_in_time_slots(self):
        invalid_time_slots = {
            "peak_hours": {
                "monday": [["08:00", "invalid"], ["10:15", "12:00"]],
            },
            "fare_chart": {
                "green,green": {"peak": 2, "non_peak": 1},
            },
            "cap_chart": {
                "green,green": {"daily": 8, "weekly": 55},
            },
        }
        config_loader = ConfigLoader()

        with self.assertRaises(InvalidStructureError):
            config_loader._validate_config(invalid_time_slots)

    def test_validate_missing_values_in_time_slots(self):
        missing_values_time_slots = {
            "peak_hours": {
                "monday": [["08:00", "10:00"], ["10:15"]],
            },
            "fare_chart": {
                "green,green": {"peak": 2, "non_peak": 1},
            },
            "cap_chart": {
                "green,green": {"daily": 8, "weekly": 55},
            },
        }
        config_loader = ConfigLoader()

        with self.assertRaises(InvalidStructureError):
            config_loader._validate_config(missing_values_time_slots)

    def test_validate_invalid_values_in_fare_and_cap_charts(self):
        invalid_values_charts = {
            "fare_chart": {
                "green,green": {"peak": 2, "non_peak": "invalid"},
                "red_red": {"peak": 3, "non_peak": -1},
            },
            "cap_chart": {
                "green,green": {"daily": 8, "weekly": "invalid"},
                "red-red": {"daily": -12, "weekly": 70},
            },
        }
        config_loader = ConfigLoader()

        with self.assertRaises(InvalidStructureError):
            config_loader._validate_config(invalid_values_charts)

    def test_invalid_line_to_line_combinations(self):
        missing_combination_config = {
            "peak_hours": {
                "monday": [["08:00", "10:00"]],
            },
            "fare_chart": {
                "green,green": {"peak": 2, "non_peak": 1},
            },
            "cap_chart": {
                "green,green": {"daily": 8, "weekly": 55},
                "red,red": {"daily": 12, "weekly": 70},
            },
        }

        config_loader = ConfigLoader()

        # Test missing combination in fare_chart
        with self.assertRaises(InvalidLineToLineCombinationError):
            config_loader._validate_config(missing_combination_config)

        missing_combination_config = {
            "peak_hours": {
                "monday": [["08:00", "10:00"]],
            },
            "fare_chart": {
                "green,green": {"peak": 2, "non_peak": 1},
                "red,red": {"peak": 3, "non_peak": 2},
            },
            "cap_chart": {
                "green,green": {"daily": 8, "weekly": 55},
            },
        }

        # Test missing combination in cap_chart
        with self.assertRaises(InvalidLineToLineCombinationError):
            config_loader._validate_config(missing_combination_config)

    def test_validate_chart_structure(self):
        config_loader = ConfigLoader()

        # Valid fare_chart structure
        valid_fare_chart = {
            "green,green": {"peak": 2, "non_peak": 1},
            "red,red": {"peak": 3, "non_peak": 2},
        }
        config_data = {
            "fare_chart": valid_fare_chart,
            "peak_hours": {},
        }
        config_loader._validate_chart_structure(
            config_data, "fare_chart", {"peak", "non_peak"}
        )

        # Missing keys in fare_chart
        invalid_fare_chart_missing_keys = {
            "green,green": {"peak": 2},
            "red,red": {"peak": 3, "non_peak": 2},
        }
        config_data["fare_chart"] = invalid_fare_chart_missing_keys
        with self.assertRaises(InvalidStructureError):
            config_loader._validate_chart_structure(
                config_data, "fare_chart", {"peak", "non_peak"}
            )

        # Extra keys in fare_chart
        invalid_fare_chart_extra_keys = {
            "green,green": {"peak": 2, "non_peak": 1, "extra_key": 42},
            "red,red": {"peak": 3, "non_peak": 2},
        }
        config_data["fare_chart"] = invalid_fare_chart_extra_keys
        with self.assertRaises(InvalidStructureError):
            config_loader._validate_chart_structure(
                config_data, "fare_chart", {"peak", "non_peak"}
            )

        # Empty fare_chart
        empty_fare_chart = {}
        config_data["fare_chart"] = empty_fare_chart
        with self.assertRaises(InvalidStructureError):
            config_loader._validate_chart_structure(
                config_data, "fare_chart", {"peak", "non_peak"}
            )

        # Missing fare_chart
        del config_data["fare_chart"]
        with self.assertRaises(InvalidStructureError):
            config_loader._validate_chart_structure(
                config_data, "fare_chart", {"peak", "non_peak"}
            )


if __name__ == "__main__":
    unittest.main()
