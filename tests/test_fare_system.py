import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from fare_system import FareCalculator, FareCap, PeakHoursChecker, UserJourneyTracker
from constants import DATE_FORMAT

class TestPeakHoursChecker(unittest.TestCase):

    def setUp(self):
        self.peak_hours_config = {
            "monday": [["08:00", "10:00"], ["16:30", "19:00"]],
            "tuesday": [["08:00", "10:00"], ["16:30", "19:00"]],
            "wednesday": [["08:00", "10:00"], ["16:30", "19:00"]],
            "thursday": [["08:00", "10:00"], ["16:30", "19:00"]],
            "friday": [["08:00", "10:00"], ["16:30", "19:00"]],
            "saturday": [["10:00", "14:00"], ["18:00", "23:00"]],
            "sunday": [["18:00", "23:00"]]
        }

    def test_peak_and_non_peak_times(self):
        test_cases = [
            ("2023-09-04T08:00:00", True),  # Weekday morning peak
            ("2023-09-04T16:30:00", True),  # Weekday evening peak
            ("2023-09-04T07:59:00", False),  # Weekday non-peak
            ("2023-09-04T19:01:00", False),  # Weekday non-peak
            ("2023-09-09T10:00:00", True),  # Saturday morning peak
            ("2023-09-09T18:00:00", True),  # Saturday evening peak
            ("2023-09-09T09:59:00", False),  # Saturday non-peak
            ("2023-09-09T23:01:00", False),  # Saturday non-peak
            ("2023-09-10T18:00:00", True),  # Sunday evening peak
            ("2023-09-10T17:59:00", False),  # Sunday non-peak (before peak)
            ("2023-09-10T23:01:00", False),  # Sunday non-peak (after peak)
        ]

        peak_checker = PeakHoursChecker(self.peak_hours_config)

        for datetime_str, expected_result in test_cases:
            with self.subTest(datetime=datetime_str, expected=expected_result):
                self.assertEqual(peak_checker.is_peak(datetime_str), expected_result)

class TestFareCalculator(unittest.TestCase):

    def setUp(self):
        self.peak_hours_checker = MagicMock()
        
        self.fare_chart_config = {
            "line1,line2": {"peak": 10, "non_peak": 5},
            "line2,line3": {"peak": 12, "non_peak": 6},
            "line3,line4": {"peak": 15, "non_peak": 7},
            "line4,line5": {"peak": 8, "non_peak": 4},   
        }

        self.fare_calculator = FareCalculator(self.peak_hours_checker, self.fare_chart_config)

    def test_get_base_fare(self):
        test_cases = [
            ("line1", "line2", "2023-09-14T08:00:00", True, 10),
            ("line2", "line3", "2023-09-14T15:00:00", True, 12),
            ("line3", "line4", "2023-09-14T18:30:00", True, 15),
            ("line4", "line5", "2023-09-14T09:45:00", True, 8),
            ("line1", "line2", "2023-09-14T21:00:00", False, 5),
            ("line2", "line3", "2023-09-14T14:00:00", False, 6),
            ("line3", "line4", "2023-09-14T06:45:00", False, 7),
            ("line4", "line5", "2023-09-14T19:30:00", False, 4),
            ("line1", "line2", "2023-09-14T12:00:00", True, 10),
            ("line1", "line2", "2023-09-14T03:00:00", False, 5),
            ("line2", "line3", "2023-09-14T22:00:00", True, 12),
            ("line2", "line3", "2023-09-14T10:15:00", True, 12),
            ("line3", "line4", "2023-09-14T16:30:00", True, 15),
            ("line3", "line4", "2023-09-14T05:45:00", True, 15),
            ("line4", "line5", "2023-09-14T23:30:00", True, 8),
            ("line4", "line5", "2023-09-14T08:45:00", True, 8),
        ]

        for from_line, to_line, date_time, is_peak, expected_fare in test_cases:
            with self.subTest(from_line=from_line, to_line=to_line, date_time=date_time):
                self.peak_hours_checker.is_peak.return_value = is_peak
                base_fare = self.fare_calculator.get_base_fare(from_line, to_line, date_time)
                self.assertEqual(base_fare, expected_fare)

class TestFareCap(unittest.TestCase):

    def setUp(self):
        self.cap_chart_config = {
            "line1,line2": {"daily": 20, "weekly": 50},
            "line2,line3": {"daily": 15, "weekly": 40},
            "line3,line4": {"daily": 30, "weekly": 60},
        }

        self.fare_cap = FareCap(self.cap_chart_config)

    def test_apply_daily_cap(self):
        test_cases = [
            ("line1", "line2", 25, 20),  # Cap reached, should return the cap
            ("line2", "line3", 10, 15),  # Cap not reached, should return the accumulated fare
            ("line3", "line4", 35, 30),  # Cap reached, should return the cap
            ("line3", "line4", 25, 30),  # Cap not reached, should return the accumulated fare
            ("line1", "line2", 18, 20),  # Cap not reached, should return the accumulated fare
            ("line1", "line2", 22, 20),  # Cap reached, should return the cap
            ("line2", "line3", 5, 15),   # Cap not reached, should return the accumulated fare
            ("line2", "line3", 17, 15),  # Cap reached, should return the cap
            ("line3", "line4", 29, 30),  # Cap not reached, should return the accumulated fare
            ("line3", "line4", 31, 30),  # Cap reached, should return the cap
        ]

        for from_line, to_line, accumulated_daily_fare, daily_cap in test_cases:
            with self.subTest(from_line=from_line, to_line=to_line):
                result = self.fare_cap.apply_daily_cap(from_line, to_line, accumulated_daily_fare)
                self.assertEqual(result, min(accumulated_daily_fare, daily_cap))

    def test_apply_weekly_cap(self):
        test_cases = [
            ("line1", "line2", 55, 50),  # Cap reached, should return the cap
            ("line2", "line3", 42, 40),  # Cap reached, should return the cap
            ("line3", "line4", 70, 60),  # Cap reached, should return the cap
            ("line1", "line2", 45, 50),  # Cap not reached, should return the accumulated fare
            ("line2", "line3", 38, 40),  # Cap not reached, should return the accumulated fare
            ("line3", "line4", 58, 60),  # Cap not reached, should return the accumulated fare
            ("line1", "line2", 49, 50),  # Cap not reached, should return the accumulated fare
            ("line1", "line2", 52, 50),  # Cap reached, should return the cap
            ("line2", "line3", 39, 40),  # Cap not reached, should return the accumulated fare
            ("line2", "line3", 43, 40),  # Cap reached, should return the cap
            ("line3", "line4", 57, 60),  # Cap not reached, should return the accumulated fare
            ("line3", "line4", 62, 60),  # Cap reached, should return the cap
        ]

        for from_line, to_line, accumulated_weekly_fare, weekly_cap in test_cases:
            with self.subTest(from_line=from_line, to_line=to_line):
                result = self.fare_cap.apply_weekly_cap(from_line, to_line, accumulated_weekly_fare)
                self.assertEqual(result, min(accumulated_weekly_fare, weekly_cap))

class TestUserJourneyTracker(unittest.TestCase):

    def setUp(self):
        # Define sample peak hours configuration
        self.peak_hours_config = {
            "monday": [["08:00", "10:00"], ["16:30", "19:00"]],
            "tuesday": [["08:00", "10:00"], ["16:30", "19:00"]],
            "wednesday": [["08:00", "10:00"], ["16:30", "19:00"]],
            "thursday": [["08:00", "10:00"], ["16:30", "19:00"]],
            "friday": [["08:00", "10:00"], ["16:30", "19:00"]],
            "saturday": [["10:00", "14:00"], ["18:00", "23:00"]],
            "sunday": [["18:00", "23:00"]]
        }

        # Create a mock PeakHoursChecker
        self.peak_hours_checker = PeakHoursChecker(self.peak_hours_config)

        # Define a sample fare chart configuration for testing
        self.fare_chart_config = {
            "line1,line2": {"peak": 10, "non_peak": 5},
            "line2,line3": {"peak": 12, "non_peak": 6},
            "line3,line4": {"peak": 20, "non_peak": 10},
        }

        # Create a FareCalculator with the mock PeakHoursChecker
        self.fare_calculator = FareCalculator(self.peak_hours_checker, self.fare_chart_config)

        # Define a sample fare cap chart configuration for testing
        self.cap_chart_config = {
            "line1,line2": {"daily": 20, "weekly": 50},
            "line2,line3": {"daily": 15, "weekly": 40},
            "line3,line4": {"daily": 10, "weekly": 70},
        }

        # Create a FareCap instance
        self.fare_cap = FareCap(self.cap_chart_config)

        # Create a UserJourneyTracker instance with the FareCalculator and FareCap
        self.journey_tracker = UserJourneyTracker(self.fare_calculator, self.fare_cap)

    def test_add_journey_single_daily_cap(self):
        peak_time = "2023-09-14T08:00:00"
        fare1 = self.journey_tracker.add_journey("line1", "line2", peak_time)
        fare2 = self.journey_tracker.add_journey("line1", "line2", peak_time)
        fare3 = self.journey_tracker.add_journey("line1", "line2", peak_time)
        self.assertEqual(fare1, 10)
        self.assertEqual(fare2, 10)
        self.assertEqual(fare3, 0) # Reached daily cap for line1,line2

    def test_add_journey_multiple_daily_cap(self):
        peak_time = "2023-09-14T08:00:00"
        fare1 = self.journey_tracker.add_journey("line1", "line2", peak_time)
        fare2 = self.journey_tracker.add_journey("line1", "line2", peak_time)
        fare3 = self.journey_tracker.add_journey("line1", "line2", peak_time)
        self.assertEqual(fare1, 10)
        self.assertEqual(fare2, 10)
        self.assertEqual(fare3, 0) # Reached daily cap for line1,line2


        fare1 = self.journey_tracker.add_journey("line2", "line3", peak_time)
        fare2 = self.journey_tracker.add_journey("line2", "line3", peak_time)
        fare3 = self.journey_tracker.add_journey("line2", "line3", peak_time)
        self.assertEqual(fare1, 12)
        self.assertEqual(fare2, 3) # Reached partial cap for line2,line3
        self.assertEqual(fare3, 0) # Reached daily cap for line2,line3

    def test_add_journey_daily_cap_reset(self):
        peak_time = "2023-09-14T08:00:00"
        fare1 = self.journey_tracker.add_journey("line1", "line2", peak_time)
        fare2 = self.journey_tracker.add_journey("line1", "line2", peak_time)
        fare3 = self.journey_tracker.add_journey("line1", "line2", peak_time)
        self.assertEqual(fare1, 10)
        self.assertEqual(fare2, 10)
        self.assertEqual(fare3, 0) # Reached daily cap for line1,line2

        peak_time_tomorrow = "2023-09-15T08:00:00"
        fare1 = self.journey_tracker.add_journey("line1", "line2", peak_time_tomorrow)
        fare2 = self.journey_tracker.add_journey("line1", "line2", peak_time_tomorrow)
        fare3 = self.journey_tracker.add_journey("line1", "line2", peak_time_tomorrow)
        self.assertEqual(fare1, 10) # Cap is reset, should be charged
        self.assertEqual(fare2, 10)
        self.assertEqual(fare3, 0) # Reached daily cap for line1,line2

    def test_add_journey_daily_cap_reset_multiple_line(self):
        non_peak_time = "2023-09-14T21:00:00"
        fare1 = self.journey_tracker.add_journey("line1", "line2", non_peak_time)
        fare2 = self.journey_tracker.add_journey("line1", "line2", non_peak_time)
        fare3 = self.journey_tracker.add_journey("line1", "line2", non_peak_time)
        fare4 = self.journey_tracker.add_journey("line1", "line2", non_peak_time)
        fare5 = self.journey_tracker.add_journey("line1", "line2", non_peak_time)
        self.assertEqual(fare1, 5)
        self.assertEqual(fare2, 5)
        self.assertEqual(fare3, 5)
        self.assertEqual(fare4, 5)
        self.assertEqual(fare5, 0) # Reached daily cap for line1,line2

        fare1 = self.journey_tracker.add_journey("line2", "line3", non_peak_time)
        fare2 = self.journey_tracker.add_journey("line2", "line3", non_peak_time)
        fare3 = self.journey_tracker.add_journey("line2", "line3", non_peak_time)
        fare4 = self.journey_tracker.add_journey("line2", "line3", non_peak_time)
        self.assertEqual(fare1, 6)
        self.assertEqual(fare2, 6) 
        self.assertEqual(fare3, 3) # Reached partial cap for line2,line3
        self.assertEqual(fare4, 0) # Reached daily cap for line2,line3

        non_peak_time_tomorrow = "2023-09-15T21:00:00"
        fare1 = self.journey_tracker.add_journey("line1", "line2", non_peak_time_tomorrow)
        fare2 = self.journey_tracker.add_journey("line1", "line2", non_peak_time_tomorrow)
        fare3 = self.journey_tracker.add_journey("line1", "line2", non_peak_time_tomorrow)
        fare4 = self.journey_tracker.add_journey("line1", "line2", non_peak_time_tomorrow)
        fare5 = self.journey_tracker.add_journey("line1", "line2", non_peak_time_tomorrow)
        self.assertEqual(fare1, 5) # Cap is reset, should be charged
        self.assertEqual(fare2, 5)
        self.assertEqual(fare3, 5)
        self.assertEqual(fare4, 5)
        self.assertEqual(fare5, 0) # Reached daily cap for line1,line2

        fare1 = self.journey_tracker.add_journey("line2", "line3", non_peak_time_tomorrow)
        fare2 = self.journey_tracker.add_journey("line2", "line3", non_peak_time_tomorrow)
        fare3 = self.journey_tracker.add_journey("line2", "line3", non_peak_time_tomorrow)
        fare4 = self.journey_tracker.add_journey("line2", "line3", non_peak_time_tomorrow)
        self.assertEqual(fare1, 6) # Cap is reset, should be charged
        self.assertEqual(fare2, 6) 
        self.assertEqual(fare3, 3) # Reached partial cap for line2,line3
        self.assertEqual(fare4, 0) # Reached daily cap for line2,line3

    def test_add_journey_weekly_cap_reset(self):
        # Set the initial date to a Monday
        running_date = datetime(2023, 9, 14, 12, 0, 0)
        non_peak_time = running_date.strftime('%Y-%m-%dT%H:%M:%S')

        # Add journeys for the entire week to reach the weekly cap
        for _ in range(6):
            fare1 = self.journey_tracker.add_journey("line3", "line4", non_peak_time)
            fare2 = self.journey_tracker.add_journey("line3", "line4", non_peak_time)
            self.assertEqual(fare1, 10)
            self.assertEqual(fare2, 0) # Reached daily cap
            running_date += timedelta(days=1)
            non_peak_time = running_date.strftime('%Y-%m-%dT%H:%M:%S')

        final_uncapped_fare = self.journey_tracker.add_journey("line3", "line4", non_peak_time)
        self.assertEqual(final_uncapped_fare, 10)
        capped_fare = self.journey_tracker.add_journey("line3", "line4", non_peak_time)
        self.assertEqual(capped_fare, 0)

        # Advance the date to the next Monday (simulate a week later)
        running_date += timedelta(days=1)
        non_peak_time = running_date.strftime('%Y-%m-%dT%H:%M:%S')

        # Add a journey for the new week
        fare = self.journey_tracker.add_journey("line3", "line4", non_peak_time)

        # The fare should be charged since it's a new week
        self.assertEqual(fare, 10)
        
if __name__ == '__main__':
    unittest.main()