import bcrypt
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from database import get_db, init_db

app = FastAPI()

# create the tables if not existing
init_db()

security = HTTPBasic()


def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """
    This function is the heart of Basic Auth.

    FastAPI's HTTPBasic scheme does two things:
    1. It reads the Authorization header from the request
    2. It decodes the Base64 string and extracts username and password
    3. It passes them to us as an HTTPBasicCredentials object

    Our job: verify these credentials against the database.
    If valid, return the user. If not, raise a 401.
    """
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (credentials.username,)
    ).fetchone()
    conn.close()

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username")

    # Compare the password the user sent with the hash in the database
    if not bcrypt.checkpw(credentials.password.encode(),
                          user["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid password")

    # Return the user as a dictionary. This will be available
    # in every endpoint that depends on this function.
    return dict(user)



# endpoints
@app.post("/register")
def register(username, password): # store the password as hash
    '''
    Take the username and password and run a query to create a new user
    if the username doesnt exist
    '''
    # Hash the password before storing it
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )
        conn.commit()
        return {"message": f"User '{username}' created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()


@app.post("/notes")
def create_note(title: str, content: str, user : dict = Depends(get_current_user)):
    """Create a new note. But wait -- anyone can pass any user_id."""
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
    """
    No user_id parameter. We automatically return only the notes
    belonging to the authenticated user. You cannot see anyone
    else's notes because the query filters by YOUR user ID.
    """
    conn = get_db()
    notes = conn.execute(
        "SELECT * FROM notes WHERE user_id = ?", (user["id"],)
    ).fetchall()
    conn.close()
    return [dict(note) for note in notes]


@app.delete("/notes/{note_id}")
def delete_note(note_id: int, user: dict = Depends(get_current_user)):
    """
    We only delete the note if it belongs to the authenticated user.
    The WHERE clause checks both the note ID and the user ID.
    You cannot delete someone else's notes.
    """
    conn = get_db()
    result = conn.execute(
        "DELETE FROM notes WHERE id = ? AND user_id = ?",
        (note_id, user["id"])
    )
    conn.commit()
    conn.close()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail="Note not found or you do not own it"
        )
    return {"message": "Note deleted"}
