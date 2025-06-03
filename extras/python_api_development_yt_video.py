from random import randrange
import time
from typing import Optional
from fastapi import FastAPI,Response,status,HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

app=FastAPI()

class Post(BaseModel):
    title:str
    content:str
    published:bool = True
    rating:Optional[int] = None

while True:
    try:
        conn=psycopg2.connect(
            database="fastapi",
            user="postgres",
            password="12122005",
            host="localhost",
            cursor_factory=RealDictCursor
            )
        cursor=conn.cursor()
        print("Database successfully connected!")
        break
    except Exception as error:
        print("Failed connecting to the database")
        print("The error is",error)
        time.sleep(2)

        
my_posts=[{"title":"This is the title 1","content":"This is the content 1","id":1},
          {"title":"This is the title 2","content":"This is the content 2","id":2}]

def find_post(id):
    for i in my_posts:
        if i["id"] == id:
            return i

def find_post_to_del(id):
    for i,p in enumerate(my_posts):
        if p["id"]==id:
            return i
        
@app.get("/")
def read_root():
    return {"Heyy!": "Welcome to this fucking world!!"}

@app.get("/get_posts")
def get_posts():
    cursor.execute("""SELECT * FROM posts""")
    posts = cursor.fetchall()
    return{"Data": posts}

@app.post("/create_posts",status_code=status.HTTP_201_CREATED)
def create_posts(new_post:Post):
    cursor.execute("""INSERT INTO posts(title,content,published) VALUES(%s,%s,%s) RETURNING *""",
                   (new_post.title,new_post.content,new_post.published))
    new_postt=cursor.fetchone()
    conn.commit()
    return{"Added data": new_postt}

@app.get("/get_posts/latest")
def latest_posts():
    cursor.execute("""SELECT * FROM posts""")
    posts = cursor.fetchall()
    post=posts[-1]
    return {"Latest one is " : post}

@app.get("/get_posts/{id}")
def get_specific_posts(id: int):
    cursor.execute("""SELECT * FROM posts WHERE id = %s""", (str(id),))
    got_post = cursor.fetchone()
    print(got_post)
    if not got_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The post with id {id} doesn't exist"
        )
    return {"post_details": got_post}


@app.delete("/get_posts/{id}")
def delete_post(id:int):
    cursor.execute("""DELETE FROM posts WHERE id = %s RETURNING *""",(str(id),))
    deleted_post = cursor.fetchone()
    conn.commit()
    if deleted_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The post with {id} is not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@app.put("/get_posts/{id}")
def update_posts(id:int,post:Post):
    cursor.execute("""UPDATE posts SET title = %s,content = %s, published = %s WHERE id = %s RETURNING *""",
                   (post.title,post.content,post.published,str(id)))
    updated_post = cursor.fetchone()
    conn.commit()
    if updated_post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"The post with {id} is not found")
    return {"Data":updated_post}

