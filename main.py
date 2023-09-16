import argparse
import csv
import logging
import os
import sys
from datetime import datetime

from config_loader import ConfigLoader
from constants import DATE_FORMAT, LOG_FORMAT
from fare_system import PeakHoursChecker, UserJourneyTracker, FareCalculator, FareCap
from settings import BASE_DIR
from utils import resolve_path

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
        absolute_path = resolve_path(file_path)
        with open(absolute_path, mode="r") as file:
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
        default=os.path.join(BASE_DIR, "data/target.csv"),
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
        default=os.path.join(BASE_DIR, "config.json"),
        help="Path to the configuration file",
    )
    parser.add_argument(
        "--write-log",
        action="store_true",
        help="If set, log output to a file. Otherwise, logs are output to the console.",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=os.path.join(BASE_DIR, "logs"),
        help="Directory to save the log file. Default is 'logs' directory.",
    )

    args = parser.parse_args()

    # Check if the script was run without any arguments, then activate interactive mode
    if len(sys.argv) == 1:
        # Displaying only the filename for better user experience
        default_csv_display = os.path.basename(args.filepath)
        default_config_display = os.path.basename(args.config_filepath)
        default_logdir_display = os.path.basename(args.log_dir)

        print("Interactive mode activated. Please input the required information.")
        input_filepath = input(
            f"Path to the input CSV file (default: {default_csv_display}): "
        ).strip()
        args.filepath = (
            resolve_path(input_filepath) if input_filepath else args.filepath
        )

        input_config_filepath = input(
            f"Path to the configuration file (default: {default_config_display}): "
        ).strip()
        args.config_filepath = (
            resolve_path(input_config_filepath)
            if input_config_filepath
            else args.config_filepath
        )

        args.log_level = (
            input(f"Set the logging level (default: {args.log_level}): ")
            or args.log_level
        )
        args.write_log = (
            True
            if input(
                f"If set, log output to a file (True/False) (default: {args.write_log}): "
            ).lower()
            == "true"
            else args.write_log
        )

        if args.write_log is True:
            input_log_dir = input(
                f"Directory to save the log file (default: {default_logdir_display}): "
            ).strip()
            args.log_dir = (
                resolve_path(input_log_dir) if input_log_dir else args.log_dir
            )

    return args


def configure_log(log_level, write_log=False, log_dir="logs"):
    """Configure logging for application, level and behaviour is modifiable by user args"""
    if log_level == "NONE":
        logging.disable(logging.CRITICAL + 1)  # Disable all logging
        return

    numeric_log_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_log_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Configure logger
    logger = logging.getLogger()
    logger.setLevel(numeric_log_level)

    # If write-log flag is set, add file handler to write logs to a file
    if write_log:
        log_folder = resolve_path(log_dir)

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
    configure_log(args.log_level, args.write_log, args.log_dir)

    try:
        config_loader = ConfigLoader(args.config_filepath)
        config = config_loader.load_config()

        valid_line_combinations = set(config["fare_chart"].keys())
        user_journey = read_csv(args.filepath, valid_line_combinations)
        total_fare = calculate_user_total_fare(config, user_journey)
        print(f"Total Fare: ${total_fare}")
    except Exception as e:
        logging.critical(f"An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
