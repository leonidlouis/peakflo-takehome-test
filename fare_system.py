import logging
from collections import defaultdict
from datetime import datetime, timedelta
from constants import DATE_FORMAT, TIME_FORMAT


# Setting up logging for the module
logger = logging.getLogger(__name__)

class PeakHoursChecker:
    """Check if a given datetime is during peak hours."""
    
    def __init__(self, peak_hours_config):
        self.peak_hours = peak_hours_config

    def is_peak(self, date_time):
        dt_obj = datetime.strptime(date_time, DATE_FORMAT)
        weekday = dt_obj.strftime('%A').lower()
        time_periods = self.peak_hours.get(weekday, [])
        
        for start, end in time_periods:
            if start <= dt_obj.strftime(TIME_FORMAT) <= end:
                logger.debug(f"{date_time} falls under peak hours.")
                return True

        logger.debug(f"{date_time} does not fall under peak hours.")
        return False


class FareCalculator:
    """Calculate the base fare based on journey details."""

    def __init__(self, peak_hours_checker, fare_chart_config):
        self.peak_hours_checker = peak_hours_checker
        self._fare_chart = fare_chart_config

    def get_base_fare(self, from_line, to_line, date_time):
        line_key = f"{from_line},{to_line}"
        fare_type = "peak" if self.peak_hours_checker.is_peak(date_time) else "non_peak"
        fare_value = self._fare_chart[line_key][fare_type]
        logger.debug(f"Base fare from {from_line} to {to_line} during {fare_type} time: ${fare_value}.")
        return fare_value

class FareCap:
    """Handle fare caps based on daily and weekly limits."""

    def __init__(self, cap_chart_config):
        self._cap_chart = cap_chart_config

    def apply_daily_cap(self, from_line, to_line, accumulated_daily_fare):
        cap = self._cap_chart[f"{from_line},{to_line}"]['daily']
        logger.debug(f"Applying daily cap of ${cap} for {from_line} to {to_line}.")
        return min(accumulated_daily_fare, cap)

    def apply_weekly_cap(self, from_line, to_line, accumulated_weekly_fare):
        cap = self._cap_chart[f"{from_line},{to_line}"]['weekly']
        logger.debug(f"Applying weekly cap of ${cap} for {from_line} to {to_line}.")
        return min(accumulated_weekly_fare, cap)


class UserJourneyTracker:
    """Track user journeys and calculate fares."""

    def __init__(self, fare_calculator, fare_cap):
        self.fare_calculator = fare_calculator
        self.fare_cap = fare_cap
        self._daily_fares = defaultdict(int)
        self._weekly_fares = defaultdict(int)
        self._last_journey_date = None
        self._week_start_date = None

    def _reset_daily_fares(self):
        for key in self._daily_fares:
            self._daily_fares[key] = 0

    def _reset_weekly_fares(self):
        for key in self._weekly_fares:
            self._weekly_fares[key] = 0

    def _reset_fares_if_needed(self, current_date):
        # Check if a new week has started
        if self._week_start_date is None or (current_date - self._week_start_date) >= timedelta(days=7):
            logger.debug(f"Resetting fares for the week starting {self._week_start_date}.")
            self._reset_weekly_fares()
            self._week_start_date = current_date

        # Check if a new day has begun
        if self._last_journey_date is not None and self._last_journey_date != current_date:
            logger.debug(f"Resetting daily fares for {self._last_journey_date}.")
            self._reset_daily_fares()

        self._last_journey_date = current_date

    def add_journey(self, from_line, to_line, date_time):
        logger.debug(f"=================================== Start Add New Journey Entry")
        journey_date = datetime.strptime(date_time, DATE_FORMAT).date()
        self._reset_fares_if_needed(journey_date)

        # Calculate base fare
        base_fare = self.fare_calculator.get_base_fare(from_line, to_line, date_time)

        # Calculate accumulated fares with the current journey
        logger.debug(f"Prev accumulated daily fare for journey from {from_line} to {to_line} is ${self._daily_fares[(from_line, to_line)]}.")
        logger.debug(f"Prev accumulated weekly fare for journey from {from_line} to {to_line} is ${self._weekly_fares[(from_line, to_line)]}.")
        accumulated_daily_fare = self._daily_fares[(from_line, to_line)] + base_fare
        accumulated_weekly_fare = self._weekly_fares[(from_line, to_line)] + base_fare

        # Apply caps
        capped_daily_fare = self.fare_cap.apply_daily_cap(from_line, to_line, accumulated_daily_fare)
        capped_weekly_fare = self.fare_cap.apply_weekly_cap(from_line, to_line, accumulated_weekly_fare)

        # Determine the fare to charge for this journey
        fare_to_charge = min(
            base_fare,
            capped_daily_fare - self._daily_fares[(from_line, to_line)],
            capped_weekly_fare - self._weekly_fares[(from_line, to_line)]
        )

        # Update accumulated fares
        self._daily_fares[(from_line, to_line)] += fare_to_charge
        self._weekly_fares[(from_line, to_line)] += fare_to_charge

        logger.debug(f"Accumulated daily fare for journey from {from_line} to {to_line} is ${self._daily_fares[(from_line, to_line)]}.")
        logger.debug(f"Accumulated weekly fare for journey from {from_line} to {to_line} is ${self._weekly_fares[(from_line, to_line)]}.")
        logger.debug(f"Fare to charge for journey from {from_line} to {to_line} is ${fare_to_charge}.")
        logger.debug(f"=================================== Finish New Journey Entry")

        return fare_to_charge
    