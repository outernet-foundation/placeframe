from fastapi import Response

plaintext_schema = {"text/plain": {"schema": {"type": "string", "format": "binary"}}}

binary_schema = {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}}

zip_schema = {"application/zip": {"schema": {"type": "string", "format": "binary"}}}

tar_schema = {"application/x-tar": {"schema": {"type": "string", "format": "binary"}}}


class PlainTextResponse(Response):
    media_type = "text/plain; charset=utf-8"


class OctetStreamResponse(Response):
    media_type = "application/octet-stream"


class ZipStreamResponse(Response):
    media_type = "application/zip"


class TarStreamResponse(Response):
    media_type = "application/x-tar"
