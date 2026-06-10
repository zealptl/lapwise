"""Circuit Profile analysis service."""

import asyncio
import statistics
from collections import Counter
from datetime import datetime

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.analysis.circuit_profile import CircuitProfile
from lapwise.models.laps import Lap
from lapwise.models.meetings import Meeting
from lapwise.models.overtakes import Overtake
from lapwise.models.stints import Stint
from lapwise.models.weather import Weather
from lapwise.services.analysis.common import (
    SC_LAP_EXCLUSION_THRESHOLD,
    get_sessions_for_meetings,
)

# Minimum race sessions required for derived statistics
_MIN_SESSIONS = 2


class CircuitProfileService:
    """Compute a high-level profile of an F1 circuit from historical race data."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def get_circuit_profile(
        self,
        circuit_key: int,
        last_n_years: int = 3,
    ) -> CircuitProfile:
        """Build and return a :class:`CircuitProfile` for *circuit_key*.

        Args:
            circuit_key: The OpenF1 circuit identifier.
            last_n_years: Number of calendar years to include (counting backwards from today).

        Returns:
            A :class:`CircuitProfile` populated from race session data.
        """
        current_year = datetime.now().year
        year_start = current_year - last_n_years + 1

        # 1. Gather all meetings for this circuit across the year window in parallel
        fetch_tasks = [
            self._client.get("meetings", Meeting, circuit_key=circuit_key, year=yr)
            for yr in range(year_start, current_year + 1)
        ]
        year_batches = await asyncio.gather(*fetch_tasks)

        meeting_keys: list[int] = []
        seen_keys: set[int] = set()
        for batch in year_batches:
            for m in batch:
                if m.meeting_key not in seen_keys:
                    meeting_keys.append(m.meeting_key)
                    seen_keys.add(m.meeting_key)

        # 2. Fetch race sessions for those meetings
        sessions = await get_sessions_for_meetings(
            self._client, meeting_keys, ["Race"]
        )

        circuit_short_name: str | None = sessions[0].circuit_short_name if sessions else None

        race_sessions_found = len(sessions)

        # Insufficient data path
        if race_sessions_found < _MIN_SESSIONS:
            return CircuitProfile(
                circuit_key=circuit_key,
                circuit_short_name=circuit_short_name,
                sample_years=last_n_years,
                race_sessions_found=race_sessions_found,
                overtake_difficulty=None,
                avg_overtakes_per_race=None,
                qualifying_importance=None,
                safety_car_tendency=None,
                weather_variability=None,
                typical_compounds=[],
                fl_typical_lap=None,
                avg_pit_stops=0.0,
            )

        session_keys = [s.session_key for s in sessions]

        # 3. Fetch all needed data in parallel across all sessions
        overtake_tasks = [
            self._client.get("overtakes", Overtake, session_key=sk) for sk in session_keys
        ]
        lap_tasks = [
            self._client.get("laps", Lap, session_key=sk) for sk in session_keys
        ]
        stint_tasks = [
            self._client.get("stints", Stint, session_key=sk) for sk in session_keys
        ]
        weather_tasks = [
            self._client.get("weather", Weather, session_key=sk) for sk in session_keys
        ]

        (
            overtake_batches,
            lap_batches,
            stint_batches,
            weather_batches,
        ) = await asyncio.gather(
            asyncio.gather(*overtake_tasks),
            asyncio.gather(*lap_tasks),
            asyncio.gather(*stint_tasks),
            asyncio.gather(*weather_tasks),
        )

        # ── Overtake difficulty ───────────────────────────────────────────────
        overtake_counts = [len(batch) for batch in overtake_batches]
        avg_overtakes = statistics.mean(overtake_counts) if overtake_counts else 0.0

        if avg_overtakes < 15:
            overtake_difficulty = "HIGH"
        elif avg_overtakes <= 30:
            overtake_difficulty = "MEDIUM"
        else:
            overtake_difficulty = "LOW"

        # ── Qualifying importance ─────────────────────────────────────────────
        qualifying_importance_map = {"HIGH": 100, "MEDIUM": 67, "LOW": 33}
        qualifying_importance = qualifying_importance_map[overtake_difficulty]

        # ── Safety car tendency ───────────────────────────────────────────────
        session_pct_slow_values: list[float] = []
        fl_lap_numbers: list[float] = []

        for laps in lap_batches:
            durations = [l.lap_duration for l in laps if l.lap_duration is not None]
            if not durations:
                continue

            median_dur = statistics.median(durations)
            threshold = SC_LAP_EXCLUSION_THRESHOLD * median_dur

            slow_count = sum(1 for d in durations if d > threshold)
            pct_slow = slow_count / len(durations)
            session_pct_slow_values.append(pct_slow)

            # FL typical lap — lap number with minimum non-SC lap duration
            eligible = [l for l in laps if l.lap_duration is not None and l.lap_duration <= threshold]
            if eligible:
                fl_lap = min(eligible, key=lambda l: l.lap_duration)  # type: ignore[arg-type]
                fl_lap_numbers.append(float(fl_lap.lap_number))

        if session_pct_slow_values:
            avg_pct_slow = statistics.mean(session_pct_slow_values)
        else:
            avg_pct_slow = 0.0

        if avg_pct_slow > 0.15:
            safety_car_tendency = "HIGH"
        elif avg_pct_slow >= 0.05:
            safety_car_tendency = "MEDIUM"
        else:
            safety_car_tendency = "LOW"

        fl_typical_lap = statistics.mean(fl_lap_numbers) if fl_lap_numbers else None

        # ── Typical compounds ─────────────────────────────────────────────────
        compound_counter: Counter[str] = Counter()
        for stints in stint_batches:
            for s in stints:
                if s.compound is not None:
                    compound_counter[s.compound] += 1

        typical_compounds = [compound for compound, _ in compound_counter.most_common()]

        # ── Weather variability ───────────────────────────────────────────────
        total_weather = 0
        rainfall_count = 0
        for weather_records in weather_batches:
            for w in weather_records:
                total_weather += 1
                if (w.rainfall or 0) == 1:
                    rainfall_count += 1

        if total_weather > 0:
            pct_rainfall = rainfall_count / total_weather
        else:
            pct_rainfall = 0.0

        if pct_rainfall > 0.30:
            weather_variability = "HIGH"
        elif pct_rainfall >= 0.10:
            weather_variability = "MEDIUM"
        else:
            weather_variability = "LOW"

        # ── Average pit stops ─────────────────────────────────────────────────
        # Per driver per session: pit_stops = max(stint_number) - 1
        all_driver_stops: list[float] = []
        for stints in stint_batches:
            # Group by driver
            driver_max_stint: dict[int, int] = {}
            for s in stints:
                current = driver_max_stint.get(s.driver_number, 0)
                if s.stint_number > current:
                    driver_max_stint[s.driver_number] = s.stint_number
            for max_stint in driver_max_stint.values():
                all_driver_stops.append(float(max(max_stint - 1, 0)))

        avg_pit_stops = statistics.mean(all_driver_stops) if all_driver_stops else 0.0

        return CircuitProfile(
            circuit_key=circuit_key,
            circuit_short_name=circuit_short_name,
            sample_years=last_n_years,
            race_sessions_found=race_sessions_found,
            overtake_difficulty=overtake_difficulty,
            avg_overtakes_per_race=avg_overtakes,
            qualifying_importance=qualifying_importance,
            safety_car_tendency=safety_car_tendency,
            weather_variability=weather_variability,
            typical_compounds=typical_compounds,
            fl_typical_lap=fl_typical_lap,
            avg_pit_stops=avg_pit_stops,
        )
