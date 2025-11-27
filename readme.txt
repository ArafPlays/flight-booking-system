Admins login to admin panel and create flights. Flights are stored on database.

Users are able to search and book these flight(s) on the homepage. They can choose one way or round trip.
Users are able to make some selections during booking process (meal choice, seat choice, etc.)
Passenger(s) and booking details are stored on database.

Users are able to manage their booking. (They need booking id and ref to manage)

LOCAL SET UP

1. Download/clone the repo

2. Create virtual environment:
   python -m venv venv

3. Activate it:
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows

4. Install dependencies:
   pip install -r requirements.txt

5. Run the app:
   python main.py
