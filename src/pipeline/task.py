import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskResult:
    status: TaskStatus
    output: Any = None
    error: str | None = None
    duration_seconds: float = 0.0


@dataclass
class Task:
    """A single unit of work in an ML pipeline."""

    name: str
    func: Callable[..., Any]
    dependencies: list[str] = field(default_factory=list)
    retries: int = 0
    timeout_seconds: int = 600
    status: TaskStatus = TaskStatus.PENDING
    result: TaskResult | None = None

    def execute(self, context: dict[str, Any]) -> TaskResult:
        """Run the task function with pipeline context."""
        start = time.time()
        attempts = 0

        while attempts <= self.retries:
            try:
                self.status = TaskStatus.RUNNING
                output = self.func(context)
                duration = time.time() - start
                self.result = TaskResult(
                    status=TaskStatus.COMPLETED,
                    output=output,
                    duration_seconds=duration,
                )
                self.status = TaskStatus.COMPLETED
                return self.result
            except Exception as e:
                attempts += 1
                if attempts > self.retries:
                    duration = time.time() - start
                    self.result = TaskResult(
                        status=TaskStatus.FAILED,
                        error=str(e),
                        duration_seconds=duration,
                    )
                    self.status = TaskStatus.FAILED
                    return self.result

        return TaskResult(status=TaskStatus.FAILED, error="Unknown error")
