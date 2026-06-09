"""FastAPI dependency providers for Lapwise.

Each provider is injected by FastAPI's dependency injection system,
keeping route handlers free from direct instantiation of collaborators.
"""

from fastapi import Request

from lapwise.clients.openf1 import OpenF1Client


def get_openf1_client(request: Request) -> OpenF1Client:
    """Return the shared OpenF1Client stored on app state during lifespan startup."""
    client: OpenF1Client = request.app.state.openf1_client
    return client


async def get_auth() -> None:
    """No-op authentication dependency.

    This slot exists so an auth mechanism can be swapped in later
    without changing route signatures.  It currently accepts all requests.
    """
    return None


# ---------------------------------------------------------------------------
# Service providers — added by endpoint capabilities
# ---------------------------------------------------------------------------
# Each endpoint capability will add a get_<resource>_service helper here.
# Example (added in the endpoint-drivers capability):
#
#   def get_driver_service(
#       client: Annotated[OpenF1Client, Depends(get_openf1_client)],
#   ) -> DriverService:
#       return DriverService(client)
