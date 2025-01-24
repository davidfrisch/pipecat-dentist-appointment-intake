from gcsa.google_calendar import GoogleCalendar
from gcsa.event import Event
import datetime as dt
from typing import List
import pytz
import os
from datetime import timedelta, datetime

# Constants for availability
AVAILABLE_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
AVAILABLE_STARTING_HOURS = [9, 10, 11, 13, 14, 15, 16]

dir_path = os.path.dirname(os.path.realpath(__file__))
# Initialize Google Calendar
gc = GoogleCalendar('frischer.london@gmail.com', credentials_path=os.path.join(dir_path, '../../credentials.json'))


def create_event(title: str, start: dt.datetime, end: dt.datetime, description: str = None):
    """
    Create an event on the Google Calendar.
    
    :param title: The title of the event.
    :param start: The start time of the event.
    :param end: The end time of the event.
    :param description: The description of the event.
    """
    gc.add_event(Event(
        title=title, 
        summary=title,
        start=start, 
        end=end, 
        description=description
    ))


def is_open_day(check_date: dt.date) -> bool:
    """
    Check if the given date falls on an available day.
    
    :param check_date: The date to check.
    :return: True if the date is an available day, False otherwise.
    """
    return check_date.strftime('%A') in AVAILABLE_DAYS



def is_open_hours(check_time: dt.time) -> bool:
    """
    Check if the given time falls within available hours.
    
    :param check_time: The time to check.
    :return: True if the time is within available hours, False otherwise.
    """
    print(check_time)
    return check_time.hour in AVAILABLE_STARTING_HOURS


def availability_date_check(check_date: dt.date) -> List[int]:
    """
    Check available hours for a given date.

    :param check_date: The date to check availability for (date object).
    :return: A list of available time slots as integers (hours).
    """
    # Copy available hours for modification
    available_hours = AVAILABLE_STARTING_HOURS.copy()
    current_time = datetime.now()

    # If the day is not open, return an empty list
    if not is_open_day(check_date):
        return []

    # Set time from now until the end of the day
    closest_earliest_hour = [hour for hour in available_hours if hour > current_time.hour] if check_date == current_time.date() else available_hours
    if not closest_earliest_hour:
        return []
    
    time_min = datetime.combine(check_date, dt.time(hour=closest_earliest_hour[0])) 
    time_max = datetime.combine(check_date, dt.time(hour=AVAILABLE_STARTING_HOURS[-1] + 1))  

    # Fetch free/busy information from Google Calendar
    free_busy = gc.get_free_busy(time_min=time_min, time_max=time_max)

    # If no busy events, return all available hours
    if not free_busy.calendars:
        return available_hours

    # Process busy intervals
    for busy_period in free_busy.calendars.values():
        for busy_time in busy_period:
            start = busy_time.start
            end = busy_time.end

            # Iterate through each hour in the busy range and remove it from availability
            for hour in range(start.hour, end.hour + 1):  # Include the end hour
                if hour in available_hours:
                    available_hours.remove(hour)

    return available_hours



def availability_date_time_check(check_date: dt.date, check_time: dt.time) -> bool:
    """
    Check if a specific date and time is available.

    :param check_date: The date to check availability for (date object).
    :param check_time: The time to check availability for (time object).
    :return: True if the date and time are available, False otherwise.
    """
    assert isinstance(check_date, dt.date), "check_date must be a date object"
    assert isinstance(check_time, dt.time), "check_time must be a time object"
    
    # Check if the day is open
    if not is_open_day(check_date):
        return False

    # Check if the time is within working hours
    if not is_open_hours(check_time):
        return False
    
    meeting_datetime = datetime.combine(check_date, check_time).replace(tzinfo=pytz.utc)
    
    time_min = datetime.combine(check_date, dt.time(hour=AVAILABLE_STARTING_HOURS[0]))  # Start of the workday
    time_max = datetime.combine(check_date, dt.time(hour=AVAILABLE_STARTING_HOURS[-1] + 1))  # End of the workday

    # Fetch free/busy information from Google Calendar
    free_busy = gc.get_free_busy(time_min=time_min, time_max=time_max)

    # Check if the specific time is busy
    for busy_period in free_busy.calendars.values():
        for busy_time in busy_period:
            start = busy_time.start
            end = busy_time.end
            print(start, end)
            print(meeting_datetime)
            if start <= meeting_datetime < end:
                return False

    return True


def closest_available_date(current_date: dt.date) -> dt.date:
    """
    Find the closest available date after the given date.
    
    :param current_date: The date to start searching from.
    :return: The closest available date after the given date.
    """
    # Increment the current date until an available day is found
    best_date = current_date
    while not is_open_day(best_date):
        best_date += timedelta(days=1)
    
    while not availability_date_check(best_date):
        print(best_date)
        best_date += timedelta(days=1)
    
    return best_date
  

def find_date_from_day(day: str) -> dt.date:
    """
    Find the date of the next available day based on the given day.
    
    :param day: The day to search for.
    :return: The date of the next available day.
    """
    day_of_the_week_french = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi']
    day_of_the_week_english = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    
    is_in_french = day.lower().strip() in day_of_the_week_french
    is_in_english = day.lower().strip() in day_of_the_week_english
    
    if not is_in_french and not is_in_english:
        raise ValueError("The day is not valid.")
    
    if is_in_french:
        day = day_of_the_week_english[day_of_the_week_french.index(day.lower().strip())]
    
    date_found = dt.date.today()    
    
    if day.lower().strip() == "today":
        date_found = dt.date.today()
    elif day.lower().strip() == "tomorrow":
        date_found = dt.date.today() + dt.timedelta(days=1)
    else:
        number_of_days = 0
        while date_found.strftime("%A").lower() != day.lower().strip():
            if number_of_days > 7:
                raise ValueError("The day is not in the next 7 days.")
            date_found += timedelta(days=1)
            number_of_days += 1
            
    return date_found
    


if __name__ == "__main__":
    # Example usage
    print(find_date_from_day("tomorrow"))
      
    