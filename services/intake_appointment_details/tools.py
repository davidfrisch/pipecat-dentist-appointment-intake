
class IntakeAppointmentTools():
    
    handle_reason_for_appointment = {
      "type": "function",
      "function": {
        "name": "handle_reason_for_appointment",
        "description": "Once the user provides the reason for the appointment, call the handle_reason_for_appointment function.",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "The reason for the appointment.",
                }
            },
        },
      }
    }
    
    handle_appointment_date_schedule={
      "type": "function",
      "function": {
        "name": "handle_appointment_date_schedule",
        "description": "Once the user provides the date for the appointment, call the handle_appointment_date_schedule function.",
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "The date of the appointment, in the format YYYY-MM-DD. Leave empty if not specified by the user.",
                },
                "day": {
                    "type": "string",
                    "description": "The day of the appointment. Leave empty if not specified by the user. It can be 'today', 'tomorrow' or a day of the week written (e.g. 'monday').",
                },
            },
        },
      }
    }
    
    handle_appointment_time_schedule={
      "type": "function",
      "function": {
        "name": "handle_appointment_time_schedule",
        "description": "Once the user provides a time of the appointment, call the handle_appointment_time_schedule function.",
        "parameters": {
            "type": "object",
            "properties": {
                "time": {
                    "type": "string",
                    "description": (
                        "The time of the appointment, in the format HH:MM, 24-hour format."
                        "It can only be during the day, so no need to specify AM or PM."
                      ),
                },
                "date": {
                    "type": "string",
                    "description": "The last given date of the appointment, in the format YYYY-MM-DD.",
                },
            },
        },
      }
    }
    
    handle_appointment_confirmation={
      "type": "function",
      "function": {
        "name": "handle_appointment_confirmation",
        "description": "When the system asks for confirmation, call the handle_appointment_confirmation function.",
        "parameters": {
            "type": "object",
            "properties": {
                "confirmation": {
                    "type": "boolean",
                    "description": "The user's confirmation.",
                }
            },
        },
      }
    }