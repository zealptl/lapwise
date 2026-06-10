"""Service for computing fastest lap candidates from historical race data."""

import asyncio
import statistics
from collections import defaultdict
from datetime import datetime

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.analysis.fastest_lap import FastestLapCandidate
from lapwise.models.laps import Lap
from lapwise.models.session_result import SessionResult
from lapwise.models.sessions import Session
from lapwise.models.stints import Stint
from lapwise.services.analysis.common import (
    SC_LAP_EXCLUSION_THRESHOLD,
    get_last_n_meeting_keys,
    get_sessions_for_meetings,
)


class FastestLapService:
    """Compute fastest lap candidate statistics for drivers across historical sessions."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def get_fastest_lap_candidates(
        self,
        last_n_races: int = 12,
        session_key: int | None = None,
        include_circuit_history: bool = False,
    ) -> list[FastestLapCandidate]:
        """Return fastest lap candidate statistics for all drivers in the sample.

        Args:
            last_n_races: Number of race weekends to include.
            session_key: When provided with include_circuit_history=True, constrains
                results to meetings at the same circuit as this session.
            include_circuit_history: When True and session_key is set, merges same-circuit
                meetings from the previous 2 calendar years.

        Returns:
            List of FastestLapCandidate, one entry per driver seen across all sessions.
        """
        # Step 1: Resolve meeting keys
        if include_circuit_history and session_key is not None:
            sessions_for_key: list[Session] = await self._client.get(
                "sessions", Session, session_key=session_key
            )
            circuit_key: int | None = sessions_for_key[0].circuit_key if sessions_for_key else None
            current_year = datetime.now().year
            year_range = (current_year - 2, current_year - 1)
            meeting_keys = await get_last_n_meeting_keys(
                self._client,
                last_n_races,
                circuit_key=circuit_key,
                year_range=year_range,
            )
        else:
            meeting_keys = await get_last_n_meeting_keys(self._client, last_n_races)

        sample_races = len(meeting_keys)

        # Step 2: Fetch Race + Sprint sessions
        sessions = await get_sessions_for_meetings(
            self._client, meeting_keys, ["Race", "Sprint"]
        )

        total_sessions = len(sessions)

        # Per-driver accumulators
        fl_count: dict[int, int] = defaultdict(int)
        fl_fresh_tyre_hits: dict[int, int] = defaultdict(int)
        fl_position_sum: dict[int, float] = defaultdict(float)
        fl_position_count: dict[int, int] = defaultdict(int)
        all_drivers: set[int] = set()

        # Step 3: Process each session
        session_keys = [s.session_key for s in sessions]

        # Fetch laps, stints, and results for all sessions in parallel
        lap_tasks = [self._client.get("laps", Lap, session_key=sk) for sk in session_keys]
        stint_tasks = [self._client.get("stints", Stint, session_key=sk) for sk in session_keys]
        result_tasks = [
            self._client.get("session_result", SessionResult, session_key=sk)
            for sk in session_keys
        ]

        lap_results, stint_results, result_results = await asyncio.gather(
            asyncio.gather(*lap_tasks),
            asyncio.gather(*stint_tasks),
            asyncio.gather(*result_tasks),
        )

        for idx, session in enumerate(sessions):
            sk = session.session_key
            all_laps: list[Lap] = lap_results[idx]
            stints: list[Stint] = stint_results[idx]
            session_results: list[SessionResult] = result_results[idx]

            # Track all drivers seen
            for lap in all_laps:
                all_drivers.add(lap.driver_number)

            # Filter: no pit-out laps, lap_duration must be present
            laps_with_duration = [
                lap for lap in all_laps
                if lap.lap_duration is not None and lap.is_pit_out_lap is not True
            ]

            if not laps_with_duration:
                continue

            # SC exclusion: compute session median from all laps that have a duration
            all_durations = [
                lap.lap_duration for lap in all_laps if lap.lap_duration is not None
            ]
            session_median = statistics.median(all_durations)
            threshold = SC_LAP_EXCLUSION_THRESHOLD * session_median

            eligible_laps = [
                lap for lap in laps_with_duration if lap.lap_duration <= threshold
            ]

            if not eligible_laps:
                continue

            # Find minimum lap duration (handles ties via task 5.2)
            min_duration = min(lap.lap_duration for lap in eligible_laps)  # type: ignore[type-var]
            winners = [lap for lap in eligible_laps if lap.lap_duration == min_duration]

            # Build lookup structures for stints and session results
            # stints keyed by driver_number
            driver_stints: dict[int, list[Stint]] = defaultdict(list)
            for stint in stints:
                driver_stints[stint.driver_number].append(stint)

            # session_result keyed by driver_number
            driver_result: dict[int, SessionResult] = {}
            for sr in session_results:
                driver_result[sr.driver_number] = sr

            for winning_lap in winners:
                driver = winning_lap.driver_number
                fl_count[driver] += 1

                # Tyre age calculation
                fl_lap_number = winning_lap.lap_number
                tyre_age = _compute_tyre_age(fl_lap_number, driver_stints.get(driver, []))
                if tyre_age is not None and tyre_age <= 2:
                    fl_fresh_tyre_hits[driver] += 1

                # Finishing position
                if driver in driver_result and driver_result[driver].position is not None:
                    fl_position_sum[driver] += driver_result[driver].position  # type: ignore[operator]
                    fl_position_count[driver] += 1

        # Step 4: Aggregate and build results
        candidates: list[FastestLapCandidate] = []
        for driver in all_drivers:
            count = fl_count[driver]
            fl_rate = count / total_sessions if total_sessions > 0 else 0.0

            typical_fl_position: float | None = None
            if fl_position_count[driver] > 0:
                typical_fl_position = fl_position_sum[driver] / fl_position_count[driver]

            fl_on_fresh_tyre_rate: float | None = None
            if count > 0:
                fl_on_fresh_tyre_rate = fl_fresh_tyre_hits[driver] / count

            candidates.append(
                FastestLapCandidate(
                    driver_number=driver,
                    fastest_lap_count=count,
                    total_sessions=total_sessions,
                    fl_rate=fl_rate,
                    typical_fl_position=typical_fl_position,
                    fl_on_fresh_tyre_rate=fl_on_fresh_tyre_rate,
                    sample_races=sample_races,
                )
            )

        return candidates


def _compute_tyre_age(lap_number: int, stints: list[Stint]) -> int | None:
    """Return the effective tyre age at the given lap number.

    Finds the stint that covers ``lap_number`` and computes:
        tyre_age = lap_number - stint.lap_start + (stint.tyre_age_at_start or 0)

    Returns None if no covering stint is found.
    """
    for stint in stints:
        lap_end = stint.lap_end if stint.lap_end is not None else float("inf")
        if stint.lap_start <= lap_number <= lap_end:
            age_at_start = stint.tyre_age_at_start or 0
            return lap_number - stint.lap_start + age_at_start
    return None
