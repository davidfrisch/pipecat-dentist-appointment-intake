

class IntakeContactDetailsTools():
    first_name = {
      "type": "function",
      "function": {
        "name": "handle_first_name",
        "description": "Once the user gives his first name, call the handle_first_name function.",
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
    
