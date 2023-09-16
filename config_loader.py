import json
import logging
from datetime import datetime
from constants import TIME_FORMAT
from utils import resolve_path


class ConfigError(Exception):
    """Base class for all configuration-related exceptions."""

    pass


class InvalidStructureError(ConfigError):
    """Raised when the config structure is invalid."""

    pass


class MissingKeyError(ConfigError):
    """Raised when a required key is missing in the config."""

    pass


class InvalidLineToLineCombinationError(ConfigError):
    """Raised when a line combination is missing in either fare_chart or cap_chart"""

    pass


class ConfigLoader:
    def __init__(self, config_path=None):
        # Default to "config.json" in the BASE_DIR if not provided
        self.config_path = config_path or resolve_path("config.json")

    def load_config(self):
        """Load and validate the configuration."""
        logging.info(f"Loading configuration from {self.config_path}.")
        config = self._read_config_from_file()
        self._validate_config(config)
        logging.info("Configuration successfully loaded and validated.")
        return config

    def _read_config_from_file(self):
        """Read the configuration from a JSON file."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logging.exception(f"Config file {self.config_path} not found.")
            raise ConfigError("Configuration file is missing.")
        except json.JSONDecodeError:
            logging.exception(
                "Error decoding config file. Please check the file format."
            )
            raise ConfigError("Configuration file format is invalid.")

    def _validate_key_structure(self, data, expected_keys, message):
        """Utility method to validate keys in dictionaries."""
        if set(data.keys()) != expected_keys:
            missing_keys = expected_keys - set(data.keys())
            extra_keys = set(data.keys()) - expected_keys
            errors = []
            if missing_keys:
                errors.append(f"Missing keys: {', '.join(missing_keys)}")
            if extra_keys:
                errors.append(f"Unexpected keys: {', '.join(extra_keys)}")
            raise InvalidStructureError(message + " " + " ".join(errors))

    def _validate_time_format(self, time_str):
        """Validates the time format HH:MM."""
        try:
            datetime.strptime(time_str, TIME_FORMAT)
        except ValueError:
            raise InvalidStructureError(
                f"Invalid time format: {time_str}. Expected format is HH:MM."
            )

    def _validate_config(self, config):
        """Validate the configuration structure and content."""
        try:
            # Check the top-level keys
            required_keys = {"fare_chart", "peak_hours", "cap_chart"}
            self._validate_key_structure(
                config, required_keys, "Top level config error."
            )

            # Validate peak_hours
            if not all(
                isinstance(day, str) and isinstance(hours, list)
                for day, hours in config["peak_hours"].items()
            ):
                raise InvalidStructureError(
                    "Invalid structure for peak_hours in config."
                )

            # Further validate the time format in peak_hours
            for day, time_slots in config["peak_hours"].items():
                prev_end_time_obj = None  # track the end time of the previous time slot

                for time_slot in time_slots:
                    if len(time_slot) != 2:
                        raise InvalidStructureError(
                            f"Expected 2 time entries for each slot in {day}, got {len(time_slot)}."
                        )

                    start_time, end_time = time_slot
                    self._validate_time_format(start_time)
                    self._validate_time_format(end_time)

                    start_time_obj = datetime.strptime(start_time, TIME_FORMAT).time()
                    end_time_obj = datetime.strptime(end_time, TIME_FORMAT).time()

                    if start_time_obj >= end_time_obj:
                        raise InvalidStructureError(
                            f"Invalid time range in {day}. Start time {start_time} should be before end time {end_time}."
                        )

                    # Check for overlaps with the previous time slot
                    if prev_end_time_obj and start_time_obj < prev_end_time_obj:
                        raise InvalidStructureError(
                            f"Overlapping time range detected in {day} for {start_time} and {end_time}."
                        )

                    prev_end_time_obj = end_time_obj  # update the previous end time

            # Validate fare_chart and cap_chart with a common pattern
            for key, validation_keys in {
                "fare_chart": {"peak", "non_peak"},
                "cap_chart": {"daily", "weekly"},
            }.items():
                self._validate_chart_structure(config, key, validation_keys)

            # Validate combinations in cap_chart and fare_chart
            fare_keys = set(config["fare_chart"].keys())
            cap_keys = set(config["cap_chart"].keys())

            if fare_keys != cap_keys:
                missing_in_fare = cap_keys - fare_keys
                missing_in_cap = fare_keys - cap_keys
                errors = []
                if missing_in_fare:
                    errors.append(
                        f"Combinations {', '.join(missing_in_fare)} found in cap_chart but missing in fare_chart."
                    )
                if missing_in_cap:
                    errors.append(
                        f"Combinations {', '.join(missing_in_cap)} found in fare_chart but missing in cap_chart."
                    )
                raise InvalidLineToLineCombinationError(" ".join(errors))
        except InvalidStructureError as e:
            logging.exception("Invalid structure detected during config validation.")
            raise
        except InvalidLineToLineCombinationError as e:
            logging.exception(
                "Invalid line-to-line combination detected during config validation."
            )
            raise
        except (
            Exception
        ) as e:  # This will catch any unexpected errors during validation
            logging.exception("An unexpected error occurred during config validation.")
            raise

    def _validate_chart_structure(self, config_data, chart_key, validation_keys):
        chart = config_data.get(chart_key)
        if not chart:
            raise InvalidStructureError(f"'{chart_key}' cannot be empty.")

        for key, value in chart.items():
            if not set(value.keys()) == validation_keys:
                missing_keys = validation_keys - set(value.keys())
                extra_keys = set(value.keys()) - validation_keys
                errors = []
                if missing_keys:
                    errors.append(
                        f"Missing keys in {chart_key} for {key}: {', '.join(missing_keys)}"
                    )
                if extra_keys:
                    errors.append(
                        f"Unexpected keys in {chart_key} for {key}: {', '.join(extra_keys)}"
                    )
                raise InvalidStructureError("; ".join(errors))

            if not all(isinstance(v, (int, float)) for v in value.values()):
                raise InvalidStructureError(
                    f"Invalid values in {chart_key} for {key}. Values must be integers or floats."
                )
