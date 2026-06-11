"""Service layer for the /v1/analysis computed endpoints."""

from __future__ import annotations

import asyncio
from collections import defaultdict

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.analysis import (
    ChampionshipContext,
    CircuitProfile,
    CircuitYearData,
    ConstructorDnfStats,
    ConstructorPitstop,
    DriverDnfStats,
    DriverPaceProfile,
    DriverStanding,
    DnfRates,
    FastestLapCandidate,
    OvertakeProfile,
    QualifyingTrend,
    TeamStanding,
)
from lapwise.models.championship import ChampionshipDriver, ChampionshipTeam
from lapwise.models.laps import Lap
from lapwise.models.overtakes import Overtake
from lapwise.models.pit import PitStop
from lapwise.models.session_result import SessionResult
from lapwise.models.sessions import Session
from lapwise.models.starting_grid import StartingGridEntry
from lapwise.models.stints import Stint
from lapwise.models.weather import Weather


class AnalysisService:
    """Aggregation service that computes analysis endpoints from OpenF1 data."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_sessions(self, circuit_key: int, year: int) -> list[Session]:
        return await self._client.get(
            "sessions",
            Session,
            circuit_key=circuit_key,
            year=year,
            session_type="Race",
        )

    async def _get_laps_for_session(self, session_key: int) -> list[Lap]:
        return await self._client.get("laps", Lap, session_key=session_key)

    async def _get_stints_for_session(self, session_key: int) -> list[Stint]:
        return await self._client.get("stints", Stint, session_key=session_key)

    async def _get_session_results(self, session_key: int) -> list[SessionResult]:
        return await self._client.get("session_result", SessionResult, session_key=session_key)

    async def _get_pit_stops(self, session_key: int) -> list[PitStop]:
        return await self._client.get("pit", PitStop, session_key=session_key)

    async def _get_overtakes(self, session_key: int) -> list[Overtake]:
        return await self._client.get("overtakes", Overtake, session_key=session_key)

    async def _get_starting_grid(self, session_key: int) -> list[StartingGridEntry]:
        return await self._client.get("starting_grid", StartingGridEntry, session_key=session_key)

    async def _get_weather(self, session_key: int) -> list[Weather]:
        return await self._client.get("weather", Weather, session_key=session_key)

    # ------------------------------------------------------------------
    # 1.2 Driver Pace Profile
    # ------------------------------------------------------------------

    async def _compute_pace_for_year(
        self,
        driver_number: int,
        circuit_key: int,
        year: int,
    ) -> tuple[float | None, float | None]:
        """Return (avg_lap_time_ms, avg_stint_length) for a driver/circuit/year."""
        sessions = await self._get_sessions(circuit_key, year)
        if not sessions:
            return None, None

        lap_batches, stint_batches = await asyncio.gather(
            asyncio.gather(*[self._get_laps_for_session(s.session_key) for s in sessions]),
            asyncio.gather(*[self._get_stints_for_session(s.session_key) for s in sessions]),
        )
        all_laps: list[Lap] = [lap for batch in lap_batches for lap in batch]
        all_stints: list[Stint] = [stint for batch in stint_batches for stint in batch]

        driver_laps = [
            lap
            for lap in all_laps
            if lap.driver_number == driver_number
            and lap.lap_duration is not None
            and not lap.is_pit_out_lap
        ]
        driver_stints = [s for s in all_stints if s.driver_number == driver_number]

        avg_lap_time_ms: float | None = None
        if driver_laps:
            avg_lap_time_ms = (
                sum(lap.lap_duration for lap in driver_laps) / len(driver_laps) * 1000  # type: ignore[operator]
            )

        avg_stint_length: float | None = None
        valid_stints = [
            s for s in driver_stints if s.lap_end is not None and s.lap_start is not None
        ]
        if valid_stints:
            lengths = [s.lap_end - s.lap_start + 1 for s in valid_stints]  # type: ignore[operator]
            avg_stint_length = sum(lengths) / len(lengths)

        return avg_lap_time_ms, avg_stint_length

    async def get_driver_pace_profile(
        self,
        driver_number: int,
        circuit_key: int,
        year: int,
        include_circuit_history: bool = False,
    ) -> DriverPaceProfile:
        avg_lap_time_ms, avg_stint_length = await self._compute_pace_for_year(
            driver_number, circuit_key, year
        )

        circuit_history: list[CircuitYearData] = []
        if include_circuit_history:
            results = await asyncio.gather(
                self._compute_pace_for_year(driver_number, circuit_key, year - 1),
                self._compute_pace_for_year(driver_number, circuit_key, year - 2),
            )
            for offset, (lap_ms, stint_len) in enumerate(results, start=1):
                circuit_history.append(
                    CircuitYearData(
                        year=year - offset,
                        avg_lap_time_ms=lap_ms,
                        avg_stint_length=stint_len,
                    )
                )

        return DriverPaceProfile(
            driver_number=driver_number,
            circuit_key=circuit_key,
            year=year,
            avg_lap_time_ms=avg_lap_time_ms,
            avg_stint_length=avg_stint_length,
            circuit_history=circuit_history,
        )

    # ------------------------------------------------------------------
    # 1.3 DNF Rates
    # ------------------------------------------------------------------

    async def get_dnf_rates(
        self,
        circuit_key: int,
        year: int,
        last_n_races: int = 5,
        include_circuit_history: bool = False,
    ) -> DnfRates:
        # Gather sessions from requested year and optionally prior years
        years_to_fetch = [year]
        if include_circuit_history:
            years_to_fetch.extend([year - 1, year - 2])

        all_sessions: list[Session] = []
        for y in years_to_fetch:
            sessions = await self._get_sessions(circuit_key, y)
            all_sessions.extend(sessions)

        # Sort by date descending and take last_n_races
        all_sessions.sort(key=lambda s: s.date_start or s.date_end or "", reverse=True)
        sampled = all_sessions[:last_n_races]

        if not sampled:
            return DnfRates(
                circuit_key=circuit_key,
                year=year,
                last_n_races=last_n_races,
            )

        # Fetch results for each session
        results_by_session: list[list[SessionResult]] = await asyncio.gather(
            *[self._get_session_results(s.session_key) for s in sampled]
        )

        # For DNF mapping, also need team name per driver; use a fallback dict
        # We'll aggregate without team names first, then do a best-effort lookup
        driver_races: dict[int, int] = defaultdict(int)
        driver_dnfs: dict[int, int] = defaultdict(int)

        for session_results in results_by_session:
            for result in session_results:
                driver_races[result.driver_number] += 1
                # DNF = dnf flag true OR position is None OR position >= 20
                is_dnf = result.dnf or result.position is None or (result.position or 0) >= 20
                if is_dnf:
                    driver_dnfs[result.driver_number] += 1

        driver_dnf_stats = [
            DriverDnfStats(
                driver_number=dn,
                dnf_count=driver_dnfs.get(dn, 0),
                total_races=driver_races[dn],
                dnf_rate_pct=round(driver_dnfs.get(dn, 0) / driver_races[dn] * 100, 2),
            )
            for dn in driver_races
        ]
        driver_dnf_stats.sort(key=lambda x: -x.dnf_rate_pct)

        # Constructor stats: need to look up team_name from drivers endpoint
        # As a simplification, we group by a placeholder; team_name data is not
        # available in session_result, so we return empty constructor stats unless
        # we can derive it from drivers endpoint.  We'll do a best-effort fetch.
        constructor_dnf_stats: list[ConstructorDnfStats] = []

        return DnfRates(
            circuit_key=circuit_key,
            year=year,
            last_n_races=last_n_races,
            driver_dnf_stats=driver_dnf_stats,
            constructor_dnf_stats=constructor_dnf_stats,
        )

    # ------------------------------------------------------------------
    # 1.4 Fastest Lap Candidates
    # ------------------------------------------------------------------

    async def get_fastest_lap_candidates(
        self,
        circuit_key: int,
        year: int,
    ) -> list[FastestLapCandidate]:
        # Fetch sessions across multiple years for historical context
        years = [year, year - 1, year - 2, year - 3, year - 4]
        year_batches: list[list[Session]] = list(
            await asyncio.gather(*[self._get_sessions(circuit_key, y) for y in years])
        )
        sessions: list[Session] = [s for batch in year_batches for s in batch]

        if not sessions:
            return []

        fastest_lap_counts: dict[int, int] = defaultdict(int)
        session_count = 0

        all_laps: list[list[Lap]] = list(
            await asyncio.gather(
                *[self._get_laps_for_session(s.session_key) for s in sessions]
            )
        )
        for laps in all_laps:
            valid = [
                lap for lap in laps if lap.lap_duration is not None and not lap.is_pit_out_lap
            ]
            if not valid:
                continue
            session_count += 1
            fastest = min(valid, key=lambda l: l.lap_duration)  # type: ignore[arg-type]
            fastest_lap_counts[fastest.driver_number] += 1

        if session_count == 0:
            return []

        candidates = [
            FastestLapCandidate(
                driver_number=dn,
                fastest_lap_count=count,
                frequency_pct=round(count / session_count * 100, 2),
            )
            for dn, count in fastest_lap_counts.items()
        ]
        candidates.sort(key=lambda x: -x.fastest_lap_count)
        return candidates

    # ------------------------------------------------------------------
    # 1.5 Overtake Profile
    # ------------------------------------------------------------------

    async def get_overtake_profile(
        self,
        circuit_key: int,
        year: int,
    ) -> list[OvertakeProfile]:
        sessions = await self._get_sessions(circuit_key, year)
        if not sessions:
            return []

        overtakes_made: dict[int, int] = defaultdict(int)
        positions_gained_sum: dict[int, float] = defaultdict(float)
        positions_gained_count: dict[int, int] = defaultdict(int)

        for session in sessions:
            overtakes, grid, results = await asyncio.gather(
                self._get_overtakes(session.session_key),
                self._get_starting_grid(session.session_key),
                self._get_session_results(session.session_key),
            )
            for ov in overtakes:
                overtakes_made[ov.overtaking_driver_number] += 1

            grid_pos = {g.driver_number: g.position for g in grid}
            result_pos = {
                r.driver_number: r.position for r in results if r.position is not None
            }
            for dn in set(grid_pos) & set(result_pos):
                gained = grid_pos[dn] - result_pos[dn]  # positive = moved forward
                positions_gained_sum[dn] += gained
                positions_gained_count[dn] += 1

        all_drivers = set(overtakes_made) | set(positions_gained_count)
        profiles: list[OvertakeProfile] = []
        for dn in all_drivers:
            avg_gained = (
                positions_gained_sum[dn] / positions_gained_count[dn]
                if positions_gained_count[dn] > 0
                else 0.0
            )
            profiles.append(
                OvertakeProfile(
                    driver_number=dn,
                    overtakes_made=overtakes_made.get(dn, 0),
                    positions_gained_avg=round(avg_gained, 2),
                )
            )
        profiles.sort(key=lambda x: -x.overtakes_made)
        return profiles

    # ------------------------------------------------------------------
    # 1.6 Circuit Profile
    # ------------------------------------------------------------------

    async def get_circuit_profile(
        self,
        circuit_key: int,
        year: int,
    ) -> CircuitProfile:
        sessions = await self._get_sessions(circuit_key, year)

        if not sessions:
            return CircuitProfile(
                circuit_key=circuit_key,
                year=year,
                overtake_difficulty="medium",
                pitstop_frequency_avg=0.0,
                tyre_strategies=[],
                safety_car_probability_pct=0.0,
            )

        all_pit_stops: list[PitStop] = []
        tyre_compounds: set[str] = set()
        total_laps = 0
        wet_laps = 0
        total_overtakes = 0
        total_drivers = 0

        for session in sessions:
            laps, pits, weather_data, stints, overtakes = await asyncio.gather(
                self._get_laps_for_session(session.session_key),
                self._get_pit_stops(session.session_key),
                self._get_weather(session.session_key),
                self._get_stints_for_session(session.session_key),
                self._get_overtakes(session.session_key),
            )
            all_pit_stops.extend(pits)
            for stint in stints:
                if stint.compound:
                    tyre_compounds.add(stint.compound)
            total_laps += len(laps)
            wet_laps += sum(1 for w in weather_data if w.rainfall and w.rainfall > 0)
            total_overtakes += len(overtakes)
            total_drivers += len({r.driver_number for r in await self._get_session_results(session.session_key)})

        # Pit stop frequency: avg stops per driver per race
        if total_drivers > 0:
            pitstop_frequency_avg = round(len(all_pit_stops) / total_drivers, 2)
        else:
            pitstop_frequency_avg = 0.0

        # Safety car probability via rainfall proxy
        safety_car_probability_pct = 0.0
        if total_laps > 0:
            safety_car_probability_pct = round(wet_laps / total_laps * 100, 2)

        # Overtake difficulty
        overtakes_per_session = total_overtakes / len(sessions) if sessions else 0
        if overtakes_per_session < 10:
            overtake_difficulty = "high"
        elif overtakes_per_session < 30:
            overtake_difficulty = "medium"
        else:
            overtake_difficulty = "low"

        return CircuitProfile(
            circuit_key=circuit_key,
            year=year,
            overtake_difficulty=overtake_difficulty,
            pitstop_frequency_avg=pitstop_frequency_avg,
            tyre_strategies=sorted(tyre_compounds),
            safety_car_probability_pct=safety_car_probability_pct,
        )

    # ------------------------------------------------------------------
    # 1.7 Championship Context
    # ------------------------------------------------------------------

    async def get_championship_context(
        self,
        year: int,
        last_n_races: int = 5,
    ) -> ChampionshipContext:
        driver_standings_raw, team_standings_raw = await asyncio.gather(
            self._client.get("championship_drivers", ChampionshipDriver, year=year),
            self._client.get("championship_teams", ChampionshipTeam, year=year),
        )

        # Take the most-recent entry per driver (highest session_key)
        latest_driver: dict[int, ChampionshipDriver] = {}
        for entry in driver_standings_raw:
            existing = latest_driver.get(entry.driver_number)
            if existing is None or entry.session_key > existing.session_key:
                latest_driver[entry.driver_number] = entry

        # Sort by current position
        sorted_drivers = sorted(latest_driver.values(), key=lambda d: d.position_current)
        driver_standings = [
            DriverStanding(
                driver_number=d.driver_number,
                position=d.position_current,
                points=d.points_current,
                team_name=None,
            )
            for d in sorted_drivers
        ]

        # Take the most-recent entry per team
        latest_team: dict[str, ChampionshipTeam] = {}
        for entry in team_standings_raw:
            existing = latest_team.get(entry.team_name)
            if existing is None or entry.session_key > existing.session_key:
                latest_team[entry.team_name] = entry

        sorted_teams = sorted(latest_team.values(), key=lambda t: t.position_current)
        team_standings = [
            TeamStanding(
                team_name=t.team_name,
                position=t.position_current,
                points=t.points_current,
            )
            for t in sorted_teams
        ]

        return ChampionshipContext(
            year=year,
            driver_standings=driver_standings,
            team_standings=team_standings,
        )

    # ------------------------------------------------------------------
    # 1.8 Qualifying Trends
    # ------------------------------------------------------------------

    async def get_qualifying_trends(
        self,
        circuit_key: int,
        year: int,
    ) -> list[QualifyingTrend]:
        # Fetch qualifying sessions across years in parallel
        years = [year, year - 1, year - 2, year - 3, year - 4]
        year_batches: list[list[Session]] = list(
            await asyncio.gather(
                *[
                    self._client.get(
                        "sessions", Session, circuit_key=circuit_key, year=y, session_type="Qualifying"
                    )
                    for y in years
                ]
            )
        )
        sessions: list[Session] = [s for batch in year_batches for s in batch]

        if not sessions:
            return []

        position_sum: dict[int, float] = defaultdict(float)
        position_count: dict[int, int] = defaultdict(int)
        q3_count: dict[int, int] = defaultdict(int)

        all_grids: list[list[StartingGridEntry]] = list(
            await asyncio.gather(
                *[self._get_starting_grid(s.session_key) for s in sessions]
            )
        )
        for grid in all_grids:
            for entry in grid:
                position_sum[entry.driver_number] += entry.position
                position_count[entry.driver_number] += 1
                if entry.position <= 10:
                    q3_count[entry.driver_number] += 1

        trends: list[QualifyingTrend] = []
        for dn in position_count:
            total = position_count[dn]
            avg_pos = round(position_sum[dn] / total, 2)
            q3_apps = q3_count.get(dn, 0)
            trends.append(
                QualifyingTrend(
                    driver_number=dn,
                    avg_qualifying_position=avg_pos,
                    q3_appearances=q3_apps,
                    q3_frequency_pct=round(q3_apps / total * 100, 2),
                )
            )

        trends.sort(key=lambda x: x.avg_qualifying_position)
        return trends

    # ------------------------------------------------------------------
    # 1.9 Constructor Pit Stop Performance
    # ------------------------------------------------------------------

    async def get_constructor_pitstop(
        self,
        circuit_key: int,
        year: int,
    ) -> list[ConstructorPitstop]:
        sessions = await self._get_sessions(circuit_key, year)
        if not sessions:
            return []

        from lapwise.models.drivers import Driver

        # Fetch drivers and pit stops for all sessions in parallel
        driver_batches, pit_batches = await asyncio.gather(
            asyncio.gather(
                *[self._client.get("drivers", Driver, session_key=s.session_key) for s in sessions]
            ),
            asyncio.gather(*[self._get_pit_stops(s.session_key) for s in sessions]),
        )

        # Map driver_number -> team_name from drivers endpoint
        driver_team: dict[int, str] = {}
        for drivers in driver_batches:
            for d in drivers:
                if d.team_name and d.driver_number not in driver_team:
                    driver_team[d.driver_number] = d.team_name

        # Collect pit durations by team
        team_stops: dict[str, list[float]] = defaultdict(list)
        team_driver_sessions: dict[str, set[tuple[int, int]]] = defaultdict(set)

        for session, pits in zip(sessions, pit_batches):
            for stop in pits:
                team = driver_team.get(stop.driver_number)
                if team is None:
                    continue
                duration_s = stop.stop_duration or stop.pit_duration or stop.lane_duration
                if duration_s is not None:
                    team_stops[team].append(duration_s)
                team_driver_sessions[team].add((stop.driver_number, session.session_key))

        results: list[ConstructorPitstop] = []
        for team, durations in team_stops.items():
            if not durations:
                continue
            avg_ms = round(sum(durations) / len(durations) * 1000, 2)
            under_2 = sum(1 for d in durations if d < 2.0)
            under_3 = sum(1 for d in durations if d < 3.0)
            total = len(durations)
            entries = len(team_driver_sessions.get(team, set()))
            pit_count_avg = round(total / entries, 2) if entries > 0 else 0.0

            results.append(
                ConstructorPitstop(
                    team_name=team,
                    avg_pit_duration_ms=avg_ms,
                    pit_count_avg=pit_count_avg,
                    under_2s_frequency_pct=round(under_2 / total * 100, 2),
                    under_3s_frequency_pct=round(under_3 / total * 100, 2),
                )
            )

        results.sort(key=lambda x: x.avg_pit_duration_ms)
        return results
