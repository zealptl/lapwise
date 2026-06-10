"""Service for the Championship Context analysis endpoint.

Computes per-driver momentum, desperation index, and constructor battle flags
from OpenF1 championship standing data.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.analysis.championship_context import (
    ChampionshipContext,
    ConstructorChampionshipContext,
    DriverChampionshipContext,
)
from lapwise.models.championship import ChampionshipDriver, ChampionshipTeam
from lapwise.models.drivers import Driver
from lapwise.models.meetings import Meeting

# Points awarded for a race win (used as max-per-race estimate for desperation calc)
_MAX_POINTS_PER_RACE = 26


def _compute_momentum(
    driver_number: int,
    last_3_data: list[list[ChampionshipDriver]],
    total_points: float,
    total_meetings: int,
) -> str:
    """Compute POSITIVE / NEUTRAL / NEGATIVE momentum for a single driver.

    Args:
        driver_number: The driver whose momentum to compute.
        last_3_data: Championship data for the (up to) 3 most recent meetings,
                     each element being the full list of driver records for that meeting.
        total_points: Driver's cumulative points for the season (points_current at
                      the latest meeting).
        total_meetings: Number of meetings included in this analysis snapshot.

    Returns:
        One of ``"POSITIVE"``, ``"NEUTRAL"``, or ``"NEGATIVE"``.
    """
    points_scored_per_meeting: list[float] = []
    for meeting_records in last_3_data:
        for rec in meeting_records:
            if rec.driver_number == driver_number:
                points_scored_per_meeting.append(rec.points_current - rec.points_start)
                break

    if not points_scored_per_meeting:
        return "NEUTRAL"

    last_3_avg = sum(points_scored_per_meeting) / len(points_scored_per_meeting)
    season_avg = total_points / total_meetings if total_meetings > 0 else 0.0

    if season_avg > 0 and last_3_avg > season_avg * 1.20:
        return "POSITIVE"
    if season_avg > 0 and last_3_avg < season_avg * 0.80:
        return "NEGATIVE"
    # Edge-case: season_avg == 0 (driver has 0 points all season)
    return "NEUTRAL"


class ChampionshipContextService:
    """Compute championship context metrics for drivers and constructors."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def get_championship_context(
        self,
        season: int | None = None,
        after_round: int | None = None,
    ) -> ChampionshipContext:
        """Return a full championship context snapshot.

        Args:
            season: Championship year.  Defaults to the current calendar year.
            after_round: If provided, only include meetings whose ``meeting_key``
                         is ``<= after_round`` (i.e. standings as of that round).

        Returns:
            A :class:`ChampionshipContext` with driver and constructor details.
        """
        current_year = datetime.now().year
        season = season or current_year

        # ── 1. Fetch & filter meetings ────────────────────────────────────────
        all_meetings: list[Meeting] = await self._client.get(
            "meetings", Meeting, year=season
        )
        # Sort ascending by date_start (None sorts first — push them last)
        all_meetings.sort(
            key=lambda m: m.date_start if m.date_start is not None else datetime.max
        )

        if after_round is not None:
            included_meetings = [m for m in all_meetings if m.meeting_key <= after_round]
        else:
            included_meetings = list(all_meetings)

        if not included_meetings:
            return ChampionshipContext(season=season, drivers=[], constructors=[])

        total_season_meetings = len(all_meetings)
        total_included = len(included_meetings)
        included_keys = [m.meeting_key for m in included_meetings]
        latest_key = included_keys[-1]

        # ── 2. Latest driver standings ────────────────────────────────────────
        latest_drivers: list[ChampionshipDriver] = await self._client.get(
            "championship_drivers", ChampionshipDriver, meeting_key=latest_key
        )
        latest_drivers.sort(key=lambda d: d.position_current)

        if not latest_drivers:
            return ChampionshipContext(season=season, drivers=[], constructors=[])

        leader_points = latest_drivers[0].points_current
        p3_points = (
            latest_drivers[2].points_current if len(latest_drivers) >= 3 else leader_points
        )

        # ── 3. Momentum — fetch last 3 meetings' championship data in parallel ─
        last_3_keys = included_keys[-3:]
        last_3_tasks = [
            self._client.get("championship_drivers", ChampionshipDriver, meeting_key=mk)
            for mk in last_3_keys
        ]
        last_3_results: list[list[ChampionshipDriver]] = list(
            await asyncio.gather(*last_3_tasks)
        )

        # ── 4. Constructor standings ──────────────────────────────────────────
        latest_teams: list[ChampionshipTeam] = await self._client.get(
            "championship_teams", ChampionshipTeam, meeting_key=latest_key
        )
        latest_teams.sort(key=lambda t: t.position_current)

        # Identify constructors under pressure (within 30 pts of adjacent team)
        under_pressure_teams: set[str] = set()
        for i in range(len(latest_teams) - 1):
            pts_diff = abs(latest_teams[i].points_current - latest_teams[i + 1].points_current)
            if pts_diff <= 30:
                under_pressure_teams.add(latest_teams[i].team_name)
                under_pressure_teams.add(latest_teams[i + 1].team_name)

        # ── 5. Fetch driver → team mapping for the latest meeting ─────────────
        driver_records: list[Driver] = await self._client.get(
            "drivers", Driver, meeting_key=latest_key
        )
        # Keep one record per driver_number (deduplicate across sessions)
        driver_team_map: dict[int, str | None] = {}
        for dr in driver_records:
            if dr.driver_number not in driver_team_map:
                driver_team_map[dr.driver_number] = dr.team_name

        driver_name_map: dict[int, str | None] = {}
        for dr in driver_records:
            if dr.driver_number not in driver_name_map:
                driver_name_map[dr.driver_number] = dr.full_name

        # ── 6. Build per-driver context ───────────────────────────────────────
        remaining_races = total_season_meetings - total_included
        max_remaining_points = remaining_races * _MAX_POINTS_PER_RACE

        driver_contexts: list[DriverChampionshipContext] = []
        for d in latest_drivers:
            gap_to_leader = leader_points - d.points_current
            gap_to_p3 = max(0.0, p3_points - d.points_current)

            # Desperation index
            if d.position_current == 1:
                desperation_index = 0.0
            elif max_remaining_points > 0:
                if gap_to_leader > max_remaining_points:
                    desperation_index = 100.0
                else:
                    desperation_index = (gap_to_leader / max_remaining_points) * 100.0
            else:
                desperation_index = 100.0 if gap_to_leader > 0 else 0.0

            momentum = _compute_momentum(
                d.driver_number, last_3_results, d.points_current, total_included
            )

            team = driver_team_map.get(d.driver_number)
            constructor_battle = team in under_pressure_teams if team else False

            driver_contexts.append(
                DriverChampionshipContext(
                    driver_number=d.driver_number,
                    full_name=driver_name_map.get(d.driver_number),
                    team_name=team,
                    points_current=d.points_current,
                    championship_position=d.position_current,
                    points_gap_to_leader=gap_to_leader,
                    points_gap_to_p3=gap_to_p3,
                    momentum=momentum,
                    desperation_index=round(desperation_index, 2),
                    constructor_battle=constructor_battle,
                )
            )

        # ── 7. Build per-constructor context ──────────────────────────────────
        constructor_leader_pts = latest_teams[0].points_current if latest_teams else 0.0
        constructor_contexts: list[ConstructorChampionshipContext] = []
        for t in latest_teams:
            constructor_contexts.append(
                ConstructorChampionshipContext(
                    team_name=t.team_name,
                    points_current=t.points_current,
                    constructor_position=t.position_current,
                    points_gap_to_leader=constructor_leader_pts - t.points_current,
                    under_pressure=t.team_name in under_pressure_teams,
                )
            )

        return ChampionshipContext(
            season=season,
            drivers=driver_contexts,
            constructors=constructor_contexts,
        )
