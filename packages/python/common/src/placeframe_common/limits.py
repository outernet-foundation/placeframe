"""Limits a client has to respect, kept where a client can read them cheaply.

The server enforces these; a caller that knows them in advance can say "this
capture is too big" before spending minutes building one, instead of meeting the
limit as a failed upload. This module deliberately imports nothing, so a CLI can
read a number without pulling in a web framework.
"""

from __future__ import annotations

# Largest request body the API accepts, as passed to Litestar's
# request_max_body_size (see common.litestar.create_app). A capture session is
# uploaded as one multipart body, so this is the ceiling on a capture tar.
#
# The body is buffered in memory server-side, so this is a memory bound as much
# as a policy one: raising it raises the API's peak footprint per upload.
REQUEST_MAX_BODY_SIZE = 1024 * 1024 * 1024


__all__ = ["REQUEST_MAX_BODY_SIZE"]
