import io
from pypdf import PdfReader, PdfWriter


def merge_pdfs(pdf_paths: list[str]) -> tuple[bytes, str]:
    writer = PdfWriter()
    for path in pdf_paths:
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    buf = io.BytesIO()
    writer.write(buf)
    writer.close()
    return buf.getvalue(), "application/pdf"


def split_pdf(pdf_path: str, ranges: list[tuple[int, int]]) -> list[tuple[bytes, str, str]]:
    reader = PdfReader(pdf_path)
    total = len(reader.pages)
    results = []

    for i, (start, end) in enumerate(ranges):
        s = max(0, start - 1)
        e = min(total, end)
        if s >= e:
            continue

        writer = PdfWriter()
        for page_num in range(s, e):
            writer.add_page(reader.pages[page_num])

        buf = io.BytesIO()
        writer.write(buf)
        writer.close()

        name = f"split_{i+1}_pages_{start}-{end}.pdf"
        results.append((buf.getvalue(), "application/pdf", name))

    return results


def compress_pdf(pdf_path: str, quality: str = "medium") -> tuple[bytes, str]:
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    for page in writer.pages:
        page.compress_content_streams()

    if reader.metadata:
        writer.add_metadata({k: v for k, v in reader.metadata.items() if v})

    buf = io.BytesIO()
    writer.write(buf)
    writer.close()
    return buf.getvalue(), "application/pdf"


def get_pdf_info(pdf_path: str) -> dict:
    reader = PdfReader(pdf_path)
    info = {
        "pages": len(reader.pages),
        "title": reader.metadata.title if reader.metadata else None,
        "author": reader.metadata.author if reader.metadata else None,
    }
    return info
