"""Business logic; intentionally independent of the execution platform."""
import os


def execute_with_metrics(mode: str, prompt: str) -> tuple[str, dict]:
    if mode == "smoke":
        return "qjai-agent-template smoke test OK", {
            "requests": 0, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
        }
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
    usage = result.context_wrapper.usage
    return str(result.final_output), {
        name: getattr(usage, name, None)
        for name in ("requests", "input_tokens", "output_tokens", "total_tokens")
    }


def execute(mode: str, prompt: str) -> str:
    return execute_with_metrics(mode, prompt)[0]
