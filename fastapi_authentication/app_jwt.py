import jwt
import bcrypt
import time
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from database import get_db, init_db


app = FastAPI()
init_db()


SECRET_KEY = "codeverra-jwt-secret-key-change-this-in-production"


# The algorithm used for signing.
ALGORITHM = "HS256"

# Tokens expire after 30 minutes (1800 seconds).
ACCESS_TOKEN_EXPIRE_SECONDS = 1800

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_token(user_id: int, username: str) -> str:
    """
    Create a JWT token containing the user's information.

    The payload (claims) includes:
    - user_id: so we know who this token belongs to
    - username: for convenience (so we do not have to query the DB every time)
    - exp: expiration time (as a Unix timestamp)

    The token is signed with our SECRET_KEY using the HS256 algorithm.
    """
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": int(time.time()) + ACCESS_TOKEN_EXPIRE_SECONDS
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    print("Generated Token: ", token)
    return token


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    This function runs before every protected endpoint.

    FastAPI's OAuth2PasswordBearer extracts the token from the
    Authorization header (the part after "Bearer ").
    We then decode and verify the token.
    """
    try:
        # jwt.decode does THREE things:
        # 1. Decodes the Base64 payload
        # 2. Verifies the signature using our SECRET_KEY
        # 3. Checks that the token has not expired (exp claim)
        # If ANY of these fail, it raises an exception.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    except jwt.ExpiredSignatureError:
        # The token's exp time has passed
        raise HTTPException(status_code=401, detail="Token has expired")

    except jwt.InvalidTokenError:
        # The signature is invalid, the token is malformed, etc.
        raise HTTPException(status_code=401, detail="Invalid token")

    # Token is valid. Return the user information from the payload.
    return {"id": payload["user_id"], "username": payload["username"]}


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
def login(username: str, password: str):
    """
    Verify credentials and return a JWT token.

    This is the ONLY time the password is sent. After this,
    the client uses the token for all subsequent requests.
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

    # Create and return the token
    token = create_token(user["id"], user["username"])

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.post("/login")
def login(username: str, password: str):
    """
    Verify credentials and return a JWT token.

    This is the ONLY time the password is sent. After this,
    the client uses the token for all subsequent requests.
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

    # Create and return the token
    token = create_token(user["id"], user["username"])

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.post("/notes") # this should come from a payload not from the url
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
