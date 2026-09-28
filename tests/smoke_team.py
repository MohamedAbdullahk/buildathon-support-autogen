import asyncio

from backend.agents.support_team import build_support_team


async def main():
    team, model_client = build_support_team()
    try:
        result = await team.run(task="How do I reset my password?")
        for msg in result.messages:
            print(f"--- {msg.source} ({type(msg).__name__})")
        print("\nStop reason:", result.stop_reason)
    finally:
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())