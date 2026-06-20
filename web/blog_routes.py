import io
import html
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse, JSONResponse
from fastapi.templating import Jinja2Templates

import blog_db
from blog_auth import (
    verify_password, create_session, delete_session, validate_session,
    require_admin_redirect, ADMIN_USERNAME,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def _ctx(request: Request, **kwargs) -> dict:
    base = {
        "request": request,
        "categories": blog_db.get_categories(),
        "tags": blog_db.get_all_tags(),
        "recent_posts": blog_db.get_recent_posts(5),
    }
    base.update(kwargs)
    return base


# ── Public Routes ──

@router.get("/blog", response_class=HTMLResponse)
def blog_list(request: Request, page: int = 1):
    data = blog_db.get_posts(page=page, per_page=10, published_only=True)
    return templates.TemplateResponse(request, "blog_list.html", context=_ctx(request, **data))


@router.get("/blog/{slug}", response_class=HTMLResponse)
def blog_post(request: Request, slug: str):
    post = blog_db.get_post_by_slug(slug)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse(request, "blog_post.html", context=_ctx(request, post=post))


@router.get("/blog/category/{slug}", response_class=HTMLResponse)
def blog_category(request: Request, slug: str, page: int = 1):
    data = blog_db.get_posts_by_category(slug, page=page)
    if not data.get("category"):
        raise HTTPException(status_code=404, detail="Category not found")
    return templates.TemplateResponse(request, "blog_category.html", context=_ctx(request, **data))


@router.get("/blog/tag/{name}", response_class=HTMLResponse)
def blog_tag(request: Request, name: str, page: int = 1):
    data = blog_db.get_posts_by_tag(name, page=page)
    return templates.TemplateResponse(request, "blog_tag.html", context=_ctx(request, **data))


@router.get("/blog/rss", response_class=PlainTextResponse)
def blog_rss(request: Request):
    data = blog_db.get_posts(page=1, per_page=20, published_only=True)
    base_url = str(request.base_url).rstrip("/")
    items = ""
    for p in data["posts"]:
        pub_date = datetime.fromisoformat(p["created_at"]).strftime("%a, %d %b %Y %H:%M:%S +0000")
        items += f"""    <item>
      <title>{html.escape(p['title'])}</title>
      <link>{base_url}/blog/{p['slug']}</link>
      <guid>{base_url}/blog/{p['slug']}</guid>
      <pubDate>{pub_date}</pubDate>
      <description>{html.escape(p['excerpt'] or p['content'][:200])}</description>
    </item>
"""
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Teta Converter Blog</title>
    <link>{base_url}/blog</link>
    <description>Tutorials, tips, and updates about Teta Converter</description>
    <language>en</language>
{items}  </channel>
</rss>"""
    return PlainTextResponse(content=rss, media_type="application/rss+xml")


# ── Admin Routes ──

@router.post("/admin/upload", response_class=JSONResponse)
async def admin_upload_file(
    request: Request,
    file: UploadFile = File(...),
):
    redirect = require_admin_redirect(request)
    if redirect:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ("md", "html", "htm", "txt"):
        return JSONResponse({"error": "Unsupported file type. Use .md, .html, or .txt"}, status_code=400)

    content_bytes = await file.read()
    try:
        content_str = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return JSONResponse({"error": "File must be UTF-8 encoded"}, status_code=400)

    title = filename.rsplit(".", 1)[0] if "." in filename else filename

    if ext in ("html", "htm"):
        import re
        title_match = re.search(r"<title[^>]*>(.*?)</title>", content_str, re.DOTALL | re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
        else:
            h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", content_str, re.DOTALL | re.IGNORECASE)
            if h1_match:
                title = re.sub(r"<[^>]+>", "", h1_match.group(1)).strip()

    if ext == "md":
        import markdown
        html_content = markdown.markdown(content_str, extensions=["tables", "fenced_code"])
        return JSONResponse({"title": title, "content": html_content, "source": "md"})
    elif ext in ("html", "htm"):
        import re
        body = content_str
        body_match = re.search(r"<body[^>]*>(.*?)</body>", content_str, re.DOTALL | re.IGNORECASE)
        if body_match:
            body = body_match.group(1)
        return JSONResponse({
            "title": title,
            "content": body.strip(),
            "full_html": content_str,
            "source": "html",
        })
    elif ext == "txt":
        escaped = content_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        html_content = f"<p>{escaped.replace(chr(10), '</p><p>')}</p>"
        return JSONResponse({"title": title, "content": html_content, "source": "txt"})

    return JSONResponse({"error": "Unexpected error"}, status_code=500)

@router.get("/admin/login", response_class=HTMLResponse)
def admin_login_form(request: Request):
    token = request.cookies.get("blog_session")
    if validate_session(token):
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse(request, "admin_login.html", context={
        "error": None,
        "categories": [],
        "tags": [],
        "recent_posts": [],
    })


@router.post("/admin/login")
def admin_login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if username != ADMIN_USERNAME or not verify_password(password):
        return templates.TemplateResponse(request, "admin_login.html", context={
            "error": "Invalid credentials",
            "categories": [],
            "tags": [],
            "recent_posts": [],
        })
    token = create_session()
    resp = RedirectResponse(url="/admin", status_code=303)
    resp.set_cookie("blog_session", token, httponly=True, max_age=86400 * 7)
    return resp


@router.get("/admin/logout")
def admin_logout(request: Request):
    token = request.cookies.get("blog_session")
    if token:
        delete_session(token)
    resp = RedirectResponse(url="/admin/login", status_code=303)
    resp.delete_cookie("blog_session")
    return resp


@router.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    redirect = require_admin_redirect(request)
    if redirect:
        return redirect
    data = blog_db.get_posts(page=1, per_page=100, published_only=False)
    return templates.TemplateResponse(request, "admin_posts.html", context=_ctx(request, **data))


@router.get("/admin/post/new", response_class=HTMLResponse)
def admin_new_post_form(request: Request):
    redirect = require_admin_redirect(request)
    if redirect:
        return redirect
    return templates.TemplateResponse(request, "admin_post_form.html", context=_ctx(request, post=None))


@router.post("/admin/post/new")
def admin_create_post(
    request: Request,
    title: str = Form(...),
    content: str = Form(""),
    excerpt: str = Form(""),
    full_html: str = Form(""),
    category: str = Form(""),
    tags: str = Form(""),
    published: str = Form(""),
):
    redirect = require_admin_redirect(request)
    if redirect:
        return redirect
    category_id = None
    if category.strip():
        cat = blog_db.create_category(category.strip())
        category_id = cat["id"]
    post = blog_db.create_post(
        title=title, content=content, excerpt=excerpt, full_html=full_html,
        category_id=category_id, tags=tags,
        published=published == "on",
    )
    return RedirectResponse(url=f"/admin/post/{post['id']}/edit", status_code=303)


@router.get("/admin/post/{post_id}/edit", response_class=HTMLResponse)
def admin_edit_post_form(request: Request, post_id: int):
    redirect = require_admin_redirect(request)
    if redirect:
        return redirect
    post = blog_db.get_post_by_id(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse(request, "admin_post_form.html", context=_ctx(request, post=post))


@router.post("/admin/post/{post_id}/edit")
def admin_update_post(
    request: Request,
    post_id: int,
    title: str = Form(...),
    content: str = Form(""),
    excerpt: str = Form(""),
    full_html: str = Form(""),
    category: str = Form(""),
    tags: str = Form(""),
    published: str = Form(""),
):
    redirect = require_admin_redirect(request)
    if redirect:
        return redirect
    category_id = None
    if category.strip():
        cat = blog_db.create_category(category.strip())
        category_id = cat["id"]
    blog_db.update_post(
        post_id=post_id, title=title, content=content, excerpt=excerpt, full_html=full_html,
        category_id=category_id, tags=tags,
        published=published == "on",
    )
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/admin/post/{post_id}/delete")
def admin_delete_post(request: Request, post_id: int):
    redirect = require_admin_redirect(request)
    if redirect:
        return redirect
    blog_db.delete_post(post_id)
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/admin/post/{post_id}/toggle")
def admin_toggle_publish(request: Request, post_id: int):
    redirect = require_admin_redirect(request)
    if redirect:
        return redirect
    post = blog_db.get_post_by_id(post_id)
    if post:
        blog_db.update_post(
            post_id=post_id, title=post["title"], content=post["content"],
            excerpt=post["excerpt"], full_html=post.get("full_html", ""),
            category_id=post["category_id"],
            tags=post["tags"], published=not bool(post["published"]),
        )
    return RedirectResponse(url="/admin", status_code=303)


@router.post("/admin/category/{cat_id}/delete")
def admin_delete_category(request: Request, cat_id: int):
    redirect = require_admin_redirect(request)
    if redirect:
        return redirect
    blog_db.delete_category(cat_id)
    return RedirectResponse(url="/admin", status_code=303)
