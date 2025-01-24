from pydantic import BaseModel


class IntakeProcessorTools():
    handle_switch_language = {
      "type": "function",
      "function": {
        "name": "handle_switch_language",
        "description": "Use this function to switch the language of call, it can either be english or french.",
        "parameters": {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "description": "The language to switch to.",
                }
            },
        },
      }
    }
    
    
    handle_end_call = {
      "type": "function",
      "function":{
        "name": "handle_end_call",
        "description": "Use this function to end the call.",
        "parameters": {
            "type": "object",
            "properties": {},
        },
      }
    }