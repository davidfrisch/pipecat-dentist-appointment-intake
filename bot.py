

import asyncio
import os
import sys

import aiohttp
from dotenv import load_dotenv
from loguru import logger
from runner import configure
from services.IntakeProcessor import IntakeProcessor

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.pipeline.parallel_pipeline import ParallelPipeline
from pipecat.services.azure import AzureTTSService, AzureSTTService, Language
from pipecat.services.openai import OpenAILLMContext, OpenAILLMContextFrame, OpenAILLMService
from pipecat.processors.logger import FrameLogger
from pipecat.processors.filters.function_filter import FunctionFilter
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.audio.vad.silero import SileroVADAnalyzer

load_dotenv(override=True)

logger.remove(0)
logger.add(sys.stderr, level="DEBUG")


async def main(current_language="english"):
    async with aiohttp.ClientSession() as session:
        (room_url, token) = await configure(session)

        transport = DailyTransport(
            room_url,
            token,
            "Chatbot",
            DailyParams(
                audio_out_enabled=True,
                vad_enabled=True,
                vad_analyzer=SileroVADAnalyzer(),
                vad_audio_passthrough=True,
            ),
        )
        
        french_sst = AzureSTTService(
            api_key=os.getenv("AZURE_SPEECH_API_KEY"),
            region=os.getenv("AZURE_SPEECH_REGION"),
            language="fr-FR",
        )
        
        english_sst = AzureSTTService(
            api_key=os.getenv("AZURE_SPEECH_API_KEY"),
            region=os.getenv("AZURE_SPEECH_REGION"),
            language="en-US",
        )
        
        llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o-mini")

        french_tts = AzureTTSService(
            api_key=os.getenv("AZURE_SPEECH_API_KEY"),
            region=os.getenv("AZURE_SPEECH_REGION"),
            voice="fr-FR-HenriNeural",
            params=AzureTTSService.InputParams(
                language=Language.FR,
            )
        )
        
        english_tts = AzureTTSService(
            api_key=os.getenv("AZURE_SPEECH_API_KEY"),
            region=os.getenv("AZURE_SPEECH_REGION"),
        )
        
        messages = []
        context = OpenAILLMContext(messages=messages)
        context_aggregator = llm.create_context_aggregator(context)

        intake = IntakeProcessor(context)

        llm.register_function("handle_switch_language", intake.handle_switch_language)
        llm.register_function("handle_first_name", intake.handle_first_name)
        llm.register_function("handle_last_name", intake.handle_last_name)
        llm.register_function("handle_reason_for_appointment", intake.handle_reason_for_appointment)
        llm.register_function("handle_appointment_date_schedule", intake.handle_appointment_date_schedule)
        llm.register_function("handle_appointment_time_schedule", intake.handle_appointment_time_schedule)
        llm.register_function("handle_appointment_confirmation", intake.handle_appointment_confirmation)
        llm.register_function("handle_end_call", intake.handle_end_call)
        
        fl = FrameLogger("LLM Output")
        
        pipeline = Pipeline(
            [
                transport.input(), 
                ParallelPipeline(  # STT (bot will listen in the chosen language)
                    [FunctionFilter(intake.english_filter), english_sst],
                    [FunctionFilter(intake.french_filter), french_sst],  
                ),
                context_aggregator.user(), 
                llm, 
                # fl, 
                ParallelPipeline(  # TTS (bot will speak the chosen language)
                    [FunctionFilter(intake.english_filter), english_tts], 
                    [FunctionFilter(intake.french_filter), french_tts],  
                ),
                transport.output(),  
                context_aggregator.assistant(),  
            ]
        )

        task = PipelineTask(pipeline, PipelineParams(allow_interruptions=True))

        @transport.event_handler("on_first_participant_joined")
        async def on_first_participant_joined(transport, participant):
            await transport.capture_participant_transcription(participant["id"])
            
            await task.queue_frames([OpenAILLMContextFrame(context)])

        runner = PipelineRunner()

        await runner.run(task)


if __name__ == "__main__":
    asyncio.run(main())