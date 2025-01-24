from .tools import IntakeContactDetailsTools
from ..intake_appointment_details.tools import IntakeAppointmentTools


class IntakeContactDetails:
    def __init__(self):
        pass
      
    async def handle_first_name(self, args, context, result_callback):
        context.set_tools([
           IntakeContactDetailsTools.first_name,
           IntakeContactDetailsTools.last_name]
        )

        await result_callback(
            {
                "role": "system",
                "content": "Confirm that the first name is correct. If it is, ask for the last name. If it is not, ask for the first name again.",
            }
        )
    
    async def handle_last_name(self, args, context, result_callback):
        if "last_name" not in args:
            await result_callback(
                {
                    "role": "system",
                    "content": "I'm sorry, I didn't get your last name. Can you please provide it again?"
                }
            )
            return
        
        context.set_tools([
           IntakeContactDetailsTools.last_name,
           IntakeAppointmentTools.handle_reason_for_appointment
        ])
        
        await result_callback(
            {
                "role": "system",
                "content": ("Confirm that the last name is correct.",
                            "If it is, ask for the reason for the appointment",
                            "If it is not, ask for the last name again"
                           )
            }
        )
      