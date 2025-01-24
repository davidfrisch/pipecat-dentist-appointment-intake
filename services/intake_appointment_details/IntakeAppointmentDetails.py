import datetime as dt
import sys

from typing import Optional
from loguru import logger


from .tools import IntakeAppointmentTools

from ..google_calendar_api import calendar_utils as gcal


class IntakeAppointmentDetails:
    def __init__(self):
        pass
      
    async def handle_reason_for_appointment(self, context, result_callback):
        context.set_tools(
          [IntakeAppointmentTools.handle_appointment_date_schedule]
        )
        
        today_date = dt.date.today()
        today_day = today_date.strftime("%A")
        
        await result_callback(
            {
                "role": "system",
                "content": (
                    "Thank you for providing the reason for your appointment."
                    "Please provide the date you would like to schedule the appointment."
                    f"Today is {today_day}, {today_date}"
                    "If the user provides just a day of the week."
                    "If the user says as soon as possible, assume it is for today."
                    "Once the user provides the date, call the handle_appointment_date_schedule function."
                ),
            }
        )
     
    async def handle_appointment_date_schedule(self, context, result_callback, meeting_date: Optional[dt.date] = None, meeting_day: Optional[str] = None):
        try:
            if meeting_day and not meeting_date:
                try:
                    meeting_date = gcal.find_date_from_day(meeting_day)
                except ValueError as e:
                    await result_callback(
                        {
                            "role": "system",
                            "content": "Cannot find the day in the next 7 days. Please provide another day for the appointment."
                        })
                    return None
                  
            if meeting_date and not meeting_day:
                meeting_day = meeting_date.strftime("%A")
                
            if not meeting_date and not meeting_day:
                meeting_date = dt.date.today() - dt.timedelta(days=1)
                meeting_day = meeting_date.strftime("%A")
                
            
            available_hours = gcal.availability_date_check(meeting_date)
        
            if len(available_hours) > 0:
                context.set_tools(
                  [IntakeAppointmentTools.handle_appointment_date_schedule,
                   IntakeAppointmentTools.handle_appointment_time_schedule]
                )
                available_hours = "h, ".join([str(hour) for hour in available_hours])
                
                context_text = f"Thank you for providing the date for your appointment. Please provide the time you would like to schedule the appointment. Available hours for {meeting_date} are {available_hours}. Don't say hundreds, just say the hour.  Once the user provides the time, call the handle_appointment_time_schedule function."
                await result_callback(
                    {
                        "role": "system",
                        "content": context_text
                    }
                )
                return meeting_date
              
              
        except Exception as e:
            logger.error(f"Error: {e}")
        
        
        context.set_tools([
          IntakeAppointmentTools.handle_appointment_date_schedule
        ])
        
        
        reason_not_available = "The date you have provided is not possible anymore" 
        closest_possible_date = gcal.closest_available_date(meeting_date)
        context_text = f"{reason_not_available}. Please provide another date for the appointment. The closest available date is {closest_possible_date}"
        await result_callback(
            {
                "role": "system",
                "content": context_text
            }
        )
        return None
                
    async def handle_appointment_time_schedule(self, args, context, result_callback, meeting_date: dt.date = None, meeting_time: Optional[dt.time] = None):
        try:
            if not meeting_time:
                raise ValueError("No time provided")
            
            meeting_time = dt.time.fromisoformat(meeting_time)
            meeting_date = dt.date.fromisoformat(meeting_date)
            
            is_time_available = gcal.availability_date_time_check(meeting_date, meeting_time)
            
            context.set_tools([
              IntakeAppointmentTools.handle_appointment_time_schedule,
              IntakeAppointmentTools.handle_appointment_confirmation
            ])
            
            if is_time_available:
                await result_callback(
                    {
                        "role": "system",
                        "content": ("Thank you for providing the time for your appointment."
                                    f"Please confirm the appointment on {meeting_date} at {meeting_time}"
                                    "Call the handle_appointment_confirmation function to confirm the appointment."
                                    )
                    }
                )
            return meeting_time
          
        except Exception as e:
            logger.error(f"Error: {e}")
       
        context.set_tools([
            IntakeAppointmentTools.handle_appointment_date_schedule,
            IntakeAppointmentTools.handle_appointment_time_schedule
        ])
        await result_callback(
            {
                "role": "system",
                "content": "The time you have provided is not available. Please provide another time for the appointment."
            }
        )
        
        return None
  
    async def handle_appointment_confirmation(self, context, result_callback, next_function, confirmation: bool, meeting_details):
        if confirmation: 
            context.set_tools(
              [next_function]
            )
            gcal.create_event(
              title=f"Appointment with {meeting_details.first_name} {meeting_details.last_name}",
              start=dt.datetime.combine(meeting_details.date, meeting_details.time),
              end=dt.datetime.combine(meeting_details.date, meeting_details.time) + dt.timedelta(hours=1),
              description=meeting_details.reason + " (Appointment scheduled by JARVIS)"
            )
            await result_callback(
                {
                    "role": "system",
                    "content": "Tell to the user 'Good bye and Thank you for confirming the appointment.' and call the handle_end_call function."
                }
            )
        else:
            context.set_tools([
                IntakeAppointmentTools.handle_appointment_date_schedule,
                IntakeAppointmentTools.handle_appointment_time_schedule
              ])
            await result_callback(
                {
                    "role": "system",
                    "content": "The appointment has not been confirmed. What would do you want to modify?"
                }
            )
        
