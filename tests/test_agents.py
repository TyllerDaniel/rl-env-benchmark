"""ClaudeAgent is tested against a scripted fake client, so no API key is needed."""

from types import SimpleNamespace

from rlbench.agents import ClaudeAgent, GoldenAgent, NoopAgent, make_agent
from rlbench.sandbox import LocalSandbox


def text_block(text):
    return SimpleNamespace(type="text", text=text)


def tool_block(block_id, command):
    return SimpleNamespace(type="tool_use", id=block_id, input={"command": command})


class FakeClient:
    """Plays back canned responses and records every request."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.requests = []
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        # Snapshot the message list: the agent keeps appending to the same
        # list after the call, while the real SDK serializes it immediately.
        self.requests.append({**kwargs, "messages": list(kwargs["messages"])})
        return self._responses.pop(0)


def test_claude_agent_runs_tool_calls_until_end_turn(tasks):
    client = FakeClient(
        [
            SimpleNamespace(
                stop_reason="tool_use",
                content=[text_block("Let me look."), tool_block("t1", "echo fixed > NOTE.txt && cat NOTE.txt")],
            ),
            SimpleNamespace(stop_reason="end_turn", content=[text_block("Done.")]),
        ]
    )
    agent = ClaudeAgent(model="test-model", client=client)

    with LocalSandbox(tasks[0]) as sb:
        trace = agent.solve(tasks[0], sb)
        assert (sb.workspace / "NOTE.txt").read_text().strip() == "fixed"

    assert trace.steps == 2
    assert len(client.requests) == 2
    assert client.requests[0]["model"] == "test-model"
    assert client.requests[0]["tools"][0]["name"] == "bash"

    # The second request must carry the tool result back to the model.
    tool_result = client.requests[1]["messages"][-1]["content"][0]
    assert tool_result["tool_use_id"] == "t1"
    assert "fixed" in tool_result["content"]
    assert tool_result["is_error"] is False


def test_claude_agent_respects_max_steps(tasks):
    looping = SimpleNamespace(stop_reason="tool_use", content=[tool_block("t", "true")])
    client = FakeClient([looping] * 10)
    agent = ClaudeAgent(model="m", client=client, max_steps=3)
    with LocalSandbox(tasks[0]) as sb:
        trace = agent.solve(tasks[0], sb)
    assert trace.steps == 3


def test_failed_commands_are_flagged(tasks):
    client = FakeClient(
        [
            SimpleNamespace(stop_reason="tool_use", content=[tool_block("t1", "exit 1")]),
            SimpleNamespace(stop_reason="end_turn", content=[text_block("ok")]),
        ]
    )
    with LocalSandbox(tasks[0]) as sb:
        ClaudeAgent(model="m", client=client).solve(tasks[0], sb)
    assert client.requests[1]["messages"][-1]["content"][0]["is_error"] is True


def test_make_agent():
    assert isinstance(make_agent("noop"), NoopAgent)
    assert isinstance(make_agent("golden"), GoldenAgent)
