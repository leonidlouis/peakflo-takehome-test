import csv
import os
import argparse
import logging
import subprocess
import inspect
from datetime import datetime
from config_loader import ConfigLoader
from constants import DATE_FORMAT, LOG_FORMAT
from fare_system import PeakHoursChecker, UserJourneyTracker, FareCalculator, FareCap

# Setting up logging
logging.basicConfig(level=logging.CRITICAL, format=LOG_FORMAT)


def validate_csv_data(journey, valid_combinations):
    from_line, to_line, date_time = journey

    if f"{from_line.lower()},{to_line.lower()}" not in valid_combinations:
        raise ValueError(f"Invalid journey combination: {from_line} to {to_line}")

    try:
        datetime.strptime(date_time, DATE_FORMAT)
    except ValueError:
        raise ValueError(f"Invalid 'date_time' format: {date_time}")


def read_csv(file_path, valid_line_combinations):
    """Read the input CSV file and return the list of journeys."""
    try:
        logging.info(f"Attempting to read CSV from {file_path}.")
        with open(file_path, mode="r") as file:
            csv_reader = csv.reader(file)
            header = next(csv_reader)  # Extract header

            if header != ["from_line", "to_line", "date_time"]:
                logging.critical("Unexpected CSV header format.")
                raise ValueError("Unexpected CSV header format.")

            journeys = list(csv_reader)
            for journey in journeys:
                validate_csv_data(journey, valid_line_combinations)  # Validate each row
            logging.info(
                f"Successfully read and validated {len(journeys)} journeys from {file_path}."
            )
            return journeys
    except FileNotFoundError:
        logging.critical(f"CSV file {file_path} not found.")
        raise
    except csv.Error as e:
        logging.critical(
            f"Error reading CSV file {file_path} at line {csv_reader.line_num}: {e}"
        )
        raise


def calculate_user_total_fare(config, journeys):
    """Process each journey from the CSV and calculate the total fare."""
    logging.info("Starting fare calculation for the given user journeys.")

    peak_hours_checker = PeakHoursChecker(config["peak_hours"])
    fare_calculator = FareCalculator(peak_hours_checker, config["fare_chart"])
    fare_cap = FareCap(config["cap_chart"])
    user_tracker = UserJourneyTracker(fare_calculator, fare_cap)
    total_fare = 0

    # Sort journey from start -> end
    journeys.sort(key=lambda x: datetime.strptime(x[2], DATE_FORMAT))

    for journey in journeys:
        from_line, to_line, date_time = journey
        from_line = from_line.lower()
        to_line = to_line.lower()
        fare_to_charge = user_tracker.add_journey(from_line, to_line, date_time)

        total_fare += fare_to_charge

    logging.info(f"Total Fare for {len(journeys)} journeys: ${total_fare}.")
    return total_fare


def parse_args():
    """Parse application user-inserted-arguments."""
    parser = argparse.ArgumentParser(
        description="Calculate fare from a given CSV file."
    )
    parser.add_argument(
        "--filepath",
        type=str,
        default="data/target.csv",
        help="Path to the input CSV file",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="CRITICAL",
        choices=["DEBUG", "INFO", "NONE", "CRITICAL"],
        help="Set the logging level",
    )
    parser.add_argument(
        "--config-filepath",
        type=str,
        default="config.json",
        help="Path to the configuration file",
    )
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    return parser.parse_args()


def configure_log(log_level):
    """Configure logging for application, level and behaviour is modifiable by user args"""
    if log_level == "NONE":
        logging.disable(logging.CRITICAL + 1)  # Disable all logging
        return

    numeric_log_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_log_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Get the directory of the calling script (your test script)
    caller_dir = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe()))
    )

    # Configure logger
    logger = logging.getLogger()
    logger.setLevel(numeric_log_level)

    # If log level is DEBUG, add file handler to write logs to a file
    if log_level.upper() == "DEBUG":
        log_folder = os.path.join(
            caller_dir, "logs"
        )  # Create the log folder in the caller's directory
        os.makedirs(log_folder, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(
            f"{log_folder}/app_debug_{timestamp}.log"
        )  # Save logs with a timestamp

        file_formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)


def main():
    """Main application logic."""
    args = parse_args()
    configure_log(args.log_level)

    if not args.skip_tests:
        test_result = subprocess.run(
            ["python3", "-m", "unittest", "discover", "tests"],
            capture_output=True,
            text=True,
        )

        if test_result.returncode != 0:
            logging.critical(
                "Tests failed. Please fix the issues before running the main logic."
            )
            captured_output = (
                test_result.stdout if test_result.stdout else test_result.stderr
            )
            logging.critical(f"Test output:\n{captured_output}")
            exit(1)

    try:
        config_loader = ConfigLoader(args.config_filepath)
        config = config_loader.load_config()

        valid_line_combinations = set(config["fare_chart"].keys())
        user_journey = read_csv(args.filepath, valid_line_combinations)
        total_fare = calculate_user_total_fare(config, user_journey)
        print(f"Total Fare: ${total_fare}")
    except Exception as e:
        logging.critical(f"An error occurred: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
