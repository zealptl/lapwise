from typing import Literal


class UpstreamError(Exception):
    def __init__(
        self,
        category: Literal["bad_gateway", "gateway_timeout", "forwarded"],
        upstream_status: int | None = None,
        upstream_message: str | None = None,
    ) -> None:
        super().__init__(category)
        self.category = category
        self.upstream_status = upstream_status
        self.upstream_message = upstream_message
