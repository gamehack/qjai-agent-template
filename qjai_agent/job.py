"""Business logic; intentionally independent of the execution platform."""
import os


def execute(mode: str, prompt: str) -> str:
    if mode == "smoke":
        return "qjai-agent-template smoke test OK"
    if mode != "live":
        raise ValueError("unsupported AGENT_MODE")
    model = os.environ.get("OPENAI_MODEL")
    if not model or not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_MODEL and OPENAI_API_KEY are required in live mode")

    from agents import Agent, Runner

    agent = Agent(
        name="QJAI Example Agent",
        instructions="Return a concise response to the supplied task.",
        model=model,
    )
    result = Runner.run_sync(agent, prompt, max_turns=5)
    return str(result.final_output)
