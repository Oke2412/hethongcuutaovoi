# -*- coding: utf-8 -*-
"""Offline validation of the deferred-write + streaming turn.

No Neo4j, no Docker, no network: every collaborator is stubbed. It proves three
things the latency work depends on:

1. a write tool emitted by the orchestrator is **queued**, never executed inside
   the reasoning loop;
2. the queued write is applied afterwards by the scribe pass (off critical path);
3. the turn emits ``phase`` → ``loop`` → ``tool`` → ``reasoning`` → ``token``
   events so an SSE transport can stay continuous through the thinking phase.

Run directly (``python tests/test_stream_pipeline.py``) or under pytest.
"""

from __future__ import annotations

import asyncio
import sys
import types
from typing import Any, Dict, List

sys.path.insert(0, ".")


# --------------------------------------------------------------------------- #
# Fakes
# --------------------------------------------------------------------------- #
class _Fn:
    def __init__(self, name: str, arguments: str) -> None:
        self.name = name
        self.arguments = arguments


class _ToolCall:
    def __init__(self, idx: int, name: str, arguments: str) -> None:
        self.id = f"call_{idx}"
        self.type = "function"
        self.function = _Fn(name, arguments)


class _Message:
    def __init__(self, content: str | None = None, tool_calls: List[_ToolCall] | None = None) -> None:
        self.content = content
        self.tool_calls = tool_calls
        self.reasoning_content = None


class _Choice:
    def __init__(self, message: Any) -> None:
        self.message = message
        self.delta = message


class _Response:
    def __init__(self, message: _Message, usage: Any = None) -> None:
        self.choices = [_Choice(message)]
        self.usage = usage


class _StreamChunk:
    def __init__(self, *, reasoning: str | None = None, content: str | None = None) -> None:
        delta = types.SimpleNamespace(reasoning_content=reasoning, content=content)
        self.choices = [types.SimpleNamespace(delta=delta)]


class _AsyncStream:
    def __init__(self, chunks: List[_StreamChunk]) -> None:
        self._chunks = chunks

    def __aiter__(self):
        async def gen():
            for chunk in self._chunks:
                yield chunk

        return gen()


class _FakeCompletions:
    """Scripted orchestrator: 1 read loop, 1 write loop, then terminate."""

    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)

        if kwargs.get("stream"):
            return _AsyncStream(
                [
                    _StreamChunk(reasoning="Suy luận "),
                    _StreamChunk(reasoning="một chút."),
                    _StreamChunk(content="《Xác nhận》 "),
                    _StreamChunk(content="Đã ghi nhận."),
                ]
            )

        loop_index = len([c for c in self.calls if not c.get("stream")])
        if loop_index == 1:
            return _Response(
                _Message(
                    tool_calls=[
                        _ToolCall(1, "search_memory_and_causality", '{"query": "kiem tra", "entities": []}')
                    ]
                )
            )
        if loop_index == 2:
            return _Response(
                _Message(
                    tool_calls=[
                        _ToolCall(2, "update_physical_status", '{"energy": 3, "mood": 2, "health": 4}')
                    ]
                )
            )
        return _Response(_Message(content="TERMINATE_LOOP"))


class _FakeClient:
    def __init__(self) -> None:
        self.chat = types.SimpleNamespace(completions=_FakeCompletions())


# --------------------------------------------------------------------------- #
# Harness
# --------------------------------------------------------------------------- #
async def _run(defer: bool = True) -> None:
    import core.brain as brain_mod
    import core.llm as llm_mod
    import core.search as search_mod

    original_flag = brain_mod.settings.deepseek_defer_writes
    brain_mod.settings.deepseek_defer_writes = defer

    applied: List[tuple[str, dict]] = []
    events: List[dict] = []

    async def _noop_async(*args: Any, **kwargs: Any) -> None:
        return None

    async def _fake_mini_ctx(uid: int) -> str:
        return "[MINI CONTEXT]"

    fake_client = _FakeClient()

    llm_mod._get_llm_client = lambda: fake_client
    llm_mod.query_causal_graph = lambda uid, ents: _value("")
    search_mod.sparse_search = lambda queries, limit=5: _value([])

    import core.omniscience as omniscience_mod

    omniscience_mod.get_mini_context = _fake_mini_ctx
    omniscience_mod.log_message = _noop_async

    import core.llm_tools as tools_mod

    async def _fake_update_physical(uid: int, energy: int, mood: int, health: int, sleep: float, notes: str) -> None:
        applied.append(("update_physical_status", {"energy": energy, "health": health}))

    tools_mod.update_physical_status_async = _fake_update_physical

    # build_hud + Neo4j driver + GDS are infra; stub them out.
    import core.hud as hud_mod

    async def _fake_hud(uid: int):
        return ("⚡E: 90% | 😐M: Calm | ❤️H: 95% | 💎Cr: 0 | 📍H3: 0", None)

    hud_mod.build_hud = _fake_hud

    import core.neo4j_client as neo_mod

    neo_mod.get_neo4j_driver = lambda: None

    import core.gds_service as gds_mod

    async def _fake_gds(uid: int, entities: Any = None) -> str:
        return ""

    gds_mod.GDSService.synthesize_gds_context = staticmethod(_fake_gds)

    brain = brain_mod.RaphaelBrain()
    brain.memory = None
    brain._init_memory = lambda: None  # keep the turn offline and fast

    async def sink(event: dict) -> None:
        events.append(event)

    result = await brain.process_input(
        user_id="1", text_content="hôm nay mệt quá", return_thinking=True, on_event=sink
    )

    # Let the background writes / persist tasks run.
    pending = [t for t in brain_mod.background_tasks if not t.done()]
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)

    brain_mod.settings.deepseek_defer_writes = original_flag

    return result, events, applied, fake_client


def _value(v: Any):
    async def _inner(*args: Any, **kwargs: Any) -> Any:
        return v

    return _inner()


def test_writes_dispatched_async_and_streamed() -> None:
    result, events, applied, fake_client = asyncio.run(_run())

    full_res, keyboard, thinking = result

    # 1. The write turn still happens (the model thinks about what to record)…
    orchestrator_calls = [c for c in fake_client.chat.completions.calls if not c.get("stream")]
    assert len(orchestrator_calls) == 2, len(orchestrator_calls)  # read turn + write turn
    offered = {t["function"]["name"] for c in orchestrator_calls for t in c["tools"]}
    assert "update_physical_status" in offered, "write tools must stay offered to the orchestrator"

    # 2. …but a write-only turn is dispatched, not awaited before Pass 2.
    async_tools = [e for e in events if e.get("type") == "tool" and e.get("status") == "async"]
    assert len(async_tools) == 1, events
    assert "update_physical_status" in async_tools[0]["name"]

    # 3. It still lands (nothing is silently dropped).
    assert applied == [("update_physical_status", {"energy": 3, "health": 4})], applied

    # 4. Progress events arrive in a usable order, and reasoning text never leaks.
    assert events[0]["type"] == "phase" and events[0]["phase"] == "ingress"
    assert any(e.get("type") == "phase" and e.get("phase") == "reasoning" for e in events)
    assert len([e for e in events if e["type"] == "token"]) == 2

    # 5. The answer really streamed (content concatenated from deltas).
    assert "《Xác nhận》" in full_res
    assert "Đã ghi nhận." in full_res
    assert "Suy luận" not in full_res  # reasoning stayed hidden
    forwarded = "".join(e["text"] for e in events if e["type"] == "token")
    assert "Suy luận" not in forwarded

    print("PASS — write turn kept, dispatched async, scribe-free, 2 token frames")


def test_tool_classification() -> None:
    from core.llm import TOOLS_DEF, WRITE_TOOLS

    all_names = {t["function"]["name"] for t in TOOLS_DEF}
    read_names = all_names - set(WRITE_TOOLS)

    assert set(WRITE_TOOLS) <= all_names, all_names - set(WRITE_TOOLS)
    assert not (read_names & set(WRITE_TOOLS)), read_names & set(WRITE_TOOLS)
    assert len(read_names) == 3 and len(WRITE_TOOLS) == 9, (len(read_names), len(WRITE_TOOLS))
    print(f"PASS — {len(read_names)} read tools, {len(WRITE_TOOLS)} write tools, all defined")


def test_sequential_mode_is_original_behaviour() -> None:
    """`DEEPSEEK_DEFER_WRITES=false` must reproduce the pre-change pipeline exactly."""
    result, events, applied, fake_client = asyncio.run(_run(defer=False))
    full_res, keyboard, thinking = result

    orchestrator_calls = [c for c in fake_client.chat.completions.calls if not c.get("stream")]
    assert len(orchestrator_calls) == 3, len(orchestrator_calls)  # read, write inline, terminate

    inline = [
        e
        for e in events
        if e.get("type") == "tool" and e.get("status") == "done" and e.get("name") == "update_physical_status"
    ]
    assert len(inline) == 1, events
    assert not [e for e in events if e.get("status") == "async"]
    assert applied == [("update_physical_status", {"energy": 3, "health": 4})], applied
    assert "《Xác nhận》" in full_res
    print("PASS — sequential mode: write executed inline, loop continued to terminate")


def test_sse_bridge_frames() -> None:
    """The transport keeps the socket alive and mirrors the brain's event stream."""
    import json as _json

    import api.routes.desktop as desktop_mod

    class _FakeBrain:
        async def process_input(self, user_id: str, text_content: str, return_thinking: bool, on_event: Any):
            await on_event({"type": "phase", "phase": "recall", "elapsed_ms": 1})
            await asyncio.sleep(desktop_mod.SSE_HEARTBEAT_SECONDS + 0.15)  # force a heartbeat
            await on_event({"type": "token", "text": "《Xác nhận》 ", "token": "a", "response": "a"})
            return ("《Xác nhận》 Ổn.\n\n━━━━━━━━━━━━━━━━━━━━━\n⚡ 9/10 | 😐 7/10", None, "thinking-text")

    async def collect() -> List[str]:
        return [frame async for frame in desktop_mod._raphael_event_stream("1", "hi")]

    original = desktop_mod.brain
    desktop_mod.brain = _FakeBrain()  # type: ignore[assignment]
    try:
        frames = asyncio.run(collect())
    finally:
        desktop_mod.brain = original  # type: ignore[assignment]

    payloads = [
        _json.loads(frame[len("data: "):]) for frame in frames if frame.startswith("data: ") and "[DONE]" not in frame
    ]

    assert payloads[0]["type"] == "open"
    assert any(p.get("type") == "heartbeat" for p in payloads), payloads
    assert frames[-1] == "data: [DONE]\n\n"

    final = [p for p in payloads if p.get("type") == "final"]
    assert len(final) == 1, payloads
    assert final[0]["text"] == "《Xác nhận》 Ổn."
    assert "⚡ 9/10" in final[0]["hud"]
    assert final[0]["thinking"] == "thinking-text"
    assert all(p.get("text") != "thinking-text" for p in payloads)
    print("PASS — SSE frames: open → heartbeat → token → final → [DONE]")


if __name__ == "__main__":
    test_tool_classification()
    test_writes_dispatched_async_and_streamed()
    test_sequential_mode_is_original_behaviour()
    test_sse_bridge_frames()
