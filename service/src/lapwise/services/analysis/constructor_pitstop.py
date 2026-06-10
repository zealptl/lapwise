"""Service layer for the constructor pitstop analysis endpoint."""

import asyncio
import statistics

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.analysis.constructor_pitstop import ConstructorPitstop
from lapwise.models.drivers import Driver
from lapwise.models.pit import PitStop
from lapwise.services.analysis.common import get_last_n_meeting_keys, get_sessions_for_meetings


def _bracket_points(stop_duration: float) -> int:
    """Return F1 Fantasy bracket points for a single stop duration."""
    if stop_duration < 2.0:
        return 20
    if stop_duration < 2.2:
        return 10
    if stop_duration < 2.5:
        return 5
    if stop_duration <= 3.0:
        return 2
    return 0


class ConstructorPitstopService:
    """Compute pit stop performance and F1 Fantasy scoring per constructor."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def get_constructor_pitstops(
        self,
        team_name: str | None = None,
        last_n_races: int = 12,
        include_circuit_history: bool = False,
    ) -> list[ConstructorPitstop]:
        """Return pit stop analytics aggregated per constructor.

        Args:
            team_name: If provided, return only this constructor's data.
            last_n_races: Number of recent race weekends to include.
            include_circuit_history: Reserved for future circuit-scoped history;
                currently has no additional effect (no circuit context available
                at this endpoint level — falls back to last_n_races).

        Returns:
            List of ConstructorPitstop instances, one per constructor.
        """
        # Step 1: Resolve meeting keys
        meeting_keys = await get_last_n_meeting_keys(self._client, last_n_races)

        # Step 2: Fetch Race + Sprint sessions
        sessions = await get_sessions_for_meetings(
            self._client, meeting_keys, ["Race", "Sprint"]
        )

        if not sessions:
            return []

        # Step 3: For each session fetch pit stops and drivers in parallel
        session_keys = [s.session_key for s in sessions]

        pit_tasks = [
            self._client.get("pit", PitStop, session_key=sk) for sk in session_keys
        ]
        driver_tasks = [
            self._client.get("drivers", Driver, session_key=sk) for sk in session_keys
        ]

        pit_results: list[list[PitStop]] = list(await asyncio.gather(*pit_tasks))
        driver_results: list[list[Driver]] = list(await asyncio.gather(*driver_tasks))

        # Per-constructor accumulation structures
        # constructor → list of valid stop_durations across all sessions
        constructor_stops: dict[str, list[float]] = {}
        # constructor → list of lane_durations (where not None)
        constructor_lane_durations: dict[str, list[float]] = {}
        # constructor → set of session_keys where it had ≥1 valid stop
        constructor_session_keys: dict[str, set[int]] = {}
        # session_key → field_min_stop (min stop_duration across all valid stops)
        session_field_min: dict[int, float] = {}
        # session_key → constructor → list of valid stops (for fantasy points)
        session_constructor_stops: dict[int, dict[str, list[float]]] = {}

        for session, pit_stops, drivers in zip(sessions, pit_results, driver_results):
            sk = session.session_key

            # Build driver_number → team_name mapping for this session
            driver_to_team: dict[int, str] = {}
            for driver in drivers:
                if driver.team_name is not None:
                    driver_to_team[driver.driver_number] = driver.team_name

            # Filter valid stops (exclude null and outliers > 60s)
            valid_stops = [
                stop for stop in pit_stops
                if stop.stop_duration is not None and stop.stop_duration <= 60.0
            ]

            if not valid_stops:
                continue

            # Compute field_min_stop for this session
            field_min = min(s.stop_duration for s in valid_stops)  # type: ignore[arg-type]
            session_field_min[sk] = field_min
            session_constructor_stops[sk] = {}

            # Attribute each stop to its constructor
            for stop in valid_stops:
                ctor = driver_to_team.get(stop.driver_number)
                if ctor is None:
                    continue

                stop_dur: float = stop.stop_duration  # type: ignore[assignment]

                constructor_stops.setdefault(ctor, []).append(stop_dur)
                constructor_session_keys.setdefault(ctor, set()).add(sk)
                if stop.lane_duration is not None:
                    constructor_lane_durations.setdefault(ctor, []).append(stop.lane_duration)

                session_constructor_stops[sk].setdefault(ctor, []).append(stop_dur)

        total_sessions = len(session_field_min)

        results: list[ConstructorPitstop] = []

        for ctor, durations in constructor_stops.items():
            if not durations:
                continue

            avg_stop = statistics.mean(durations)
            fastest_stop = min(durations)
            sub_2s_count = sum(1 for d in durations if d < 2.0)
            sub_2s = sub_2s_count / len(durations)

            consistency = (
                max(0.0, 100.0 - statistics.stdev(durations) * 100.0)
                if len(durations) >= 2
                else 100.0
            )

            lane_durs = constructor_lane_durations.get(ctor, [])
            avg_lane = statistics.mean(lane_durs) if lane_durs else None

            sample_stops = len(durations)
            sample_races = len(constructor_session_keys.get(ctor, set()))

            # Fantasy points per session
            session_totals: list[float] = []
            fastest_pitstop_sessions = 0

            for sk, field_min in session_field_min.items():
                ctor_stops_this_session = session_constructor_stops[sk].get(ctor, [])
                if not ctor_stops_this_session:
                    continue

                # Bracket points for all this constructor's stops this session
                bracket_sum = sum(_bracket_points(d) for d in ctor_stops_this_session)

                # Check fastest pitstop bonus (tie: any stop equals field_min)
                had_fastest = any(d == field_min for d in ctor_stops_this_session)
                bonus = 5 if had_fastest else 0
                if had_fastest:
                    fastest_pitstop_sessions += 1

                session_totals.append(bracket_sum + bonus)

            fantasy_avg = statistics.mean(session_totals) if session_totals else 0.0
            fastest_pitstop_rate = (
                fastest_pitstop_sessions / total_sessions if total_sessions > 0 else 0.0
            )

            results.append(
                ConstructorPitstop(
                    team_name=ctor,
                    avg_stop_duration=avg_stop,
                    avg_lane_duration=avg_lane,
                    fastest_stop_in_sample=fastest_stop,
                    fantasy_points_avg=fantasy_avg,
                    fastest_pitstop_rate=fastest_pitstop_rate,
                    sub_2s_rate=sub_2s,
                    consistency_score=consistency,
                    sample_stops=sample_stops,
                    sample_races=sample_races,
                )
            )

        # Filter by team_name if provided
        if team_name is not None:
            results = [r for r in results if r.team_name == team_name]

        return results
