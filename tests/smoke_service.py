import asyncio

from backend.services.support_service import run_support_query


async def main():
    result = await run_support_query("who is the CM of tamilnadu now?")

    print("\n🧠 ASSISTANT ANSWER:\n", result.assistant_answer)
    print("\n🌐 WEB ANSWER:\n", result.web_answer)
    print("\n⏱️ Duration:", result.duration_seconds, "seconds")
    print("🔎 Search context length:", len(result.search_context), "chars")
    print("🧾 Trace items:", len(result.trace))
    print("🛑 Stop reason:", result.stop_reason)


if __name__ == "__main__":
    asyncio.run(main())