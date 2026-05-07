from fastapi import FastAPI, HTTPException, Header, Depends
from database import get_db, init_db

app = FastAPI()

# create the tables if not existing
init_db()

API_KEY = "codeverra-secret-key-2025"


def verify_api_key(x_api_key: str = Header()):
    """
    This function checks if the client sent a valid API key.

    How it works:
    - FastAPI sees the parameter name 'x_api_key' and the type hint Header()
    - It automatically looks for a header called 'X-Api-Key' in the request
      (FastAPI converts underscores to hyphens and handles case)
    - If the header is missing, FastAPI returns a 422 error automatically
    - If the header is present, we check if the value matches our key
    """
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

# endpoints
@app.post("/register")
def register(username, password):
    '''
    Take the username and password and run a query to create a new user
    if the username doesnt exist
    '''
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        return {"message": f"User '{username}' created successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()


# @app.post("/notes")
# def create_note(user_id: int, title: str, content: str, api_key : str = Header(alias = "X-API-KEY")):
#     """Create a new note. But wait -- anyone can pass any user_id."""

#     verify_api_key(api_key) # this line can be avoided if we use Depends function for authentication
#     conn = get_db()
#     conn.execute(
#         "INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)",
#         (user_id, title, content)
#     )
#     conn.commit()
#     conn.close()
#     return {"message": "Note created"}


@app.post("/notes")
def create_note(user_id: int, title: str, content: str, _ = Depends(verify_api_key)):
    """Create a new note. But wait -- anyone can pass any user_id."""
    conn = get_db()
    conn.execute(
        "INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)",
        (user_id, title, content)
    )
    conn.commit()
    conn.close()
    return {"message": "Note created"}


@app.get("/notes")
def get_notes(user_id: int, _ = Depends(verify_api_key)):
    """Get all notes for a user. Anyone can pass any user_id and read
    someone else's notes."""
    # verify_api_key(api_key)
    conn = get_db()
    notes = conn.execute(
        "SELECT * FROM notes WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(note) for note in notes]


@app.delete("/notes/{note_id}")
def delete_note(note_id: int, api_key: str = Header(alias="X-API-KEY")):
    """Delete a note. Anyone can delete any note. No questions asked."""
    verify_api_key(api_key)
    conn = get_db()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    return {"message": "Note deleted"}
