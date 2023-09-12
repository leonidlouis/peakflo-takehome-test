# Fare System

A fare calculation system for a fictional public transportation network.

## Features

- Computes fare based on journey details.
- Considers peak hours for fare adjustments.
- Implements daily and weekly fare caps.
- Reads and processes CSV files containing journey records.

## Getting Started

### Prerequisites

- Python 3.x

### Installation

1. Clone this repository.
```bash
git clone https://github.com/leonidlouis/peakflo-takehome-test
```
2. Navigate to the project directory.
```bash
cd peakflo-takehome-test
```
3. Run the program.
```bash
python3 main.py
```

## Usage
Run the `main.py` script to calculate the fare from a sample CSV file. If all tests pass, the total fare will be printed to the console. If any test fails, the corresponding error message will be displayed.

## Tests
Unit tests are provided in `test.py`. The main logic (`main.py`) will first execute these tests before calculating the fare. Ensure all tests are passing to get a valid fare calculation.
### Running Tests Separately
You can run unit tests independently with:
```bash
python3 test.py
```
