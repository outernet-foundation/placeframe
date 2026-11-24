from __future__ import annotations

import pytest
from lease_server.routers.queue_state import NON_ACTIVE_STATUSES, get_queue_state
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import Select


class StubResult:
    def __init__(self, count: int) -> None:
        self._count = count

    def scalar_one(self) -> int:
        return self._count


class StubSession:
    def __init__(self, counts: list[int]) -> None:
        self._counts = counts
        self.statements: list[Select[tuple[int]]] = []

    async def execute(self, statement: Select[tuple[int]]) -> StubResult:
        self.statements.append(statement)
        return StubResult(self._counts.pop(0))


def _rendered(statement: Select[tuple[int]]) -> str:
    return str(statement.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


def test_non_active_statuses_are_terminal_queued_and_paused() -> None:
    assert {status.value for status in NON_ACTIVE_STATUSES} == {"succeeded", "failed", "queued", "paused"}


@pytest.mark.asyncio
async def test_reports_both_counts() -> None:
    session = StubSession([3, 2])

    state = await get_queue_state.fn(session=session)

    assert state.queued == 3
    assert state.in_flight == 2


@pytest.mark.asyncio
async def test_zero_state() -> None:
    session = StubSession([0, 0])

    state = await get_queue_state.fn(session=session)

    assert state.queued == 0
    assert state.in_flight == 0


@pytest.mark.asyncio
async def test_queued_count_filters_on_the_queued_status() -> None:
    session = StubSession([0, 0])

    await get_queue_state.fn(session=session)

    clause = _rendered(session.statements[0])
    assert "'queued'" in clause, f"queued predicate must target the queued status: {clause}"
    assert "'succeeded'" not in clause
    assert "'paused'" not in clause


@pytest.mark.asyncio
async def test_in_flight_count_excludes_terminal_queued_and_paused() -> None:
    session = StubSession([0, 0])

    await get_queue_state.fn(session=session)

    clause = _rendered(session.statements[1])
    for value in ("'succeeded'", "'failed'", "'queued'", "'paused'"):
        assert value in clause, f"in_flight predicate must exclude {value}: {clause}"
