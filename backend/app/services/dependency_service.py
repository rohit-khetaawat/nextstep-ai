"""Deterministic dependency-graph logic for tasks.

Dependencies are directed edges: (task_id -> depends_on_task_id) meaning
task_id cannot start until depends_on_task_id is COMPLETED.
"""

from collections import defaultdict, deque


class CycleDetectedError(Exception):
    pass


def validate_edges(task_ids: set[int], edges: list[tuple[int, int]]) -> None:
    """Ensure every edge references a real task and no self-dependency exists."""

    for task_id, depends_on in edges:
        if task_id not in task_ids or depends_on not in task_ids:
            raise ValueError(f"Dependency edge references an unknown task: {task_id} -> {depends_on}")
        if task_id == depends_on:
            raise ValueError(f"Task {task_id} cannot depend on itself.")


def has_cycle(task_ids: set[int], edges: list[tuple[int, int]]) -> bool:
    graph: dict[int, list[int]] = defaultdict(list)
    for task_id, depends_on in edges:
        graph[task_id].append(depends_on)

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {tid: WHITE for tid in task_ids}

    def visit(node: int) -> bool:
        color[node] = GRAY
        for neighbor in graph.get(node, []):
            if color.get(neighbor, WHITE) == GRAY:
                return True
            if color.get(neighbor, WHITE) == WHITE and visit(neighbor):
                return True
        color[node] = BLACK
        return False

    return any(color[tid] == WHITE and visit(tid) for tid in task_ids)


def topological_order(task_ids: set[int], edges: list[tuple[int, int]]) -> list[int]:
    """Return task ids ordered so every dependency precedes its dependents.

    Raises CycleDetectedError if the graph is not a DAG.
    """

    if has_cycle(task_ids, edges):
        raise CycleDetectedError("Dependency graph contains a cycle.")

    # in_degree counts incoming "depended upon by" edges for Kahn's algorithm,
    # where we process a depends_on target only after all its dependents... but
    # for scheduling we want depends_on completed first, so build the reverse
    # graph: edge depends_on -> task_id means depends_on must come first.
    graph: dict[int, list[int]] = defaultdict(list)
    in_degree: dict[int, int] = {tid: 0 for tid in task_ids}
    for task_id, depends_on in edges:
        graph[depends_on].append(task_id)
        in_degree[task_id] += 1

    queue = deque(sorted(tid for tid in task_ids if in_degree[tid] == 0))
    order: list[int] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in sorted(graph.get(node, [])):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(task_ids):
        raise CycleDetectedError("Dependency graph contains a cycle.")
    return order


def unblocked_counts(task_ids: set[int], edges: list[tuple[int, int]]) -> dict[int, int]:
    """For each task, how many other tasks directly depend on it completing."""

    counts = {tid: 0 for tid in task_ids}
    for _task_id, depends_on in edges:
        counts[depends_on] = counts.get(depends_on, 0) + 1
    return counts


def is_blocked(task_id: int, edges: list[tuple[int, int]], completed_ids: set[int]) -> bool:
    prerequisites = [dep for tid, dep in edges if tid == task_id]
    return any(dep not in completed_ids for dep in prerequisites)
