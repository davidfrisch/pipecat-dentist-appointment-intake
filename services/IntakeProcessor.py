
import sys

from dotenv import load_dotenv
import datetime as dt
from pydantic import BaseModel
from typing import Optional
from loguru import logger


from pipecat.services.openai import OpenAILLMContext, FunctionCallResultProperties
from pipecat.processors.frame_processor import FrameDirection
from pipecat.frames.frames import EndFrame

from .constants import TIME_OF_MEETING
from .llm_tools.intake_appointment_details import IntakeAppointmentTools

from .transitions import FLOW_TRANSITIONS
from .google_calendar_api import calendar_utils as gcal

load_dotenv(override=True)


class MeetingDetailsForm(BaseModel):
    """
    A class to represent the form for meeting details.
      first_name: str
      last_name: str
      reason: str
      date: dt.date
      time: dt.time
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    reason: Optional[str] = None
    date: Optional[dt.date] = None
    time: Optional[dt.time] = None


class IntakeProcessor:
    def __init__(self, context: OpenAILLMContext):
        self.current_language = "french"
        self.meeting_details = MeetingDetailsForm()

        context.add_message(FLOW_TRANSITIONS["init"]["message"](self.current_language))
        context.set_tools(FLOW_TRANSITIONS["init"]["tools"])
    
    
    """
    Handlers for the different states
    """
    async def handle_first_name(self, function_name, tool_call_id, args, llm, context, result_callback):
        first_name = args["first_name"] if "first_name" in args else None
        
        context.set_tools(FLOW_TRANSITIONS[function_name]["tools"])
        await result_callback(FLOW_TRANSITIONS[function_name]["message"])
        
        if first_name:
            self.meeting_details.first_name = first_name
        
        
    async def handle_last_name(self, function_name, tool_call_id, args, llm, context, result_callback):
        last_name = args["last_name"] if "last_name" in args else None

        if "last_name" not in args:
            await result_callback(
                {
                    "role": "system",
                    "content": "I'm sorry, I didn't get your last name. Can you please provide it again?"
                }
            )
            return
        
        context.set_tools(FLOW_TRANSITIONS[function_name]["tools"])
        await result_callback(FLOW_TRANSITIONS[function_name]["message"])

        if last_name:
            self.meeting_details.last_name = last_name
        
  
    async def handle_reason_for_appointment(self, function_name, tool_call_id, args, llm, context, result_callback):
        reason = args["reason"] if "reason" in args else None
        self.meeting_details.reason = reason
        
        today_date = dt.date.today().strftime("%B %d, %Y")
        today_day = dt.date.today().strftime("%A")
        
        total_today = f"{today_day}, {today_date}"
        
        context.set_tools(FLOW_TRANSITIONS[function_name]["tools"])
        await result_callback(FLOW_TRANSITIONS[function_name]["message"](total_today))


    async def handle_appointment_date_schedule(self, function_name, tool_call_id, args, llm, context, result_callback):
        meeting_day = args["day"] if "day" in args else None
        meeting_date = dt.date.fromisoformat(args["date"]) if "date" in args else None
        try:
            if meeting_day and not meeting_date:
                try:
                    meeting_date = gcal.find_date_from_day(meeting_day)
                except ValueError as e:
                    await result_callback(
                        {
                            "role": "system",
                            "content": "This day is not valid. Please provide a valid day of the week."
                        })
                    return None
                  
            if meeting_date and not meeting_day:
                meeting_day = meeting_date.strftime("%A")
                
            if not meeting_date and not meeting_day:
                meeting_date = dt.date.today()
                meeting_day = meeting_date.strftime("%A")
              
                
            available_hours = gcal.availability_date_check(meeting_date)
        
            if len(available_hours) > 0:
                self.meeting_details.date = meeting_date
                
                context.set_tools(FLOW_TRANSITIONS[function_name]["tools"])
                available_hours = "h, ".join([str(hour) for hour in available_hours])
                
                await result_callback(FLOW_TRANSITIONS[function_name]["message"](meeting_date, available_hours))
                return meeting_date
              
              
        except Exception as e:
            logger.error(f"Error: {e}")
        
        
        # Stay in the same state because the date is not available
        context.set_tools([IntakeAppointmentTools.handle_appointment_date_schedule])
        
        closest_possible_date = gcal.closest_available_date(meeting_date)
        context_text = f"The date you have provided is not possible anymore. Please provide another date for the appointment. The closest available date is/are {closest_possible_date}"
        
        await result_callback(
            {
                "role": "system",
                "content": context_text
            }
        )
        return None        
        
  
  
     
    async def handle_appointment_time_schedule(self, function_name, tool_call_id, args, llm, context, result_callback):
        meeting_time = args["time"] if "time" in args else None
        meeting_date = args["date"] if "date" in args else self.meeting_details.date
        try:
            if not meeting_time:
                raise ValueError("No time provided")
            
            meeting_time = dt.time.fromisoformat(meeting_time)
            meeting_date = dt.date.fromisoformat(meeting_date)
            self.meeting_details.time = meeting_time
            
            is_time_available = gcal.availability_date_time_check(meeting_date, meeting_time)
            
            context.set_tools(FLOW_TRANSITIONS[function_name]["tools"])
            
            if is_time_available:
                await result_callback(FLOW_TRANSITIONS[function_name]["message"](meeting_date, meeting_time))
            return meeting_time
          
        except Exception as e:
            logger.error(f"Error: {e}")
       
       
        # Stay in the same state because the time is not available
        context.set_tools([
            IntakeAppointmentTools.handle_appointment_date_schedule,
            IntakeAppointmentTools.handle_appointment_time_schedule
        ])
        await result_callback(
            {
                "role": "system",
                "content": """The time you have provided is not available. Please provide another time for the appointment. Or ask for another date.
                If the user ask for another date, call the handle_appointment_date_schedule function.
                If the user provides another time, call the handle_appointment_time_schedule function.
                """
            }
        )
        
        return None

  
      
    async def handle_appointment_confirmation(self, function_name, tool_call_id, args, llm, context, result_callback):
        confirmation = args["confirmation"] if "confirmation" in args else False
        if confirmation: 
            context.set_tools(FLOW_TRANSITIONS[function_name]["tools"])
            gcal.create_event(
                title=f"Appointment with {self.meeting_details.first_name} {self.meeting_details.last_name}",
                start=dt.datetime.combine(self.meeting_details.date, self.meeting_details.time),
                end=dt.datetime.combine(self.meeting_details.date, self.meeting_details.time) + dt.timedelta(hours=TIME_OF_MEETING),
                description=self.meeting_details.reason + " (Appointment scheduled by JARVIS)"
            )
            await result_callback(FLOW_TRANSITIONS[function_name]["message"])
        else:
            context.set_tools(FLOW_TRANSITIONS["handle_appointment_time_schedule"]["tools"])
            await result_callback(
                {
                    "role": "system",
                    "content": "I'm sorry, the appointment has not been confirmed. Please provide another time or date for the appointment."
                }
            )
        
    
    async def handle_switch_language(self, function_name, tool_call_id, args, llm, context, result_callback):
        language = args["language"] if "language" in args else None
        
        if language not in ["english", "french"]:
            await result_callback(
                {
                    "role": "system",
                    "content": "I'm sorry, I only speak English and French. Please choose one of the two languages. (In the current language)"
                }
            )
            return
          
        self.current_language = language
        await result_callback(
            {
                "role": "system",
                "content": f"Language has been switched to {language}. Ask now for their first name."
            }
        )


    async def handle_end_call(self, function_name, tool_call_id, args, llm, context, result_callback):
        await llm.push_frame(EndFrame(), FrameDirection.DOWNSTREAM)
        properties = FunctionCallResultProperties(run_llm=False)
        await result_callback(None, properties=properties)
    
    
    
    """
    Filters for language
    """
    async def english_filter(self, frame):
        return self.current_language == "english"
    
    async def french_filter(self, frame):
        return self.current_language == "french"
 