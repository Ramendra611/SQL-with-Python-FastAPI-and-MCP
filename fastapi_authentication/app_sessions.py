import uuid
import bcrypt
from fastapi import FastAPI, HTTPException, Depends, Response, Cookie
from database import get_db, init_db

app = FastAPI()
init_db()

sessions = {} # this is simulating a session db. For this example we are using a in memory python dictionary


def get_current_user(session_id: str = Cookie(default = None)):
    '''
    We will check the session_id if it is existing in the database
    '''
    print(f"{sessions = }")
    if session_id is None: ## session_id was not sent
        raise HTTPException(status_code = 401, 
                            detail = "Not logged in!")

    user = sessions.get(session_id)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid. Please log in again."
        )

    return user

@app.post("/register")
def register(username: str, password: str):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed)
        )
        conn.commit()
        return {"message": f"User '{username}' created successfully"}
    except Exception:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()


@app.post("/login")
def login(username: str, password: str, response: Response):
    """
    The user sends their password exactly ONCE, here at login.
    After this, they never send it again.
    """
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username")

    if not bcrypt.checkpw(password.encode(), user["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid password")

    # Create a new session.
    # uuid4() generates a random unique string like
    # "a7f3b2c1-d9e8-4f5a-b6c7-8d9e0f1a2b3c"
    session_id = str(uuid.uuid4()) # generate a session_id

    # Store the session in our dictionary.
    # We store the user's id and username -- everything we need
    # to process future requests without touching the database.
    sessions[session_id] = {"id": user["id"], "username": user["username"]} # storing in the database
    print(f"{sessions = }")
    # Send the session ID to the client as a cookie.
    # httponly=True means JavaScript in the browser cannot read this
    # cookie. This prevents XSS attacks from stealing the session.
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True
    )

    return {"message": f"Welcome, {user['username']}!"}


@app.post("/logout")
def logout(session_id: str = Cookie(default=None)):
    """
    Destroy the session. The cookie on the client becomes meaningless.
    """
    if session_id and session_id in sessions:
        del sessions[session_id]
    print("After deleting session: ", sessions)
    return {"message": "Logged out"}


## CRUD operations 
@app.post("/notes")
def create_note(title: str, content: str,
                user: dict = Depends(get_current_user)):
    conn = get_db()
    conn.execute(
        "INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)",
        (user["id"], title, content)
    )
    conn.commit()
    conn.close()
    return {"message": "Note created"}


@app.get("/notes")
def get_notes(user: dict = Depends(get_current_user)):
    conn = get_db()
    notes = conn.execute(
        "SELECT * FROM notes WHERE user_id = ?", (user["id"],)
    ).fetchall()
    conn.close()
    return [dict(note) for note in notes]


@app.delete("/notes/{note_id}")
def delete_note(note_id: int, user: dict = Depends(get_current_user)):
    conn = get_db()
    result = conn.execute(
        "DELETE FROM notes WHERE id = ? AND user_id = ?",
        (note_id, user["id"])
    )
    conn.commit()
    conn.close()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"message": "Note deleted"}
