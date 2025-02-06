from os import getenv
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import SQLModel, Field, Session, create_engine, select
from pydantic import BaseModel

DATABASE_URL = "sqlite:///database.db"

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str

class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int
    content: str

engine = create_engine(DATABASE_URL, echo=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(lifespan=lifespan)

def get_session():
    with Session(engine) as session:
        yield session

class CreatePostModel(BaseModel):
    title: str
    content: str

@app.post("/posts", response_model=CreatePostModel)
@app.put("/posts", response_model=CreatePostModel)
def create_post(post: CreatePostModel, session: Session = Depends(get_session)):
    post = Post(title=post.title, content=post.content)
    session.add(post)
    session.commit()
    session.refresh(post)
    return post

@app.get("/posts", response_model=List[Post])
def read_posts(session: Session = Depends(get_session)):
    posts = session.exec(select(Post)).all()
    return posts

@app.get("/posts/{post_id}", response_model=Post)
def read_post(post_id: int, session: Session = Depends(get_session)):
    post = session.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@app.put("/posts/{post_id}", response_model=Post)
def replace_post(post_id: int, post: CreatePostModel, session: Session = Depends(get_session)):
    db_post = session.get(Post, post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    post_data = post.dict()
    db_post.title = post_data["title"]
    db_post.content = post_data["content"]
    session.add(db_post)
    session.commit()
    session.refresh(db_post)
    return db_post

@app.patch("/posts/{post_id}", response_model=Post)
def update_post(post_id: int, patch_data: dict, session: Session = Depends(get_session)):
    db_post = session.get(Post, post_id)
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    for key, value in patch_data.items():
        setattr(db_post, key, value)
    session.add(db_post)
    session.commit()
    session.refresh(db_post)
    return db_post

@app.delete("/posts/{post_id}")
def delete_post(post_id: int, session: Session = Depends(get_session)):
    post = session.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    session.delete(post)
    session.commit()
    return {"message": "Post deleted successfully"}

@app.get("/posts/{post_id}/comments", response_model=List[Comment])
def read_post_comments(post_id: int, session: Session = Depends(get_session)):
    comments = session.exec(select(Comment).where(Comment.post_id == post_id)).all()
    return comments

class CreateCommentModel(BaseModel):
    post_id: int
    content: str

@app.post("/comments", response_model=CreateCommentModel)
@app.put("/comments", response_model=CreateCommentModel)
def create_comment(comment: CreateCommentModel, session: Session = Depends(get_session)):
    comment = Comment(post_id=comment.post_id, content=comment.content)
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment

@app.get("/comments", response_model=List[Comment])
def read_comments(session: Session = Depends(get_session)):
    comments = session.exec(select(Comment)).all()
    return comments

@app.get("/comments/{comment_id}", response_model=Comment)
def read_comment(comment_id: int, session: Session = Depends(get_session)):
    comment = session.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment

@app.put("/comments/{comment_id}", response_model=Comment)
def replace_comment(comment_id: int, comment: CreateCommentModel, session: Session = Depends(get_session)):
    db_comment = session.get(Comment, comment_id)
    if db_comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    comment_data = comment.dict()
    db_comment.post_id = comment_data["post_id"]
    db_comment.content = comment_data["content"]
    session.add(db_comment)
    session.commit()
    session.refresh(db_comment)
    return db_comment

@app.patch("/comments/{comment_id}", response_model=Comment)
def update_comment(comment_id: int, patch_data: dict, session: Session = Depends(get_session)):
    db_comment = session.get(Comment, comment_id)
    if db_comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    for key, value in patch_data.items():
        setattr(db_comment, key, value)
    session.add(db_comment)
    session.commit()
    session.refresh(db_comment)
    return db_comment

@app.delete("/comments/{comment_id}")
def delete_comment(comment_id: int, session: Session = Depends(get_session)):
    comment = session.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    session.delete(comment)
    session.commit()
    return {"message": "Comment deleted successfully"}

@app.get("/comments/{comment_id}/post", response_model=Post)
def read_comment_post(comment_id: int, session: Session = Depends(get_session)):
    comment = session.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    post = session.get(Post, comment.post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

if __name__ == "__main__":
    import uvicorn

    host = getenv("HOST", "127.0.0.1")
    port = getenv("PORT", 8000)

    try:
        port = int(port)
    except ValueError:
        port = 8000

    uvicorn.run(app, host="127.0.0.1", port=8000)