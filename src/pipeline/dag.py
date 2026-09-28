from dataclasses import dataclass, field

from src.pipeline.task import Task


@dataclass
class DAG:
    """Directed Acyclic Graph of pipeline tasks."""

    name: str
    tasks: dict[str, Task] = field(default_factory=dict)

    def add_task(self, task: Task) -> None:
        if task.name in self.tasks:
            raise ValueError(f"Task '{task.name}' already exists")
        self.tasks[task.name] = task

    def validate(self) -> list[str]:
        """Returns list of errors (empty = valid)."""
        errors = []
        for name, task in self.tasks.items():
            for dep in task.dependencies:
                if dep not in self.tasks:
                    errors.append(
                        f"Task '{name}' depends on unknown task '{dep}'"
                    )
        if not errors and self._has_cycle():
            errors.append("DAG contains a cycle")
        return errors

    def topological_sort(self) -> list[list[str]]:
        """Kahn's algorithm. Returns tasks grouped by execution level.

        Tasks in the same level can run in parallel.
        """
        in_degree: dict[str, int] = {name: 0 for name in self.tasks}
        for task in self.tasks.values():
            for dep in task.dependencies:
                if dep in in_degree:
                    in_degree[task.name] += 1

        queue = [n for n, d in in_degree.items() if d == 0]
        levels: list[list[str]] = []

        while queue:
            levels.append(list(queue))
            next_queue = []
            for name in queue:
                for task_name, task in self.tasks.items():
                    if name in task.dependencies:
                        in_degree[task_name] -= 1
                        if in_degree[task_name] == 0:
                            next_queue.append(task_name)
            queue = next_queue

        return levels

    def _has_cycle(self) -> bool:
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(name: str) -> bool:
            visited.add(name)
            rec_stack.add(name)
            for dep in self.tasks[name].dependencies:
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True
            rec_stack.discard(name)
            return False

        for name in self.tasks:
            if name not in visited:
                if dfs(name):
                    return True
        return False

    def get_ready_tasks(self, completed: set[str]) -> list[str]:
        """Get tasks whose dependencies are all completed."""
        ready = []
        for name, task in self.tasks.items():
            if task.status.value != "pending":
                continue
            if all(dep in completed for dep in task.dependencies):
                ready.append(name)
        return ready
