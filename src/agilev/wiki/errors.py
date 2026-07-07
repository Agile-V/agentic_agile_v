"""Errors raised by the Agile-V OpenWiki knowledge-layer package."""

from __future__ import annotations


class WikiError(Exception):
    """Base class for all agilev.wiki errors."""


class WikiNotInitializedError(WikiError):
    """Raised when an operation requires an existing openwiki/ tree."""


class WikiRunnerError(WikiError):
    """Raised when the external `openwiki` CLI cannot be invoked."""
