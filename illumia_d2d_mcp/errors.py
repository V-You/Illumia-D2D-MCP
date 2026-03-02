"""Error model for Illumia D2D MCP.

All tools return errors in a consistent envelope so the LLM agent
can recover gracefully and the SE sees actionable messages.
"""

from __future__ import annotations
from typing import Any


class D2DError(Exception):
    """Raised when a tool encounters a domain error."""

    def __init__(
        self,
        code: str,
        message: str = "",
        retriable: bool = False,
        suggested_action: str = "",
    ):
        self.code = code
        self.message = message
        self.retriable = retriable
        self.suggested_action = suggested_action
        super().__init__(message)

    def to_envelope(self) -> dict[str, Any]:
        return make_error_envelope(
            code=self.code,
            message=self.message,
            retriable=self.retriable,
            suggested_action=self.suggested_action,
        )


def make_error_envelope(
    code: str,
    message: str = "",
    retriable: bool = False,
    suggested_action: str = "",
) -> dict[str, Any]:
    """Build a structured error envelope."""
    return {
        "error": {
            "code": code,
            "message": message,
            "retriable": retriable,
            "suggested_action": suggested_action,
        }
    }
