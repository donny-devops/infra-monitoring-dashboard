import json
from flask import Response, stream_with_context


def sse_stream(generator_fn):
    """Wrap a generator that yields dicts into a proper SSE response."""
    def generate():
        for data in generator_fn():
            if data is None:
                yield ": keepalive\n\n"
            else:
                yield f"data: {json.dumps(data)}\n\n"

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
