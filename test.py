import csv
import unittest

from io import StringIO
from unittest import mock, TestCase
from unittest.mock import mock_open

from fare_system import UserJourneyTracker, FareCalculator, PeakHours
from main import read_csv_and_calculate_fare

class TestPeakHours(TestCase):
    # Weekdays Tests
    def test_peak_on_weekdays(self):
        # Morning
        self.assertTrue(PeakHours.is_peak("2023-09-04T08:00:00"))
        self.assertTrue(PeakHours.is_peak("2023-09-04T10:00:00"))
        # Evening
        self.assertTrue(PeakHours.is_peak("2023-09-04T16:30:00"))
        self.assertTrue(PeakHours.is_peak("2023-09-04T19:00:00"))

    def test_non_peak_on_weekdays(self):
        # Morning
        self.assertFalse(PeakHours.is_peak("2023-09-04T07:59:00"))
        self.assertFalse(PeakHours.is_peak("2023-09-04T10:01:00"))
        # Evening
        self.assertFalse(PeakHours.is_peak("2023-09-04T16:29:00"))
        self.assertFalse(PeakHours.is_peak("2023-09-04T19:01:00"))

    # Saturdays Tests
    def test_peak_on_saturdays(self):
        # Morning
        self.assertTrue(PeakHours.is_peak("2023-09-09T10:00:00"))
        self.assertTrue(PeakHours.is_peak("2023-09-09T14:00:00"))
        # Evening
        self.assertTrue(PeakHours.is_peak("2023-09-09T18:00:00"))
        self.assertTrue(PeakHours.is_peak("2023-09-09T23:00:00"))

    def test_non_peak_on_saturdays(self):
        # Morning
        self.assertFalse(PeakHours.is_peak("2023-09-09T09:59:00"))
        self.assertFalse(PeakHours.is_peak("2023-09-09T14:01:00"))
        # Evening
        self.assertFalse(PeakHours.is_peak("2023-09-09T17:59:00"))
        self.assertFalse(PeakHours.is_peak("2023-09-09T23:01:00"))

    # Sundays Tests
    def test_peak_on_sundays(self):
        # Evening
        self.assertTrue(PeakHours.is_peak("2023-09-10T18:00:00"))
        self.assertTrue(PeakHours.is_peak("2023-09-10T23:00:00"))

    def test_non_peak_on_sundays(self):
        # Before evening peak
        self.assertFalse(PeakHours.is_peak("2023-09-10T17:59:00"))
        # After evening peak
        self.assertFalse(PeakHours.is_peak("2023-09-10T23:01:00"))

class TestFareCalculator(TestCase):

    def test_green_to_green_peak(self):
        self.assertEqual(FareCalculator.calculate_base_fare('Green', 'Green', "2023-09-04T08:00:00"), 2)
        self.assertEqual(FareCalculator.calculate_base_fare('Green', 'Green', "2023-09-09T10:30:00"), 2)
        self.assertEqual(FareCalculator.calculate_base_fare('Green', 'Green', "2023-09-10T18:30:00"), 2)

    def test_green_to_green_non_peak(self):
        self.assertEqual(FareCalculator.calculate_base_fare('Green', 'Green', "2023-09-04T10:01:00"), 1)
        self.assertEqual(FareCalculator.calculate_base_fare('Green', 'Green', "2023-09-09T09:59:00"), 1)
        self.assertEqual(FareCalculator.calculate_base_fare('Green', 'Green', "2023-09-10T17:59:00"), 1)

    def test_red_to_red_peak(self):
        self.assertEqual(FareCalculator.calculate_base_fare('Red', 'Red', "2023-09-04T08:00:00"), 3)
        self.assertEqual(FareCalculator.calculate_base_fare('Red', 'Red', "2023-09-09T11:00:00"), 3)
        self.assertEqual(FareCalculator.calculate_base_fare('Red', 'Red', "2023-09-10T18:45:00"), 3)

    def test_red_to_red_non_peak(self):
        self.assertEqual(FareCalculator.calculate_base_fare('Red', 'Red', "2023-09-04T10:01:00"), 2)
        self.assertEqual(FareCalculator.calculate_base_fare('Red', 'Red', "2023-09-09T09:59:00"), 2)
        self.assertEqual(FareCalculator.calculate_base_fare('Red', 'Red', "2023-09-10T17:59:00"), 2)

    def test_green_to_red_peak(self):
        self.assertEqual(FareCalculator.calculate_base_fare('Green', 'Red', "2023-09-04T08:00:00"), 4)
        self.assertEqual(FareCalculator.calculate_base_fare('Green', 'Red', "2023-09-09T12:00:00"), 4)
        self.assertEqual(FareCalculator.calculate_base_fare('Green', 'Red', "2023-09-10T19:00:00"), 4)

    def test_green_to_red_non_peak(self):
        self.assertEqual(FareCalculator.calculate_base_fare('Green', 'Red', "2023-09-04T10:01:00"), 3)
        self.assertEqual(FareCalculator.calculate_base_fare('Green', 'Red', "2023-09-09T09:59:00"), 3)
        self.assertEqual(FareCalculator.calculate_base_fare('Green', 'Red', "2023-09-10T17:59:00"), 3)

    def test_red_to_green_peak(self):
        self.assertEqual(FareCalculator.calculate_base_fare('Red', 'Green', "2023-09-04T08:00:00"), 3)
        self.assertEqual(FareCalculator.calculate_base_fare('Red', 'Green', "2023-09-09T13:00:00"), 3)
        self.assertEqual(FareCalculator.calculate_base_fare('Red', 'Green', "2023-09-10T20:00:00"), 3)

    def test_red_to_green_non_peak(self):
        self.assertEqual(FareCalculator.calculate_base_fare('Red', 'Green', "2023-09-04T10:01:00"), 2)
        self.assertEqual(FareCalculator.calculate_base_fare('Red', 'Green', "2023-09-09T09:59:00"), 2)
        self.assertEqual(FareCalculator.calculate_base_fare('Red', 'Green', "2023-09-10T17:59:00"), 2)

    # Daily Cap Tests
    def test_apply_daily_cap_below_limit(self):
        # Accumulated fare is below the cap for Green to Green line
        self.assertEqual(FareCalculator.apply_daily_cap('Green', 'Green', 5), 5)

        # Accumulated fare is below the cap for Green to Red line
        self.assertEqual(FareCalculator.apply_daily_cap('Green', 'Red', 10), 10)

    def test_apply_daily_cap_at_limit(self):
        # Accumulated fare meets the cap for Green to Green line
        self.assertEqual(FareCalculator.apply_daily_cap('Green', 'Green', 8), 8)

        # Accumulated fare meets the cap for Green to Red line
        self.assertEqual(FareCalculator.apply_daily_cap('Green', 'Red', 15), 15)

    def test_apply_daily_cap_above_limit(self):
        # Accumulated fare exceeds the cap for Green to Green line
        self.assertEqual(FareCalculator.apply_daily_cap('Green', 'Green', 10), 8)

        # Accumulated fare exceeds the cap for Green to Red line
        self.assertEqual(FareCalculator.apply_daily_cap('Green', 'Red', 20), 15)

    # Weekly Cap Tests
    def test_apply_weekly_cap_below_limit(self):
        # Accumulated fare is below the cap for Green to Green line
        self.assertEqual(FareCalculator.apply_weekly_cap('Green', 'Green', 40), 40)

        # Accumulated fare is below the cap for Green to Red line
        self.assertEqual(FareCalculator.apply_weekly_cap('Green', 'Red', 70), 70)

    def test_apply_weekly_cap_at_limit(self):
        # Accumulated fare meets the cap for Green to Green line
        self.assertEqual(FareCalculator.apply_weekly_cap('Green', 'Green', 55), 55)

        # Accumulated fare meets the cap for Green to Red line
        self.assertEqual(FareCalculator.apply_weekly_cap('Green', 'Red', 90), 90)

    def test_apply_weekly_cap_above_limit(self):
        # Accumulated fare exceeds the cap for Green to Green line
        self.assertEqual(FareCalculator.apply_weekly_cap('Green', 'Green', 60), 55)

        # Accumulated fare exceeds the cap for Green to Red line
        self.assertEqual(FareCalculator.apply_weekly_cap('Green', 'Red', 100), 90)


class TestUserJourneyTracker(TestCase):

    def setUp(self):
        self.tracker = UserJourneyTracker()

    # Single journey fare tests
    def test_single_journey_fare(self):
        fare = FareCalculator.calculate_base_fare('Green', 'Green', "2023-09-04T09:00:00")
        charged_fare = self.tracker.add_journey('Green', 'Green', fare, "2023-09-04T09:00:00")
        self.assertEqual(charged_fare, fare)

    # Daily fare reset tests
    def test_reset_daily_fares_next_day(self):
        fare1 = FareCalculator.calculate_base_fare('Green', 'Green', "2023-09-04T09:00:00")
        self.tracker.add_journey('Green', 'Green', fare1, "2023-09-04T09:00:00")

        fare2 = FareCalculator.calculate_base_fare('Green', 'Green', "2023-09-05T09:00:00")
        charged_fare = self.tracker.add_journey('Green', 'Green', fare2, "2023-09-05T09:00:00")
        self.assertEqual(charged_fare, fare2)

    # Weekly fare reset tests
    def test_reset_weekly_fares_next_week(self):
        fare1 = FareCalculator.calculate_base_fare('Green', 'Green', "2023-09-04T09:00:00")
        self.tracker.add_journey('Green', 'Green', fare1, "2023-09-04T09:00:00")

        fare2 = FareCalculator.calculate_base_fare('Green', 'Green', "2023-09-12T09:00:00")
        charged_fare = self.tracker.add_journey('Green', 'Green', fare2, "2023-09-12T09:00:00")
        self.assertEqual(charged_fare, fare2)

    # Testing daily and weekly fare caps
    def test_daily_cap(self):
        fare = FareCalculator.calculate_base_fare('Green', 'Green', "2023-09-04T09:00:00")
        total_charged = 0
        for _ in range(10):  # Loop to intentionally exceed daily cap
            total_charged += self.tracker.add_journey('Green', 'Green', fare, "2023-09-04T09:00:00")
        self.assertTrue(total_charged <= FareCalculator._cap_chart[('Green', 'Green')]['Daily'])

    def test_weekly_cap(self):
        fare = FareCalculator.calculate_base_fare('Green', 'Green', "2023-09-04T09:00:00")
        total_charged = 0
        for day in range(7):  # Loop through a week
            date = f"2023-09-{4 + day:02}T09:00:00"
            for _ in range(10):  # Intentionally exceed daily cap, but mainly push towards the weekly cap
                total_charged += self.tracker.add_journey('Green', 'Green', fare, date)
        self.assertTrue(total_charged <= FareCalculator._cap_chart[('Green', 'Green')]['Weekly'])


class TestCSVProcessing(TestCase):

    def setUp(self):
        self.m = mock_open()

    def read_csv_helper(self, csv_content):
        # Use StringIO to simulate file object
        mock_file = StringIO(csv_content)

        # Mocking csv.reader and the open function
        with mock.patch('builtins.open', return_value=mock_file):
            with mock.patch('csv.reader', return_value=csv.reader(mock_file)):
                return read_csv_and_calculate_fare('mocked_path.csv')

    def test_empty_file(self):
        result = self.read_csv_helper('')
        self.assertEqual(result, 0)

    def test_single_row(self):
        csv_content = 'Green,Red,2023-09-12T08:30:00'
        base_fare = FareCalculator.calculate_base_fare('Green', 'Red', '2023-09-12T08:30:00')
        expected_fare = base_fare
        self.assertEqual(self.read_csv_helper(csv_content), expected_fare)

    def test_multiple_rows_unsorted(self):
        csv_content = '''Green,Red,2023-09-12T15:30:00
Green,Red,2023-09-12T08:30:00'''
        base_fare_morning = FareCalculator.calculate_base_fare('Green', 'Red', '2023-09-12T08:30:00')
        base_fare_afternoon = FareCalculator.calculate_base_fare('Green', 'Red', '2023-09-12T15:30:00')
        expected_fare = base_fare_morning + base_fare_afternoon
        self.assertEqual(self.read_csv_helper(csv_content), expected_fare)

    def test_malformed_csv(self):
        csv_content = '''Green,Red
                         Green,RedA,2023-09-12T08:30:00XYZ'''
        with self.assertRaises(Exception):
            self.read_csv_helper(csv_content)


if __name__ == "__main__":
    unittest.main()