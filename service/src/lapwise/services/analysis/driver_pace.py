"""Driver pace profile service — Qpace, Rpace, sector deltas, overtake adjustment."""

import asyncio
from datetime import datetime
from statistics import median

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.analysis.driver_pace import DriverPaceProfile
from lapwise.models.laps import Lap
from lapwise.models.session_result import SessionResult
from lapwise.models.sessions import Session
from lapwise.models.starting_grid import StartingGridEntry
from lapwise.models.stints import Stint
from lapwise.services.analysis.common import (
    SC_LAP_EXCLUSION_THRESHOLD,
    get_last_n_meeting_keys,
    get_sessions_for_meetings,
)


class DriverPaceService:
    """Compute a multi-dimensional pace profile for a Formula 1 driver."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def get_driver_pace_profile(
        self,
        driver_number: int,
        last_n_races: int = 12,
        session_key: int | None = None,
        include_circuit_history: bool = False,
    ) -> DriverPaceProfile:
        """Build and return a DriverPaceProfile for the given driver.

        Args:
            driver_number: Car number identifying the driver.
            last_n_races: Number of recent race weekends to include.
            session_key: Optional session key used to resolve the circuit when
                include_circuit_history is True.
            include_circuit_history: When True and session_key is provided, also
                merge meetings from the same circuit in the previous two years.

        Returns:
            A fully populated DriverPaceProfile.
        """
        # ── Step 1: Resolve meeting keys ──────────────────────────────────────
        meeting_keys = await self._resolve_meeting_keys(
            last_n_races, session_key, include_circuit_history
        )

        # ── Step 2–3: Qpace score + trend ─────────────────────────────────────
        qpace_score, qpace_trend, qual_sessions = await self._compute_qpace(
            driver_number, meeting_keys
        )

        # ── Step 4: Sector deltas ─────────────────────────────────────────────
        sector_1_delta, sector_2_delta, sector_3_delta, strongest_sector = (
            await self._compute_sector_deltas(driver_number, qual_sessions)
        )

        # ── Step 5: Rpace ─────────────────────────────────────────────────────
        rpace_score, rpace_percentile = await self._compute_rpace(
            driver_number, meeting_keys
        )

        # ── Step 6: Overtake adjustment ───────────────────────────────────────
        overtake_adjustment = await self._compute_overtake_adjustment(
            driver_number, meeting_keys
        )

        return DriverPaceProfile(
            driver_number=driver_number,
            qpace_score=qpace_score,
            qpace_trend=qpace_trend,
            sector_1_delta=sector_1_delta,
            sector_2_delta=sector_2_delta,
            sector_3_delta=sector_3_delta,
            strongest_sector=strongest_sector,
            rpace_score=rpace_score,
            rpace_percentile=rpace_percentile,
            overtake_adjustment=overtake_adjustment,
            sample_races=len(meeting_keys),
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    async def _resolve_meeting_keys(
        self,
        last_n_races: int,
        session_key: int | None,
        include_circuit_history: bool,
    ) -> list[int]:
        """Return the list of meeting keys to analyse."""
        if include_circuit_history and session_key is not None:
            sessions: list[Session] = await self._client.get(
                "sessions", Session, session_key=session_key
            )
            if sessions:
                circuit_key = sessions[0].circuit_key
                current_year = datetime.now().year
                year_range = (current_year - 2, current_year - 1)
                return await get_last_n_meeting_keys(
                    self._client,
                    last_n_races,
                    circuit_key=circuit_key,
                    year_range=year_range,
                )
        return await get_last_n_meeting_keys(self._client, last_n_races)

    async def _compute_qpace(
        self,
        driver_number: int,
        meeting_keys: list[int],
    ) -> tuple[float, str, list[Session]]:
        """Compute Qpace score and trend. Also returns qualifying sessions for reuse."""
        qual_sessions = await get_sessions_for_meetings(
            self._client, meeting_keys, ["Qualifying"]
        )

        if not qual_sessions:
            return 0.0, "STABLE", []

        # Fetch starting grids concurrently
        grids: list[list[StartingGridEntry]] = await asyncio.gather(
            *[
                self._client.get(
                    "starting_grid", StartingGridEntry, session_key=s.session_key
                )
                for s in qual_sessions
            ]
        )

        # Build scores list, most-recent session first (index 0)
        # Reverse so index 0 = most recent
        sessions_desc = list(reversed(qual_sessions))
        grids_desc = list(reversed(grids))

        scores: list[float] = []
        for session, grid in zip(sessions_desc, grids_desc):
            driver_entries = [e for e in grid if e.driver_number == driver_number]
            if driver_entries:
                position = driver_entries[0].position
                score = max(0, 21 - position)
            else:
                score = 0
            scores.append(float(score))

        decay = 0.85
        weights = [decay**i for i in range(len(scores))]
        total_weight = sum(weights)

        if total_weight == 0:
            qpace_score = 0.0
        else:
            weighted_sum = sum(s * w for s, w in zip(scores, weights))
            qpace_score = min(100.0, max(0.0, (weighted_sum / total_weight) * 5))

        # Trend: split into first-half (older) and second-half (newer, incl. middle if odd)
        n = len(scores)
        mid = n // 2

        if n < 2:
            qpace_trend = "STABLE"
        else:
            # scores[0] = most-recent; second_half = newer (lower indices)
            if n % 2 == 0:
                second_half_scores = scores[:mid]
                first_half_scores = scores[mid:]
            else:
                second_half_scores = scores[: mid + 1]
                first_half_scores = scores[mid + 1 :]

            second_half_weights = [decay**i for i in range(len(second_half_scores))]
            first_half_weights = [decay**i for i in range(len(first_half_scores))]

            def _wavg(sc: list[float], ws: list[float]) -> float:
                tw = sum(ws)
                return sum(s * w for s, w in zip(sc, ws)) / tw if tw else 0.0

            second_avg = _wavg(second_half_scores, second_half_weights)
            first_avg = _wavg(first_half_scores, first_half_weights)

            if first_avg == 0:
                qpace_trend = "STABLE"
            elif second_avg > first_avg * 1.10:
                qpace_trend = "IMPROVING"
            elif second_avg < first_avg * 0.90:
                qpace_trend = "DECLINING"
            else:
                qpace_trend = "STABLE"

        return qpace_score, qpace_trend, qual_sessions

    async def _compute_sector_deltas(
        self,
        driver_number: int,
        qual_sessions: list[Session],
    ) -> tuple[float | None, float | None, float | None, str | None]:
        """Compute average sector deltas vs session bests across qualifying sessions."""
        if not qual_sessions:
            return None, None, None, None

        all_laps: list[list[Lap]] = await asyncio.gather(
            *[
                self._client.get("laps", Lap, session_key=s.session_key)
                for s in qual_sessions
            ]
        )

        s1_deltas: list[float] = []
        s2_deltas: list[float] = []
        s3_deltas: list[float] = []

        for laps in all_laps:
            # Field minimums
            field_s1 = [l.duration_sector_1 for l in laps if l.duration_sector_1 is not None]
            field_s2 = [l.duration_sector_2 for l in laps if l.duration_sector_2 is not None]
            field_s3 = [l.duration_sector_3 for l in laps if l.duration_sector_3 is not None]

            # Driver bests
            driver_laps = [l for l in laps if l.driver_number == driver_number]
            drv_s1 = [
                l.duration_sector_1 for l in driver_laps if l.duration_sector_1 is not None
            ]
            drv_s2 = [
                l.duration_sector_2 for l in driver_laps if l.duration_sector_2 is not None
            ]
            drv_s3 = [
                l.duration_sector_3 for l in driver_laps if l.duration_sector_3 is not None
            ]

            if field_s1 and drv_s1:
                s1_deltas.append(min(drv_s1) - min(field_s1))
            if field_s2 and drv_s2:
                s2_deltas.append(min(drv_s2) - min(field_s2))
            if field_s3 and drv_s3:
                s3_deltas.append(min(drv_s3) - min(field_s3))

        avg_s1 = sum(s1_deltas) / len(s1_deltas) if s1_deltas else None
        avg_s2 = sum(s2_deltas) / len(s2_deltas) if s2_deltas else None
        avg_s3 = sum(s3_deltas) / len(s3_deltas) if s3_deltas else None

        # Strongest sector = smallest average delta (driver closest to field best)
        candidates: list[tuple[float, str]] = []
        if avg_s1 is not None:
            candidates.append((avg_s1, "S1"))
        if avg_s2 is not None:
            candidates.append((avg_s2, "S2"))
        if avg_s3 is not None:
            candidates.append((avg_s3, "S3"))

        strongest_sector: str | None = (
            min(candidates, key=lambda x: x[0])[1] if candidates else None
        )

        return avg_s1, avg_s2, avg_s3, strongest_sector

    async def _compute_rpace(
        self,
        driver_number: int,
        meeting_keys: list[int],
    ) -> tuple[float | None, float | None]:
        """Compute Rpace score and percentile vs field."""
        race_sessions = await get_sessions_for_meetings(
            self._client, meeting_keys, ["Race"]
        )

        if not race_sessions:
            return None, None

        # Fetch all data for all race sessions concurrently
        driver_laps_futures = [
            self._client.get("laps", Lap, session_key=s.session_key, driver_number=driver_number)
            for s in race_sessions
        ]
        all_laps_futures = [
            self._client.get("laps", Lap, session_key=s.session_key)
            for s in race_sessions
        ]
        stints_futures = [
            self._client.get(
                "stints", Stint, session_key=s.session_key, driver_number=driver_number
            )
            for s in race_sessions
        ]

        driver_laps_per_session, all_laps_per_session, stints_per_session = await asyncio.gather(
            asyncio.gather(*driver_laps_futures),
            asyncio.gather(*all_laps_futures),
            asyncio.gather(*stints_futures),
        )

        all_normalized: list[float] = []

        for session, driver_laps, all_laps, stints in zip(
            race_sessions,
            driver_laps_per_session,
            all_laps_per_session,
            stints_per_session,
        ):
            session_median = self._compute_session_median(all_laps)
            if session_median is None or session_median == 0:
                continue

            clean_laps = self._filter_clean_laps(driver_laps, stints, session_median)
            for lap in clean_laps:
                all_normalized.append(lap.lap_duration / session_median)  # type: ignore[operator]

        if len(all_normalized) < 3:
            return None, None

        driver_rpace = median(all_normalized)

        # Compute rpace for all drivers in the same sessions to determine percentile
        all_driver_rpaces = await self._compute_all_drivers_rpace(
            race_sessions,
            all_laps_per_session,  # type: ignore[arg-type]
            stints_per_session,  # type: ignore[arg-type]
        )

        if len(all_driver_rpaces) <= 1:
            return driver_rpace, 50.0

        # Lower rpace = faster; percentile = fraction of drivers who are slower (higher rpace)
        slower_count = sum(1 for r in all_driver_rpaces.values() if r > driver_rpace)
        total = len(all_driver_rpaces)
        percentile = (slower_count / total) * 100.0

        return driver_rpace, percentile

    def _compute_session_median(self, all_laps: list[Lap]) -> float | None:
        """Compute the median lap duration for a session from all drivers' laps."""
        durations = [
            l.lap_duration
            for l in all_laps
            if l.lap_duration is not None
            and l.is_pit_out_lap is not True
            and l.lap_number > 1
        ]
        if not durations:
            return None
        return median(durations)

    def _filter_clean_laps(
        self,
        driver_laps: list[Lap],
        stints: list[Stint],
        session_median: float,
    ) -> list[Lap]:
        """Apply SC exclusion and prime tyre window filters."""
        result: list[Lap] = []
        for lap in driver_laps:
            if lap.is_pit_out_lap is True:
                continue
            if lap.lap_number <= 1:
                continue
            if lap.lap_duration is None:
                continue
            if lap.lap_duration > SC_LAP_EXCLUSION_THRESHOLD * session_median:
                continue

            # Find stint for this lap
            stint = next(
                (
                    s
                    for s in stints
                    if s.lap_start <= lap.lap_number <= (s.lap_end or 9999)
                ),
                None,
            )
            if stint is None:
                continue

            tyre_age = lap.lap_number - stint.lap_start + (stint.tyre_age_at_start or 0)
            if not (3 <= tyre_age <= 15):
                continue

            result.append(lap)
        return result

    async def _compute_all_drivers_rpace(
        self,
        race_sessions: list[Session],
        all_laps_per_session: list[list[Lap]],
        stints_per_session: list[list[Stint]],
    ) -> dict[int, float]:
        """Compute rpace score for every driver across all race sessions."""
        # Collect unique driver numbers from all laps
        all_driver_numbers: set[int] = set()
        for session_laps in all_laps_per_session:
            for lap in session_laps:
                all_driver_numbers.add(lap.driver_number)

        # Fetch stints for all drivers × sessions concurrently
        tasks: list[tuple[int, int]] = [
            (drv, s.session_key) for drv in all_driver_numbers for s in race_sessions
        ]
        stint_results: list[list[Stint]] = await asyncio.gather(
            *[
                self._client.get("stints", Stint, session_key=sk, driver_number=drv)
                for drv, sk in tasks
            ]
        )
        driver_session_stints: dict[int, dict[int, list[Stint]]] = {}
        for (drv, sk), stints in zip(tasks, stint_results):
            driver_session_stints.setdefault(drv, {})[sk] = stints

        # Build session_key → session_median lookup
        session_medians: dict[int, float | None] = {}
        for session, all_laps in zip(race_sessions, all_laps_per_session):
            session_medians[session.session_key] = self._compute_session_median(all_laps)

        # Build session_key → {driver_number: [Lap]} lookup
        session_driver_laps: dict[int, dict[int, list[Lap]]] = {}
        for session, all_laps in zip(race_sessions, all_laps_per_session):
            dl: dict[int, list[Lap]] = {}
            for lap in all_laps:
                dl.setdefault(lap.driver_number, []).append(lap)
            session_driver_laps[session.session_key] = dl

        driver_rpaces: dict[int, float] = {}
        for drv in all_driver_numbers:
            normalized: list[float] = []
            for session in race_sessions:
                sm = session_medians.get(session.session_key)
                if sm is None or sm == 0:
                    continue
                drv_laps = session_driver_laps.get(session.session_key, {}).get(drv, [])
                drv_stints = driver_session_stints.get(drv, {}).get(session.session_key, [])
                clean = self._filter_clean_laps(drv_laps, drv_stints, sm)
                for lap in clean:
                    normalized.append(lap.lap_duration / sm)  # type: ignore[operator]
            if len(normalized) >= 3:
                driver_rpaces[drv] = median(normalized)

        return driver_rpaces

    async def _compute_overtake_adjustment(
        self,
        driver_number: int,
        meeting_keys: list[int],
    ) -> float:
        """Return average net positions gained in races where the driver started P10+."""
        race_sessions = await get_sessions_for_meetings(
            self._client, meeting_keys, ["Race"]
        )

        if not race_sessions:
            return 0.0

        grid_futures = [
            self._client.get("starting_grid", StartingGridEntry, session_key=s.session_key)
            for s in race_sessions
        ]
        result_futures = [
            self._client.get("session_result", SessionResult, session_key=s.session_key)
            for s in race_sessions
        ]

        grids_list, results_list = await asyncio.gather(
            asyncio.gather(*grid_futures),
            asyncio.gather(*result_futures),
        )

        net_gains: list[float] = []
        for grid, results in zip(grids_list, results_list):
            driver_grid = next(
                (e for e in grid if e.driver_number == driver_number), None
            )
            if driver_grid is None or driver_grid.position < 10:
                continue

            driver_result = next(
                (r for r in results if r.driver_number == driver_number), None
            )
            if driver_result is None or driver_result.position is None:
                continue

            net_gain = driver_grid.position - driver_result.position
            net_gains.append(float(net_gain))

        if not net_gains:
            return 0.0

        return sum(net_gains) / len(net_gains)
