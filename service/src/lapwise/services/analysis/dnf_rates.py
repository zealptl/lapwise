"""DNF rates analysis service."""

import asyncio
from collections import defaultdict

from lapwise.clients.openf1 import OpenF1Client
from lapwise.models.analysis.dnf_rates import DnfBreakdown, DnfRates
from lapwise.models.session_result import SessionResult
from lapwise.services.analysis.common import get_last_n_meeting_keys, get_sessions_for_meetings

_COMPETITIVE_SESSION_TYPES = ["Qualifying", "Race", "Sprint"]


class DnfRatesService:
    """Compute per-driver DNF/DNS/DSQ rates across recent competitive sessions."""

    def __init__(self, client: OpenF1Client) -> None:
        self._client = client

    async def get_dnf_rates(
        self,
        driver_number: int | None = None,
        season: int | None = None,
        last_n_races: int = 12,
    ) -> list[DnfRates]:
        """Compute DNF rates for all (or one) driver(s).

        Args:
            driver_number: If provided, return stats only for this driver.
            season: Championship year to filter meetings by. Defaults to all years.
            last_n_races: Number of most-recent race weekends to include.

        Returns:
            A list of DnfRates, one entry per driver seen in the sample.
        """
        meeting_keys = await get_last_n_meeting_keys(
            self._client, last_n_races, year=season
        )
        sessions = await get_sessions_for_meetings(
            self._client, meeting_keys, _COMPETITIVE_SESSION_TYPES
        )

        # Build a mapping from session_key -> session_type for quick lookup
        session_type_map: dict[int, str] = {
            s.session_key: (s.session_type or "Unknown") for s in sessions
        }

        # Fetch session results for every session in parallel
        result_batches: list[list[SessionResult]] = list(
            await asyncio.gather(
                *[
                    self._client.get(
                        "session_result", SessionResult, session_key=s.session_key
                    )
                    for s in sessions
                ]
            )
        )
        all_results: list[SessionResult] = [r for batch in result_batches for r in batch]

        # Filter by driver if requested
        if driver_number is not None:
            all_results = [r for r in all_results if r.driver_number == driver_number]

        if not all_results:
            return []

        # Aggregate per driver
        # Structure: driver_number -> session_type -> list of (dnf, dns, dsq)
        driver_by_type: dict[int, dict[str, list[tuple[bool, bool, bool]]]] = defaultdict(
            lambda: defaultdict(list)
        )

        for result in all_results:
            stype = session_type_map.get(result.session_key, "Unknown")
            driver_by_type[result.driver_number][stype].append(
                (result.dnf, result.dns, result.dsq)
            )

        dnf_rates_list: list[DnfRates] = []

        for drv_num, by_type in driver_by_type.items():
            # Flatten all results for this driver
            all_drv_results = [
                entry for entries in by_type.values() for entry in entries
            ]
            total_sessions = len(all_drv_results)

            dnf_count = sum(1 for dnf, dns, dsq in all_drv_results if dnf)
            dns_count = sum(1 for dnf, dns, dsq in all_drv_results if dns)
            dsq_count = sum(1 for dnf, dns, dsq in all_drv_results if dsq)

            total_incidents = dnf_count + dns_count + dsq_count
            dnf_rate = total_incidents / total_sessions if total_sessions > 0 else 0.0
            reliability_score = (1.0 - dnf_rate) * 100.0

            # Per session type breakdown
            def _rate_for_type(stype: str) -> float:
                entries = by_type.get(stype, [])
                if not entries:
                    return 0.0
                incidents = sum(1 for dnf, dns, dsq in entries if dnf or dns or dsq)
                return incidents / len(entries)

            breakdown = DnfBreakdown(
                qualifying_dnf_rate=_rate_for_type("Qualifying"),
                race_dnf_rate=_rate_for_type("Race"),
                sprint_dnf_rate=_rate_for_type("Sprint"),
            )

            dnf_rates_list.append(
                DnfRates(
                    driver_number=drv_num,
                    dnf_count=dnf_count,
                    dns_count=dns_count,
                    dsq_count=dsq_count,
                    total_sessions=total_sessions,
                    dnf_rate=dnf_rate,
                    reliability_score=reliability_score,
                    sample_races=len(meeting_keys),
                    breakdown=breakdown,
                )
            )

        # Sort by driver_number for deterministic output
        dnf_rates_list.sort(key=lambda x: x.driver_number)
        return dnf_rates_list
