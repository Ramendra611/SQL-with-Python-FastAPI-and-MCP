from fastapi import FastAPI, HTTPException
from database import get_db, init_db

app = FastAPI()

# create the tables if not existing
init_db()

## endpoints

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


@app.post("/notes")
def create_note(user_id: int, title: str, content: str):
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
def get_notes(user_id: int):
    """Get all notes for a user. Anyone can pass any user_id and read
    someone else's notes."""
    conn = get_db()
    notes = conn.execute(
        "SELECT * FROM notes WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(note) for note in notes]


@app.delete("/notes/{note_id}")
def delete_note(note_id: int):
    """Delete a note. Anyone can delete any note. No questions asked."""
    conn = get_db()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    return {"message": "Note deleted"}
