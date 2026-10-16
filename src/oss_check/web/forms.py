"""웹 입력 크기를 제한하고 폼을 메모리에서 읽음."""

from collections.abc import AsyncGenerator

from fastapi import Request
from python_multipart.multipart import parse_options_header
from starlette.datastructures import FormData
from starlette.formparsers import FormParser, MultiPartException, MultiPartParser


MAX_INPUT_BYTES = 1_048_576
# URL 인코딩에서는 바이트 하나가 %XX 세 문자로 늘어나므로 여유를 둠.
MAX_FORM_BYTES = MAX_INPUT_BYTES * 12 + 65_536


class InputTooLarge(MultiPartException):
    """입력 또는 폼 전체가 크기 제한을 초과함."""


# [강의] 메서드 재정의: 기존 폼 해석을 유지하며 크기 검사만 앞에 추가함.
class MemoryFormParser(MultiPartParser):
    """파일을 포함한 각 항목을 1MB로 제한하고 디스크 저장 전에 거부함."""

    spool_max_size = MAX_INPUT_BYTES

    def on_part_begin(self) -> None:
        super().on_part_begin()
        self.part_bytes = 0

    def on_part_data(self, data: bytes, start: int, end: int) -> None:
        self.part_bytes += end - start
        if self.part_bytes > MAX_INPUT_BYTES:
            raise InputTooLarge("입력 크기 초과")
        super().on_part_data(data, start, end)


async def read_form(request: Request) -> FormData:
    """폼을 크기 제한 내에서 읽으며 업로드 내용을 로그에 남기지 않음."""
    async def bounded_stream() -> AsyncGenerator[bytes, None]:
        total = 0
        async for chunk in request.stream():
            total += len(chunk)
            if total > MAX_FORM_BYTES:
                raise InputTooLarge("폼 크기 초과")
            yield chunk

    content_type, _ = parse_options_header(request.headers.get("content-type", ""))
    if content_type == b"multipart/form-data":
        parser = MemoryFormParser(request.headers, bounded_stream(), max_files=1,
                                  max_fields=3, max_part_size=MAX_INPUT_BYTES)
    else:
        parser = FormParser(request.headers, bounded_stream(),
                            max_fields=3, max_part_size=MAX_FORM_BYTES)
    return await parser.parse()
