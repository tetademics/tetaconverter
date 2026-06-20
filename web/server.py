import asyncio
import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Request
from fastapi.responses import Response, JSONResponse
from fastapi.staticfiles import StaticFiles

from converter import (
    FORMAT_HANDLERS, FORMAT_MIME, FORMAT_EXT,
    image_convert, IMG_FORMATS, IMG_MIME,
    audio_convert, AUDIO_FORMATS, AUDIO_MIME,
    video_to_gif,
    spreadsheet_convert,
    document_convert,
)

from rate_limiter import check_rate_limit, record_conversion, get_rate_info

import blog_db
from blog_routes import router as blog_router
from pdf_tools import merge_pdfs, split_pdf, compress_pdf, get_pdf_info

blog_db.init_db()

app = FastAPI(title="Teta Converter")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(blog_router)

# In-memory store for batch conversion results
_conversion_results: dict[str, dict] = {}


@app.get("/")
async def index():
    return Response(
        content=(STATIC_DIR / "index.html").read_bytes(),
        media_type="text/html",
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/rate-limit")
async def rate_limit_info(request: Request):
    return get_rate_info(request)


@app.get("/api/blog/recent")
async def get_recent_blog_posts():
    posts = blog_db.get_recent_posts(limit=3)
    return posts


@app.get("/api/result/{result_id}")
async def get_result(result_id: str):
    r = _conversion_results.get(result_id)
    if not r:
        raise HTTPException(status_code=404, detail="Result not found or expired.")
    return Response(
        content=r["data"],
        media_type=r["mime"],
        headers={"Content-Disposition": f'attachment; filename="{r["name"]}"'},
    )


def _convert_file(input_path: str, filename: str, target_format: str, converter_type: str, **kwargs) -> tuple[bytes, str, str]:
    ext_map = {
        "pdf": FORMAT_EXT,
        "image": {fmt: f".{fmt}" for fmt in IMG_FORMATS},
        "audio": {fmt: f".{fmt}" for fmt in AUDIO_FORMATS},
        "video": {".gif": ".gif"},
        "spreadsheet": {"csv": ".csv", "tsv": ".tsv", "json": ".json", "xlsx": ".xlsx", "html": ".html", "markdown": ".md"},
        "document": {"pdf": ".pdf", "html": ".html"},
    }
    mime_map = {
        "pdf": FORMAT_MIME,
        "image": IMG_MIME,
        "audio": AUDIO_MIME,
        "video": {"gif": "image/gif"},
        "spreadsheet": {"csv": "text/csv", "tsv": "text/tab-separated-values", "json": "application/json", "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "html": "text/html", "markdown": "text/markdown"},
        "document": {"pdf": "application/pdf", "html": "text/html"},
    }

    stem = Path(filename).stem
    out_ext = ext_map[converter_type].get(target_format, f".{target_format}")
    mime = mime_map[converter_type].get(target_format, "application/octet-stream")

    if converter_type == "pdf":
        result = FORMAT_HANDLERS[target_format](input_path, str(Path(input_path).parent))
        data = result.read_bytes()
    elif converter_type == "image":
        data, mime = image_convert(input_path, target_format, kwargs.get("quality", 90), kwargs.get("width"), kwargs.get("height"))
    elif converter_type == "audio":
        data, mime = audio_convert(input_path, target_format, bitrate=kwargs.get("bitrate", "192k"))
    elif converter_type == "video":
        data, mime = video_to_gif(input_path, fps=kwargs.get("fps", 8), width=kwargs.get("width"), start=kwargs.get("start", 0), duration=kwargs.get("duration"))
    elif converter_type == "spreadsheet":
        data, mime, out_ext = spreadsheet_convert(input_path, target_format)
    elif converter_type == "document":
        data, mime, out_ext = document_convert(input_path, target_format)
    else:
        raise ValueError(f"Unknown converter type: {converter_type}")

    out_name = f"{stem}{out_ext}"
    return data, mime, out_name


@app.post("/api/convert")
async def batch_convert(
    request: Request,
    files: list[UploadFile] = File(...),
    format: str = Form("md"),
    converter_type: str = Form("pdf"),
    quality: int = Form(90),
    width: int = Form(0),
    height: int = Form(0),
    bitrate: str = Form("192k"),
    fps: int = Form(8),
    start: float = Form(0),
    duration: float = Form(0),
):
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files per batch.")

    rate = check_rate_limit(request)
    if not rate["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit reached. {rate['cooldown_seconds']}s cooldown remaining.",
        )

    tmpdir = tempfile.mkdtemp(prefix="teta_batch_")
    results = []

    try:
        for i, file in enumerate(files):
            if not rate["allowed"]:
                results.append({
                    "index": i,
                    "filename": file.filename,
                    "success": False,
                    "error": "Rate limit reached.",
                })
                continue

            try:
                file_path = Path(tmpdir) / file.filename
                with open(file_path, "wb") as f:
                    f.write(await file.read())

                kwargs = {}
                if converter_type == "image":
                    kwargs = {"quality": quality, "width": width or None, "height": height or None}
                elif converter_type == "audio":
                    kwargs = {"bitrate": bitrate}
                elif converter_type == "video":
                    kwargs = {"fps": fps, "width": width or None, "start": start, "duration": duration if duration > 0 else None}

                data, mime, out_name = _convert_file(
                    str(file_path), file.filename, format, converter_type, **kwargs
                )

                result_id = uuid.uuid4().hex[:12]
                _conversion_results[result_id] = {"data": data, "mime": mime, "name": out_name}

                size_kb = len(data) / 1024
                results.append({
                    "index": i,
                    "filename": file.filename,
                    "success": True,
                    "result_id": result_id,
                    "output_name": out_name,
                    "size_kb": round(size_kb, 1),
                })

                record_conversion(request)
                rate = check_rate_limit(request)

            except Exception as e:
                results.append({
                    "index": i,
                    "filename": file.filename,
                    "success": False,
                    "error": str(e),
                })

        return JSONResponse(content={
            "results": results,
            "rate_limit": {
                "remaining": rate["remaining"],
                "limit": rate["limit"],
                "cooldown": rate["cooldown_seconds"],
            },
        })
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ─── PDF Tools ────────────────────────────────────────────────────────────────

@app.get("/pdf-tools")
async def pdf_tools_page():
    return Response(
        content=(STATIC_DIR / "pdf-tools.html").read_bytes(),
        media_type="text/html",
    )


@app.post("/api/pdf/merge")
async def api_merge_pdfs(
    request: Request,
    files: list[UploadFile] = File(...),
):
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="At least 2 PDF files required to merge.")
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 files per merge.")

    rate = check_rate_limit(request)
    if not rate["allowed"]:
        raise HTTPException(status_code=429, detail=f"Rate limit reached. {rate['cooldown_seconds']}s cooldown remaining.")

    tmpdir = tempfile.mkdtemp(prefix="teta_merge_")
    try:
        paths = []
        for file in files:
            if not file.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"{file.filename} is not a PDF file.")
            file_path = Path(tmpdir) / file.filename
            with open(file_path, "wb") as f:
                f.write(await file.read())
            paths.append(str(file_path))

        data, mime = merge_pdfs(paths)
        result_id = uuid.uuid4().hex[:12]
        _conversion_results[result_id] = {"data": data, "mime": mime, "name": "merged.pdf"}
        record_conversion(request)
        rate = check_rate_limit(request)

        return JSONResponse(content={
            "success": True,
            "result_id": result_id,
            "output_name": "merged.pdf",
            "size_kb": round(len(data) / 1024, 1),
            "rate_limit": {
                "remaining": rate["remaining"],
                "limit": rate["limit"],
                "cooldown": rate["cooldown_seconds"],
            },
        })
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@app.post("/api/pdf/split")
async def api_split_pdf(
    request: Request,
    file: UploadFile = File(...),
    ranges: str = Form(""),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    rate = check_rate_limit(request)
    if not rate["allowed"]:
        raise HTTPException(status_code=429, detail=f"Rate limit reached. {rate['cooldown_seconds']}s cooldown remaining.")

    tmpdir = tempfile.mkdtemp(prefix="teta_split_")
    try:
        file_path = Path(tmpdir) / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())

        split_ranges = []
        if ranges:
            import re as _re
            parts = _re.split(r"[;,]", ranges)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                if "-" in part:
                    s, e = part.split("-", 1)
                    split_ranges.append((int(s.strip()), int(e.strip())))
                elif part.isdigit():
                    n = int(part.strip())
                    split_ranges.append((n, n))

        if not split_ranges:
            info = get_pdf_info(str(file_path))
            total = info["pages"]
            mid = total // 2
            split_ranges = [(1, mid), (mid + 1, total)]

        results_list = split_pdf(str(file_path), split_ranges)
        result_ids = []
        for data, mime, name in results_list:
            rid = uuid.uuid4().hex[:12]
            _conversion_results[rid] = {"data": data, "mime": mime, "name": name}
            result_ids.append({"result_id": rid, "output_name": name, "size_kb": round(len(data) / 1024, 1)})

        record_conversion(request)
        rate = check_rate_limit(request)

        return JSONResponse(content={
            "success": True,
            "results": result_ids,
            "rate_limit": {
                "remaining": rate["remaining"],
                "limit": rate["limit"],
                "cooldown": rate["cooldown_seconds"],
            },
        })
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@app.post("/api/pdf/compress")
async def api_compress_pdf(
    request: Request,
    file: UploadFile = File(...),
    quality: str = Form("medium"),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    rate = check_rate_limit(request)
    if not rate["allowed"]:
        raise HTTPException(status_code=429, detail=f"Rate limit reached. {rate['cooldown_seconds']}s cooldown remaining.")

    tmpdir = tempfile.mkdtemp(prefix="teta_compress_")
    try:
        file_path = Path(tmpdir) / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())

        original_size = Path(file_path).stat().st_size

        data, mime = compress_pdf(str(file_path), quality)
        result_id = uuid.uuid4().hex[:12]
        _conversion_results[result_id] = {"data": data, "mime": mime, "name": f"compressed_{file.filename}"}
        record_conversion(request)
        rate = check_rate_limit(request)

        compressed_size = len(data)
        reduction = round((1 - compressed_size / original_size) * 100, 1) if original_size > 0 else 0

        return JSONResponse(content={
            "success": True,
            "result_id": result_id,
            "output_name": f"compressed_{file.filename}",
            "size_kb": round(compressed_size / 1024, 1),
            "original_size_kb": round(original_size / 1024, 1),
            "reduction_percent": reduction,
            "rate_limit": {
                "remaining": rate["remaining"],
                "limit": rate["limit"],
                "cooldown": rate["cooldown_seconds"],
            },
        })
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
