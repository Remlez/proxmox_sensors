"""Pure helpers for configuration-flow permission validation."""

from __future__ import annotations


REQUIRED_NONEMPTY_LIST_ENDPOINTS = {"nodes", "admin/datastore"}


def minimum_endpoint_has_resources(endpoint, response):
    """Return whether a required endpoint exposes at least one resource."""
    if response is None:
        return False
    if endpoint in REQUIRED_NONEMPTY_LIST_ENDPOINTS and isinstance(response, list):
        return bool(response)
    return True
