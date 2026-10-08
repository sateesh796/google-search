from pathlib import Path

from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentServer, AgentSession, Agent, inference, room_io, TurnHandlingOptions

try:
    from livekit.plugins import ai_coustics
except ImportError:  # pragma: no cover - optional dependency for noise cancellation
    ai_coustics = None  # type: ignore[assignment]

load_dotenv(Path(__file__).with_name(".env"))


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice AI assistant.
            Be a warm, attentive personal assistant for relaxed, everyday conversation.
            Listen closely, respond naturally, and keep most replies brief enough to sound comfortable aloud.
            Make room for casual small talk, follow up on details the user has shared in this conversation,
            and ask one gentle question at a time when it helps keep the conversation going.
            Help with simple brainstorming, explanations, choices, and planning. Be supportive without
            pretending to be a therapist, and be honest when you do not know something.
            Do not claim to remember past sessions or to perform actions such as setting reminders unless
            a tool actually allows it. Avoid lists, markdown, emojis, and decorative punctuation unless
            the user asks for them.""",
        )

server = AgentServer()

@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: agents.JobContext):
    session = AgentSession(
        stt=inference.STT(model="assemblyai/universal-3-5-pro", language="en"),
        llm=inference.LLM(model="google/gemma-4-31b-it"),
        tts=inference.TTS(
            model="fishaudio/s2.1-pro",
            voice="fa4c9eb3dccc4806b382b40d61c6b10a",
        ),
        turn_handling=TurnHandlingOptions(
            turn_detection="stt",
        ),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=ai_coustics.audio_enhancement(model=ai_coustics.EnhancerModel.QUAIL_VF_S),
            ),
        ),
    )

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    agents.cli.run_app(server)