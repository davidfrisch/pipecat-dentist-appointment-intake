

class IntakeContactDetailsTools():
    first_name = {
      "type": "function",
      "function": {
        "name": "handle_first_name",
        "description": "Use this function to verify the user's first name.",
        "parameters": {
            "type": "object",
            "properties": {
                "first_name": {
                    "type": "string",
                    "description": "The user's first name.",
                }
            },
        },
      }
    }
    
    last_name = {
      "type": "function",
      "function": {
        "name": "handle_last_name",
        "description": "Once the user gives his last name, call the handle_last_name function.",
        "parameters": {
            "type": "object",
            "properties": {
                "last_name": {
                    "type": "string",
                    "description": "The user's last name.",
                }
            },
        },
      },
    }
    
