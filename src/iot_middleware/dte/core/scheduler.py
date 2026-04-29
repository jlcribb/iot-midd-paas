"""Priority scheduler for periodic and event-triggered tasks."""

from __future__ import annotations

import heapq
import itertools
import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Optional


class TaskPriority(IntEnum):
    HIGH = 0
    MEDIUM = 1
    LOW = 2


TaskCallback = Callable[..., Any]


@dataclass(order=True)
class ScheduledTask:
    sort_index: tuple[float, int, int] = field(init=False, repr=False)
    next_run: float
    priority: TaskPriority
    sequence: int
    name: str = field(compare=False)
    callback: TaskCallback = field(compare=False)
    interval_seconds: Optional[float] = field(default=None, compare=False)
    event_types: Optional[set[str]] = field(default=None, compare=False)
    entity_id: Optional[str] = field(default=None, compare=False)
    enabled: bool = field(default=True, compare=False)

    def __post_init__(self) -> None:
        self.sort_index = (self.next_run, int(self.priority), self.sequence)

    def update_sort_index(self) -> None:
        self.sort_index = (self.next_run, int(self.priority), self.sequence)


class PriorityScheduler:
    """Runs high-priority tasks first when tasks share the same due timestamp."""

    def __init__(self) -> None:
        self._counter = itertools.count(1)
        self._periodic_heap: list[ScheduledTask] = []
        self._event_tasks: list[ScheduledTask] = []

    def add_periodic_task(
        self,
        name: str,
        interval_seconds: float,
        callback: TaskCallback,
        priority: TaskPriority = TaskPriority.MEDIUM,
        start_immediately: bool = True,
    ) -> ScheduledTask:
        now = time.monotonic()
        next_run = now if start_immediately else now + interval_seconds
        task = ScheduledTask(
            name=name,
            next_run=next_run,
            priority=priority,
            sequence=next(self._counter),
            callback=callback,
            interval_seconds=interval_seconds,
        )
        heapq.heappush(self._periodic_heap, task)
        return task

    def add_event_task(
        self,
        name: str,
        event_types: set[str],
        callback: TaskCallback,
        priority: TaskPriority = TaskPriority.MEDIUM,
        entity_id: Optional[str] = None,
    ) -> ScheduledTask:
        task = ScheduledTask(
            name=name,
            next_run=0.0,
            priority=priority,
            sequence=next(self._counter),
            callback=callback,
            event_types=event_types,
            entity_id=entity_id,
        )
        self._event_tasks.append(task)
        return task

    def cancel(self, task: ScheduledTask) -> None:
        task.enabled = False

    def due_periodic_tasks(self, now_monotonic: Optional[float] = None) -> list[ScheduledTask]:
        now = time.monotonic() if now_monotonic is None else now_monotonic
        due: list[ScheduledTask] = []
        while self._periodic_heap and self._periodic_heap[0].next_run <= now:
            task = heapq.heappop(self._periodic_heap)
            if task.enabled:
                due.append(task)
        due.sort(key=lambda item: (int(item.priority), item.sequence))
        return due

    def reschedule_periodic(self, task: ScheduledTask, now_monotonic: Optional[float] = None) -> None:
        if not task.enabled or task.interval_seconds is None:
            return
        now = time.monotonic() if now_monotonic is None else now_monotonic
        task.next_run = now + task.interval_seconds
        task.update_sort_index()
        heapq.heappush(self._periodic_heap, task)

    def tasks_for_event(self, event_type: str, entity_id: Optional[str]) -> list[ScheduledTask]:
        matched: list[ScheduledTask] = []
        for task in self._event_tasks:
            if not task.enabled or not task.event_types:
                continue
            if event_type not in task.event_types:
                continue
            if task.entity_id and task.entity_id != entity_id:
                continue
            matched.append(task)
        matched.sort(key=lambda item: (int(item.priority), item.sequence))
        return matched
