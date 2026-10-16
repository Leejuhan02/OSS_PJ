from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from oss_check.app.sample import sample_report
from starlette.datastructures import FormData, UploadFile
from starlette.formparsers import MultiPartException

from oss_check.web.forms import InputTooLarge, MAX_INPUT_BYTES, read_form


router = APIRouter()

templates = Jinja2Templates(
    directory="src/oss_check/web/templates"
)


@router.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@router.post("/analyze", response_class=HTMLResponse)
async def receive_input(request: Request) -> HTMLResponse:
    """IF-UI-01: 폼 입력을 접수함. 실제 분석 서비스 연결은 별도 단계임."""
    try:
        form = await read_form(request)
    except InputTooLarge:
        return input_response(request, "입력 크기는 1MB 이하여야 합니다.", 413)
    except MultiPartException:
        return input_response(request, "입력 형식을 확인해 주세요.", 400)
    try:
        return await receive_form(request, form)
    finally:
        await form.close()


async def receive_form(request: Request, form: FormData) -> HTMLResponse:
    """원본 바이트 크기를 검사한 뒤 파일 또는 텍스트를 접수함."""
    dependency_file = form.get("dependency_file")
    dependency_text = form.get("dependency_text", "")
    project_license = form.get("project_license", "MIT")
    if not isinstance(dependency_text, str) or not isinstance(project_license, str):
        return input_response(request, "입력 형식을 확인해 주세요.", 400)
    if len(dependency_text.encode("utf-8")) > MAX_INPUT_BYTES:
        return input_response(request, "입력 크기는 1MB 이하여야 합니다.", 413)
    text = dependency_text.strip()
    has_file = isinstance(dependency_file, UploadFile) and bool(dependency_file.filename)
    error = None
    try:
        if has_file and text:
            error = "파일과 직접 입력 중 하나만 사용해 주세요."
        elif has_file:
            try:
                content = await dependency_file.read(MAX_INPUT_BYTES + 1)
                if len(content) > MAX_INPUT_BYTES:
                    return input_response(request, "입력 크기는 1MB 이하여야 합니다.", 413)
                text = content.decode("utf-8-sig").strip()
            except UnicodeDecodeError:
                error = "UTF-8 텍스트 파일을 선택해 주세요."
        if not error and not text:
            error = "파일을 선택하거나 의존성 목록을 입력해 주세요."
    finally:
        if isinstance(dependency_file, UploadFile):
            await dependency_file.close()

    return input_response(request, error, 400 if error else 200,
                          project_license, dependency_text)


def input_response(request: Request, error: str | None, status: int,
                   project_license: str = "MIT", dependency_text: str = "") -> HTMLResponse:
    """접수 결과와 오류를 같은 입력 화면에서 안내함."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "input_received": error is None,
            "input_error": error,
            "received_license": project_license.strip() or "MIT",
            "dependency_text": dependency_text,
        },
        status_code=status,
    )


@router.get("/preview", response_class=HTMLResponse)
async def preview(request: Request) -> HTMLResponse:
    """FR-OUT-01: R0가 제공한 Report로 예시 결과 화면을 표시함."""
    report = sample_report()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"report": report, "counts": report.counts(),
                 "rows": report.sorted_rows()},
    )
