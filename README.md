# Project Overview - Appointment Scheduling Chatbot with Pipecat

## Description
This project demonstrates an AI-driven appointment scheduling system. It includes:
• Google Calendar integration for scheduling
• Azure-based speech recognition and text-to-speech
• OpenAI-based language models for conversation
• Daily.co integration for real-time audio/video interactions

## Requirements
- Python 3.10+
- Google Cloud Console account
- Azure Speech Services account
- OpenAI account
- Daily.co account
- Google Calendar account

Visit the pipecat repository for more information on the pipeline framework:
- [pipecat](https://docs.pipecat.ai/getting-started/overview)

Visit the gcsa documentation for more information on the Google Calendar API:
- [gcsa](https://google-calendar-simple-api.readthedocs.io/en/latest/getting_started.html#installation)


## Setup
1. Create a virtual environment and install required packages.
   ```
      pip install -r requirements.txt
    ```


2. Provide your credentials in the .env and credentials.json files (keep them private) at the root of the project.
    ```
    # .env file
    AZURE_SPEECH_API_KEY=<token>
    AZURE_SPEECH_REGION=<token>
    DAILY_API_KEY=<token>
    DAILY_SAMPLE_ROOM_URL=<token>
    OPENAI_API_KEY=<token>
  ```
  - For Google Calendar, download the credentials.json file from the Google Cloud Console and place it in the root of the project.

3. Run the bot with:
  ```
  python bot.py
  ```

## Key Components
• services/: Contains appointment logic and tools for handling scheduling details.  
• runner.py: Configures environment and tokens for daily.co usage.  
• bot.py: Main entry point, orchestrates the pipeline and runs the chatbot.

## Usage
After starting the application, a call session is launched where the system interacts via speech and text, scheduling appointments in a conversation flow. The pipeline ensures language function calls, TTS responses, and meeting creation on Google Calendar.
