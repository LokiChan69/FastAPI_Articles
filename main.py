from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import sqlite3
import uvicorn
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware




class ArticleCreate(BaseModel):
    title: str
    content: str


def get_db():
    conn = sqlite3.connect("articles.db")
    conn.row_factory = sqlite3.Row
    return conn

@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()
    yield
app = FastAPI(lifespan=lifespan)

# Позволяет любому источнику обращаться к API (в разработке)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или укажи конкретный адрес вместо "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "Article API is working"}

@app.post("/articles")
def create_article(article: ArticleCreate):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO articles (title, content) VALUES (?, ?)",
        (article.title, article.content)
    )
    conn.commit()
    article_id = cursor.lastrowid
    conn.close()
    return {"id": article_id, "message": "Статья создана"}

@app.get("/articles")
def get_all_articles():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content FROM articles")
    rows = cursor.fetchall()
    conn.close()
    return {"articles": [dict(row) for row in rows]}

@app.get("/articles/{article_id}")
def get_article(article_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, content FROM articles WHERE id = ?", (article_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    return dict(row)

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)
