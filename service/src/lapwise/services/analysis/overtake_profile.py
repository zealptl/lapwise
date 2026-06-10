"""Service layer for the overtake profile analysis endpoint."""

from datetime import datetime

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.analysis.overtake_profile import OvertakeProfile
from lapwise.models.overtakes import Overtake
from lapwise.models.sessions import Session
from lapwise.services.analysis.common import get_last_n_meeting_keys, get_sessions_for_meetings


class OvertakeProfileService:
    """Computes per-driver overtake statistics from Race and Sprint sessions."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def get_overtake_profiles(
        self,
        driver_number: int | None = None,
        last_n_races: int = 12,
        session_key: int | None = None,
        include_circuit_history: bool = False,
    ) -> list[OvertakeProfile]:
        """Return overtake profiles for all drivers (or a single driver).

        Args:
            driver_number: If provided, return only this driver's profile.
            last_n_races: Number of race weekends to include.
            session_key: If provided, constrains to the circuit of this session.
                Also used to compute circuit_overtake_avg.
            include_circuit_history: If True and session_key is provided, merges
                meetings from the same circuit for the previous 2 calendar years.

        Returns:
            A list of OvertakeProfile instances.
        """
        # ── Step 1: Resolve meeting keys ─────────────────────────────────────
        circuit_key: int | None = None

        if include_circuit_history and session_key is not None:
            # Fetch the session to get its circuit_key
            sessions_for_key: list[Session] = await self._client.get(
                "sessions", Session, session_key=session_key
            )
            if sessions_for_key:
                circuit_key = sessions_for_key[0].circuit_key
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
        else:
            meeting_keys = await get_last_n_meeting_keys(self._client, last_n_races)

        # ── Step 2: Fetch Race + Sprint sessions ─────────────────────────────
        sessions = await get_sessions_for_meetings(
            self._client, meeting_keys, ["Race", "Sprint"]
        )

        # ── Step 3: Fetch overtakes per session ──────────────────────────────
        all_overtakes: list[Overtake] = []
        for session in sessions:
            overtakes = await self._client.get(
                "overtakes", Overtake, session_key=session.session_key
            )
            all_overtakes.extend(overtakes)

        # ── Step 4: Aggregate per driver ─────────────────────────────────────
        total_races = len(sessions)
        sample_races = len(meeting_keys)

        overtakes_made: dict[int, int] = {}
        overtakes_lost: dict[int, int] = {}

        for ot in all_overtakes:
            made_driver = ot.overtaking_driver_number
            lost_driver = ot.overtaken_driver_number
            overtakes_made[made_driver] = overtakes_made.get(made_driver, 0) + 1
            overtakes_lost[lost_driver] = overtakes_lost.get(lost_driver, 0) + 1

        # Collect all unique drivers seen in any overtake event
        all_drivers = set(overtakes_made.keys()) | set(overtakes_lost.keys())

        # ── Step 5: Compute aggression_score (percentile rank) ───────────────
        # overtake_rate per driver
        overtake_rates: dict[int, float] = {}
        for d in all_drivers:
            made = overtakes_made.get(d, 0)
            overtake_rates[d] = made / total_races if total_races > 0 else 0.0

        # Percentile rank: for each driver, score = (# drivers with lower rate) / (total-1) * 100
        # Handle the edge case of a single driver or all tied rates
        aggression_scores: dict[int, float] = {}
        n_drivers = len(all_drivers)
        if n_drivers <= 1:
            for d in all_drivers:
                aggression_scores[d] = 0.0
        else:
            sorted_rates = sorted(overtake_rates.values())
            for d in all_drivers:
                rate = overtake_rates[d]
                rank = sum(1 for r in sorted_rates if r < rate)
                aggression_scores[d] = (rank / (n_drivers - 1)) * 100.0

        # ── Step 6: Compute circuit_overtake_avg ─────────────────────────────
        circuit_overtake_avgs: dict[int, float | None] = {}
        if session_key is not None or include_circuit_history:
            # Determine which sessions belong to the relevant circuit
            if circuit_key is not None:
                circuit_sessions = [s for s in sessions if s.circuit_key == circuit_key]
            elif session_key is not None:
                # If circuit_key wasn't resolved, try to derive from sessions by session_key
                target_session_list = [s for s in sessions if s.session_key == session_key]
                if target_session_list:
                    ck = target_session_list[0].circuit_key
                    circuit_sessions = [s for s in sessions if s.circuit_key == ck]
                else:
                    circuit_sessions = sessions
            else:
                circuit_sessions = sessions

            circuit_session_keys = {s.session_key for s in circuit_sessions}
            n_circuit_sessions = len(circuit_sessions)

            # Count overtakes made by each driver in circuit sessions only
            circuit_made: dict[int, int] = {}
            for ot in all_overtakes:
                if ot.session_key in circuit_session_keys:
                    d = ot.overtaking_driver_number
                    circuit_made[d] = circuit_made.get(d, 0) + 1

            for d in all_drivers:
                if n_circuit_sessions > 0:
                    circuit_overtake_avgs[d] = circuit_made.get(d, 0) / n_circuit_sessions
                else:
                    circuit_overtake_avgs[d] = None
        else:
            for d in all_drivers:
                circuit_overtake_avgs[d] = None

        # ── Step 7: Build profiles ────────────────────────────────────────────
        profiles: list[OvertakeProfile] = []
        for d in all_drivers:
            made = overtakes_made.get(d, 0)
            lost = overtakes_lost.get(d, 0)
            rate = overtake_rates[d]
            def_rate = lost / total_races if total_races > 0 else 0.0
            profiles.append(
                OvertakeProfile(
                    driver_number=d,
                    overtakes_made=made,
                    overtakes_lost=lost,
                    net_overtakes=made - lost,
                    overtake_rate=rate,
                    defensive_rate=def_rate,
                    aggression_score=aggression_scores[d],
                    circuit_overtake_avg=circuit_overtake_avgs[d],
                    sample_races=sample_races,
                    total_races=total_races,
                )
            )

        # ── Step 8: Filter by driver_number if requested ──────────────────────
        if driver_number is not None:
            profiles = [p for p in profiles if p.driver_number == driver_number]

        return profiles
