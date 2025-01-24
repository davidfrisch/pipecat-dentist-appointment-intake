
import sys

from dotenv import load_dotenv
import datetime as dt
from pydantic import BaseModel
from typing import Optional

from pipecat.services.openai import OpenAILLMContext
from pipecat.transports.services.daily import DailyTransport
from pipecat.processors.frame_processor import FrameDirection
from pipecat.frames.frames import EndFrame

from .tools import IntakeProcessorTools

from .intake_contact_details.IntakeContactDetails import IntakeContactDetails
from .intake_contact_details.tools import IntakeContactDetailsTools
from .intake_appointment_details.IntakeAppointmentDetails import IntakeAppointmentDetails


from loguru import logger
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
        self.intake_contact_details = IntakeContactDetails()
        self.intake_appointment_details = IntakeAppointmentDetails()
        context.set_tool_choice
        context.add_message(
            {
                "role": "system",
                "content": f"""You are JARVIS, an assistant for Very Fresh Dentals. Your role is to help to add future appointments. You are speaking with an unknown caller. Remember, you are not a medical professional and must not provide medical advice. 
                Keep your responses concise and avoid making assumptions about input values; always seek clarification if a user's response is unclear. Start by presenting yourself and ask the caller if they prefer English or French. If they do not specify, assume the language is {self.current_language} and continue in that language. Ask for the user's first name and then call the handle_first_name function. 
                Mention that you can speak English or French and invite the user to switch languages if needed. If the user requests a language change, call the handle_switch_language function."""
            }
        )
        
        
        context.set_tools([
          IntakeProcessorTools.handle_switch_language,
          IntakeContactDetailsTools.first_name
        ])
    
        
    async def handle_first_name(self, function_name, tool_call_id, args, llm, context, result_callback):
        first_name = args["first_name"] if "first_name" in args else None
        await self.intake_contact_details.handle_first_name(args, context, result_callback)
        if first_name:
            self.meeting_details.first_name = first_name
        
        
    async def handle_last_name(self, function_name, tool_call_id, args, llm, context, result_callback):
        last_name = args["last_name"] if "last_name" in args else None
        await self.intake_contact_details.handle_last_name(args, context, result_callback)
        if last_name:
            self.meeting_details.last_name = last_name
        
  
    async def handle_reason_for_appointment(self, function_name, tool_call_id, args, llm, context, result_callback):
        reason = args["reason"] if "reason" in args else None
        self.meeting_details.reason = reason
        await self.intake_appointment_details.handle_reason_for_appointment(context, result_callback)


    async def handle_appointment_date_schedule(self, function_name, tool_call_id, args, llm, context, result_callback):
        arg_day = args["day"] if "day" in args else None
        arg_date = dt.date.fromisoformat(args["date"]) if "date" in args else None
        meeting_day = await self.intake_appointment_details.handle_appointment_date_schedule(context, result_callback, arg_date, arg_day)
        if meeting_day:
            self.meeting_details.date = meeting_day
  
     
    async def handle_appointment_time_schedule(self, function_name, tool_call_id, args, llm, context, result_callback):
        args_time = args["time"] if "time" in args else None
        args_date = args["date"] if "date" in args else self.meeting_details.date
        meeting_time = await self.intake_appointment_details.handle_appointment_time_schedule(args, context, result_callback, args_date, args_time)
        if meeting_time:
            self.meeting_details.time = meeting_time
  
      
    async def handle_appointment_confirmation(self, function_name, tool_call_id, args, llm, context, result_callback):
        confirmation = args["confirmation"] if "confirmation" in args else False
        await self.intake_appointment_details.handle_appointment_confirmation(
            context,
            result_callback,
            IntakeProcessorTools.handle_end_call,
            confirmation,
            self.meeting_details
        )
        
        
    async def handle_switch_language(self, function_name, tool_call_id, args, llm, context, result_callback):
        language = args["language"]
        
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
        await result_callback(None)
    
    async def english_filter(self, frame):
        return self.current_language == "english"
    
    async def french_filter(self, frame):
        return self.current_language == "french"
 