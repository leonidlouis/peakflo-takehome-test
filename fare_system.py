from datetime import datetime, timedelta

class PeakHours:
    _weekdays = [('08:00', '10:00'), ('16:30', '19:00')]
    _saturdays = [('10:00', '14:00'), ('18:00', '23:00')]
    _sundays = [('18:00', '23:00')]

    @classmethod
    def is_peak(cls, date_time):
        dt_obj = datetime.strptime(date_time, "%Y-%m-%dT%H:%M:%S")
        weekday = dt_obj.weekday()

        if 0 <= weekday < 5:  # Monday to Friday
            time_periods = cls._weekdays
        elif weekday == 5:  # Saturday
            time_periods = cls._saturdays
        else:  # Sunday
            time_periods = cls._sundays

        for start, end in time_periods:
            if start <= dt_obj.strftime('%H:%M') <= end:
                return True
        return False


class FareCalculator:
    _fare_chart = {
        ('Green', 'Green'): {'Peak': 2, 'Non-Peak': 1},
        ('Red', 'Red'): {'Peak': 3, 'Non-Peak': 2},
        ('Green', 'Red'): {'Peak': 4, 'Non-Peak': 3},
        ('Red', 'Green'): {'Peak': 3, 'Non-Peak': 2}
    }

    _cap_chart = {
        ('Green', 'Green'): {'Daily': 8, 'Weekly': 55},
        ('Red', 'Red'): {'Daily': 12, 'Weekly': 70},
        ('Green', 'Red'): {'Daily': 15, 'Weekly': 90},
        ('Red', 'Green'): {'Daily': 15, 'Weekly': 90}
    }

    @staticmethod
    def calculate_base_fare(from_line, to_line, date_time):
        if PeakHours.is_peak(date_time):
            return FareCalculator._fare_chart[(from_line, to_line)]['Peak']
        else:
            return FareCalculator._fare_chart[(from_line, to_line)]['Non-Peak']

    @classmethod
    def apply_daily_cap(cls, from_line, to_line, accumulated_daily_fare):
        return min(accumulated_daily_fare, cls._cap_chart[(from_line, to_line)]['Daily'])

    @classmethod
    def apply_weekly_cap(cls, from_line, to_line, accumulated_weekly_fare):
        return min(accumulated_weekly_fare, cls._cap_chart[(from_line, to_line)]['Weekly'])
    

class UserJourneyTracker:
    def __init__(self):
        self._daily_fares = {
            ('Green', 'Green'): 0,
            ('Red', 'Red'): 0,
            ('Green', 'Red'): 0,
            ('Red', 'Green'): 0
        }
        self._weekly_fares = {
            ('Green', 'Green'): 0,
            ('Red', 'Red'): 0,
            ('Green', 'Red'): 0,
            ('Red', 'Green'): 0
        }
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
            self._reset_weekly_fares()
            self._week_start_date = current_date

        # Check if a new day has begun
        if self._last_journey_date is not None and self._last_journey_date != current_date:
            self._reset_daily_fares()

        self._last_journey_date = current_date

    def add_journey(self, from_line, to_line, base_fare, date):
        # Parse date
        journey_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S").date()

        self._reset_fares_if_needed(journey_date)

        # Calculate cumulative daily and weekly fare for the specific line combination + base fare
        accumulated_daily_fare = self._daily_fares[(from_line, to_line)] + base_fare
        accumulated_weekly_fare = self._weekly_fares[(from_line, to_line)] + base_fare

        capped_daily_fare = FareCalculator.apply_daily_cap(from_line, to_line, accumulated_daily_fare)
        capped_weekly_fare = FareCalculator.apply_weekly_cap(from_line, to_line, accumulated_weekly_fare)

        # Determine the fare that can be charged for this journey considering both daily and weekly caps
        fare_to_charge = min(base_fare, capped_daily_fare - self._daily_fares[(from_line, to_line)], capped_weekly_fare - self._weekly_fares[(from_line, to_line)])

        # Update the accumulated fares after charging for this journey
        self._daily_fares[(from_line, to_line)] += fare_to_charge
        self._weekly_fares[(from_line, to_line)] += fare_to_charge

        return fare_to_charge
    