import sqlite3
import os
from datetime import datetime, timezone
from slugify import slugify

DB_PATH = os.path.join(os.path.dirname(__file__), "blog.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            slug TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL DEFAULT '',
            excerpt TEXT NOT NULL DEFAULT '',
            full_html TEXT NOT NULL DEFAULT '',
            category_id INTEGER,
            tags TEXT NOT NULL DEFAULT '',
            published INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_posts_slug ON posts(slug);
        CREATE INDEX IF NOT EXISTS idx_posts_published ON posts(published);
        CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category_id);
    """)

    # Migration: add full_html column if missing (upgrade from older schema)
    try:
        conn.execute("SELECT full_html FROM posts LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE posts ADD COLUMN full_html TEXT NOT NULL DEFAULT ''")
    conn.commit()
    conn.commit()
    conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_slug(title: str, exclude_id: int | None = None) -> str:
    base = slugify(title, max_length=80)
    if not base:
        base = "post"
    conn = get_db()
    slug = base
    counter = 1
    while True:
        row = conn.execute(
            "SELECT id FROM posts WHERE slug = ? AND id != ?",
            (slug, exclude_id or 0),
        ).fetchone()
        if not row:
            break
        slug = f"{base}-{counter}"
        counter += 1
    conn.close()
    return slug


# ── Categories ──

def create_category(name: str) -> dict:
    conn = get_db()
    slug = slugify(name, max_length=50)
    existing = conn.execute("SELECT id FROM categories WHERE slug = ?", (slug,)).fetchone()
    if existing:
        conn.close()
        return dict(existing)
    cur = conn.execute(
        "INSERT INTO categories (name, slug) VALUES (?, ?)", (name, slug)
    )
    conn.commit()
    cat = {"id": cur.lastrowid, "name": name, "slug": slug}
    conn.close()
    return cat


def get_categories() -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT c.*, COUNT(p.id) as post_count FROM categories c "
        "LEFT JOIN posts p ON p.category_id = c.id AND p.published = 1 "
        "GROUP BY c.id ORDER BY c.name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_category_by_slug(slug: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM categories WHERE slug = ?", (slug,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_category(cat_id: int):
    conn = get_db()
    conn.execute("UPDATE posts SET category_id = NULL WHERE category_id = ?", (cat_id,))
    conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()


# ── Posts ──

def create_post(
    title: str,
    content: str,
    excerpt: str = "",
    full_html: str = "",
    category_id: int | None = None,
    tags: str = "",
    published: bool = False,
) -> dict:
    conn = get_db()
    now = _now()
    slug = _make_slug(title)
    cur = conn.execute(
        "INSERT INTO posts (title, slug, content, excerpt, full_html, category_id, tags, published, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (title, slug, content, excerpt, full_html, category_id, tags, int(published), now, now),
    )
    conn.commit()
    post = dict(conn.execute("SELECT * FROM posts WHERE id = ?", (cur.lastrowid,)).fetchone())
    conn.close()
    return post


def update_post(
    post_id: int,
    title: str,
    content: str,
    excerpt: str = "",
    full_html: str = "",
    category_id: int | None = None,
    tags: str = "",
    published: bool = False,
) -> dict:
    conn = get_db()
    now = _now()
    existing = conn.execute("SELECT slug FROM posts WHERE id = ?", (post_id,)).fetchone()
    slug = _make_slug(title, exclude_id=post_id)
    conn.execute(
        "UPDATE posts SET title=?, slug=?, content=?, excerpt=?, full_html=?, category_id=?, tags=?, published=?, updated_at=? "
        "WHERE id=?",
        (title, slug, content, excerpt, full_html, category_id, tags, int(published), now, post_id),
    )
    conn.commit()
    post = dict(conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone())
    conn.close()
    return post


def delete_post(post_id: int):
    conn = get_db()
    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()


def get_post_by_id(post_id: int) -> dict | None:
    conn = get_db()
    row = conn.execute(
        "SELECT p.*, c.name as category_name, c.slug as category_slug "
        "FROM posts p LEFT JOIN categories c ON p.category_id = c.id "
        "WHERE p.id = ?", (post_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_post_by_slug(slug: str) -> dict | None:
    conn = get_db()
    row = conn.execute(
        "SELECT p.*, c.name as category_name, c.slug as category_slug "
        "FROM posts p LEFT JOIN categories c ON p.category_id = c.id "
        "WHERE p.slug = ? AND p.published = 1", (slug,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_posts(page: int = 1, per_page: int = 10, published_only: bool = True) -> dict:
    conn = get_db()
    where = "WHERE p.published = 1" if published_only else ""
    total = conn.execute(f"SELECT COUNT(*) FROM posts p {where}").fetchone()[0]
    offset = (page - 1) * per_page
    rows = conn.execute(
        f"SELECT p.*, c.name as category_name, c.slug as category_slug "
        f"FROM posts p LEFT JOIN categories c ON p.category_id = c.id "
        f"{where} ORDER BY p.created_at DESC LIMIT ? OFFSET ?",
        (per_page, offset),
    ).fetchall()
    conn.close()
    return {
        "posts": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
    }


def get_posts_by_category(category_slug: str, page: int = 1, per_page: int = 10) -> dict:
    conn = get_db()
    cat = conn.execute("SELECT * FROM categories WHERE slug = ?", (category_slug,)).fetchone()
    if not cat:
        conn.close()
        return {"posts": [], "total": 0, "page": 1, "per_page": per_page, "total_pages": 1, "category": None}
    cat = dict(cat)
    total = conn.execute(
        "SELECT COUNT(*) FROM posts WHERE category_id = ? AND published = 1", (cat["id"],)
    ).fetchone()[0]
    offset = (page - 1) * per_page
    rows = conn.execute(
        "SELECT p.*, c.name as category_name, c.slug as category_slug "
        "FROM posts p LEFT JOIN categories c ON p.category_id = c.id "
        "WHERE p.category_id = ? AND p.published = 1 "
        "ORDER BY p.created_at DESC LIMIT ? OFFSET ?",
        (cat["id"], per_page, offset),
    ).fetchall()
    conn.close()
    return {
        "posts": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
        "category": cat,
    }


def get_posts_by_tag(tag: str, page: int = 1, per_page: int = 10) -> dict:
    conn = get_db()
    total = conn.execute(
        "SELECT COUNT(*) FROM posts WHERE published = 1 AND (',' || tags || ',') LIKE ?",
        (f"%,{tag},%",),
    ).fetchone()[0]
    offset = (page - 1) * per_page
    rows = conn.execute(
        "SELECT p.*, c.name as category_name, c.slug as category_slug "
        "FROM posts p LEFT JOIN categories c ON p.category_id = c.id "
        "WHERE p.published = 1 AND (',' || p.tags || ',') LIKE ? "
        "ORDER BY p.created_at DESC LIMIT ? OFFSET ?",
        (f"%,{tag},%", per_page, offset),
    ).fetchall()
    conn.close()
    return {
        "posts": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total + per_page - 1) // per_page),
        "tag": tag,
    }


def get_all_tags() -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT tags FROM posts WHERE published = 1 AND tags != ''"
    ).fetchall()
    conn.close()
    tag_counts: dict[str, int] = {}
    for row in rows:
        for t in row["tags"].split(","):
            t = t.strip()
            if t:
                tag_counts[t] = tag_counts.get(t, 0) + 1
    return [{"name": k, "count": v} for k, v in sorted(tag_counts.items(), key=lambda x: -x[1])]


def get_recent_posts(limit: int = 5) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT p.title, p.slug, p.created_at, p.excerpt "
        "FROM posts p WHERE p.published = 1 "
        "ORDER BY p.created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
