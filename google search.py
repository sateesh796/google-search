
"""Google Search agent for current news and up-to-date information."""
import argparse
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types

load_dotenv(Path(__file__).with_name(".env"))

root_agent = Agent(
    name="google_search_agent",
    model="gemini-2.5-flash",
    tools=[google_search],
    instruction=(
        "Answer questions helpfully and accurately. For current news, recent events, "
        "or information that may have changed, search Google before answering. "
        "Use the newest reliable sources available, state publication dates when "
        "relevant, and cite sources with links. If sources conflict or a fact cannot "
        "be verified, say so clearly. Never present outdated knowledge as current."
    ),
)

agent = root_agent


async def search_and_print(query: str) -> None:
    app_name = root_agent.name
    user_id = "console_user"
    session_id = "console_session"
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
    runner = Runner(
        agent=root_agent,
        app_name=app_name,
        session_service=session_service,
    )
    message = types.Content(role="user", parts=[types.Part(text=query)])

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message,
    ):
        if event.is_final_response() and event.content:
            answer = "\n".join(
                part.text for part in event.content.parts if part.text
            ).strip()
            if answer:
                print(answer)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search Google for current information and print the answer."
    )
    parser.add_argument("query", nargs="*", help="The topic or question to search")
    args = parser.parse_args()

    initial_query = " ".join(args.query).strip()
    if initial_query:
        queries = [initial_query]
    else:
        queries = []

    while True:
        if queries:
            query = queries.pop(0)
        else:
            query = input("What should I search for? ").strip()
            if not query:
                continue

        if query.lower() in {"exit", "quit", "q"}:
            break

        asyncio.run(search_and_print(query))


if __name__ == "__main__":
    main()


