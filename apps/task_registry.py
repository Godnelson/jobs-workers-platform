from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable


TaskCallable = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


async def task_echo(payload: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "echo": payload}


async def task_sleep(payload: dict[str, Any]) -> dict[str, Any]:
    seconds = float(payload.get("seconds", 1))
    await asyncio.sleep(seconds)
    return {"ok": True, "slept": seconds}


TASKS: dict[str, TaskCallable] = {
    "echo": task_echo,
    "sleep": task_sleep,
}


def get_task(task_name: str) -> TaskCallable | None:
    return TASKS.get(task_name)


def list_task_names() -> list[str]:
    return sorted(TASKS.keys())
