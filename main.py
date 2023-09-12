import csv
import subprocess
from datetime import datetime
from fare_system import UserJourneyTracker, FareCalculator

def read_csv_and_calculate_fare(file_path):
    user_tracker = UserJourneyTracker()
    total_fare = 0
    journeys = []

    # Load the CSV into the journeys list
    with open(file_path, mode='r') as file:
        csv_reader = csv.reader(file)
        journeys = list(csv_reader)

    # Sort the journeys by date and time
    journeys.sort(key=lambda x: datetime.strptime(x[2], "%Y-%m-%dT%H:%M:%S"))

    for journey in journeys:
        if len(journey) != 3:
            raise ValueError("Malformed CSV data detected")
            
        from_line, to_line, date_time = journey
        base_fare = FareCalculator.calculate_base_fare(from_line, to_line, date_time)
        
        fare_to_charge = user_tracker.add_journey(from_line, to_line, base_fare, date_time)

        total_fare += fare_to_charge

    return total_fare

if __name__ == "__main__":
    result = subprocess.run(['python3', '-m', 'unittest', 'test.py'], capture_output=True)
    
    if result.returncode == 0:
        print(f"Total Fare: ${read_csv_and_calculate_fare('target.csv')}")
    else:
        print("Tests failed. Please fix the issues before running the main logic.")
        print(result.stdout.decode('utf-8'))