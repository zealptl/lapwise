"""Service for computing qualifying performance trends for a single driver."""

import asyncio

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.analysis.qualifying_trends import (
    QualifyingTrends,
    SectorDominance,
    SectorStats,
)
from lapwise.models.championship import ChampionshipDriver
from lapwise.models.laps import Lap
from lapwise.models.sessions import Session
from lapwise.models.starting_grid import StartingGridEntry
from lapwise.services.analysis.common import get_last_n_meeting_keys, get_sessions_for_meetings

_DECAY = 0.85


def _decay_weighted_avg(values: list[float]) -> float | None:
    """Compute a decay-weighted average.

    Index 0 is the *most recent* observation (weight = 1.0).
    Each subsequent older observation is multiplied by an additional factor of
    ``_DECAY``.
    """
    if not values:
        return None
    total_weight = 0.0
    total = 0.0
    for i, v in enumerate(values):
        w = _DECAY ** i
        total += v * w
        total_weight += w
    return total / total_weight


class QualifyingTrendsService:
    """Compute qualifying trend metrics for a given driver."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def get_qualifying_trends(
        self,
        driver_number: int,
        last_n_races: int = 12,
        include_circuit_history: bool = False,  # no-op for this endpoint (no session_key)
    ) -> QualifyingTrends:
        """Return qualifying trends for *driver_number* across recent meetings.

        Args:
            driver_number: Car number of the driver to analyse.
            last_n_races: Number of most-recent race weekends to include.
            include_circuit_history: Accepted but currently a no-op for this
                endpoint because no ``session_key`` / ``circuit_key`` is
                available to scope history.

        Returns:
            A :class:`QualifyingTrends` instance populated with all metrics.
        """
        # 1. Resolve meeting keys (descending – most recent first)
        meeting_keys = await get_last_n_meeting_keys(self._client, last_n_races)

        # 2. Fetch qualifying sessions for those meetings
        sessions: list[Session] = await get_sessions_for_meetings(
            self._client, meeting_keys, ["Qualifying"]
        )

        # Order ascending by date for trend calculation (oldest → newest)
        sessions.sort(
            key=lambda s: s.date_start if s.date_start is not None else __import__("datetime").datetime.min
        )

        if not sessions:
            return QualifyingTrends(
                driver_number=driver_number,
                sessions_analysed=0,
                sector_dominance=SectorDominance(
                    sector_1=SectorStats(),
                    sector_2=SectorStats(),
                    sector_3=SectorStats(),
                ),
            )

        # 3-4. Fetch grid positions for each session in parallel
        async def fetch_grid(s: Session) -> list[StartingGridEntry]:
            return await self._client.get(
                "starting_grid", StartingGridEntry, session_key=s.session_key
            )

        # 5. Fetch laps for sector analysis in parallel
        async def fetch_laps(s: Session) -> list[Lap]:
            return await self._client.get("laps", Lap, session_key=s.session_key)

        # 6. Fetch championship standings per meeting
        async def fetch_champ(mk: int) -> list[ChampionshipDriver]:
            return await self._client.get(
                "championship_drivers",
                ChampionshipDriver,
                meeting_key=mk,
                driver_number=driver_number,
            )

        grid_results, lap_results, champ_results = await asyncio.gather(
            asyncio.gather(*[fetch_grid(s) for s in sessions]),
            asyncio.gather(*[fetch_laps(s) for s in sessions]),
            asyncio.gather(*[fetch_champ(s.meeting_key) for s in sessions]),
        )

        # ------------------------------------------------------------------ #
        # Grid position metrics
        # ------------------------------------------------------------------ #
        # Build list of grid positions, most-recent last (sessions are asc)
        # We want index 0 = most recent for decay weighting, so reverse.
        grid_entries: list[int] = []  # ascending (oldest first)
        session_has_grid: list[bool] = []

        for entries in grid_results:
            driver_entry = next(
                (e for e in entries if e.driver_number == driver_number), None
            )
            if driver_entry is not None:
                grid_entries.append(driver_entry.position)
                session_has_grid.append(True)
            else:
                session_has_grid.append(False)

        # Reverse for decay weighting (index 0 = most recent)
        positions_for_decay = list(reversed(grid_entries))
        avg_grid = _decay_weighted_avg([float(p) for p in positions_for_decay])
        best_grid = min(grid_entries) if grid_entries else None
        worst_grid = max(grid_entries) if grid_entries else None

        n_with_entry = len(grid_entries)
        q3_rate = (
            sum(1 for p in grid_entries if p <= 10) / n_with_entry
            if n_with_entry > 0
            else None
        )
        q2_rate = (
            sum(1 for p in grid_entries if p <= 15) / n_with_entry
            if n_with_entry > 0
            else None
        )

        # ------------------------------------------------------------------ #
        # Sector dominance (task 9.2)
        # ------------------------------------------------------------------ #
        sector_attrs = [
            ("duration_sector_1", "s1"),
            ("duration_sector_2", "s2"),
            ("duration_sector_3", "s3"),
        ]

        # Per-sector accumulators: list of (driver_best, field_min) pairs
        sector_deltas: dict[str, list[float]] = {"s1": [], "s2": [], "s3": []}
        sector_dominated: dict[str, int] = {"s1": 0, "s2": 0, "s3": 0}
        sector_sessions_with_data: dict[str, int] = {"s1": 0, "s2": 0, "s3": 0}

        for laps in lap_results:
            for attr, key in sector_attrs:
                all_values = [
                    getattr(lap, attr)
                    for lap in laps
                    if getattr(lap, attr) is not None
                ]
                total_laps = len(laps)
                null_count = total_laps - len(all_values)

                # Skip session if >50% of laps have null sector time
                if total_laps == 0 or null_count > total_laps / 2:
                    continue

                field_min = min(all_values)

                driver_values = [
                    getattr(lap, attr)
                    for lap in laps
                    if lap.driver_number == driver_number
                    and getattr(lap, attr) is not None
                ]
                if not driver_values:
                    continue

                driver_best = min(driver_values)
                delta = driver_best - field_min
                sector_deltas[key].append(delta)
                sector_sessions_with_data[key] += 1

                if driver_best == field_min:
                    sector_dominated[key] += 1

        def _sector_stats(key: str) -> SectorStats:
            deltas = sector_deltas[key]
            sessions_with = sector_sessions_with_data[key]
            avg_delta = (sum(deltas) / len(deltas)) if deltas else None
            dominance = (sector_dominated[key] / sessions_with) if sessions_with > 0 else None
            return SectorStats(avg_delta_to_fastest=avg_delta, dominance_rate=dominance)

        s1_stats = _sector_stats("s1")
        s2_stats = _sector_stats("s2")
        s3_stats = _sector_stats("s3")

        # Strongest sector = smallest avg_delta_to_fastest
        candidates: list[tuple[int, float]] = []
        for idx, stats in enumerate([s1_stats, s2_stats, s3_stats], start=1):
            if stats.avg_delta_to_fastest is not None:
                candidates.append((idx, stats.avg_delta_to_fastest))
        strongest_sector = min(candidates, key=lambda x: x[1])[0] if candidates else None

        # ------------------------------------------------------------------ #
        # Grid vs expected (championship position at time of qualifying)
        # ------------------------------------------------------------------ #
        # Map meeting_key → championship position
        champ_pos_by_meeting: dict[int, int] = {}
        for s, champ_list in zip(sessions, champ_results):
            if champ_list:
                champ_pos_by_meeting[s.meeting_key] = champ_list[0].position_current

        grid_vs_expected_deltas: list[float] = []
        grid_entry_idx = 0
        for i, s in enumerate(sessions):
            if not session_has_grid[i]:
                continue
            grid_pos = grid_entries[grid_entry_idx]
            grid_entry_idx += 1
            champ_pos = champ_pos_by_meeting.get(s.meeting_key)
            if champ_pos is not None:
                grid_vs_expected_deltas.append(grid_pos - champ_pos)

        grid_vs_expected = (
            sum(grid_vs_expected_deltas) / len(grid_vs_expected_deltas)
            if grid_vs_expected_deltas
            else None
        )

        # ------------------------------------------------------------------ #
        # Recent trend
        # ------------------------------------------------------------------ #
        recent_trend: str | None = None
        if len(positions_for_decay) >= 2:
            mid = len(positions_for_decay) // 2
            # positions_for_decay is most-recent first; "newer half" = indices 0..mid-1
            newer = positions_for_decay[:mid]
            older = positions_for_decay[mid:]
            newer_avg = _decay_weighted_avg([float(p) for p in newer])
            older_avg = _decay_weighted_avg([float(p) for p in older])
            if newer_avg is not None and older_avg is not None and older_avg > 0:
                ratio = newer_avg / older_avg
                if ratio < 0.90:
                    recent_trend = "IMPROVING"
                elif ratio > 1.10:
                    recent_trend = "DECLINING"
                else:
                    recent_trend = "STABLE"

        return QualifyingTrends(
            driver_number=driver_number,
            sessions_analysed=len(sessions),
            avg_grid_position=avg_grid,
            best_grid_position=best_grid,
            worst_grid_position=worst_grid,
            q3_appearance_rate=q3_rate,
            q2_appearance_rate=q2_rate,
            sector_dominance=SectorDominance(
                sector_1=s1_stats,
                sector_2=s2_stats,
                sector_3=s3_stats,
            ),
            strongest_sector=strongest_sector,
            grid_vs_expected=grid_vs_expected,
            recent_trend=recent_trend,
        )
