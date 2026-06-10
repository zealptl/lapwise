"""Analysis services package — exposes AnalysisService for the /v1/analysis endpoints."""

# Re-export AnalysisService from its implementation module so that
# `from lapwise.services.analysis import AnalysisService` continues to work
# now that this directory is a package.
from lapwise.services.analysis._core import AnalysisService

__all__ = ["AnalysisService"]
