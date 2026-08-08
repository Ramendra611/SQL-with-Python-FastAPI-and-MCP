# The Complete Guide to Authentication in FastAPI: From Zero to Production

---

**Module 4, Part 3: Authentication Deep Dive**
**Course:** SQL with Python, FastAPI and MCP
**Platform:** Codeverra (learn.codeverra.com)

---

## Table of Contents

- [What This Guide Is About](#what-this-guide-is-about)
- [The Application We Will Build (And Break)](#the-application-we-will-build-and-break)
- [Method 1: API Key Authentication](#method-1-api-key-authentication)
- [Method 2: HTTP Basic Authentication](#method-2-http-basic-authentication)
- [Method 3: Session-Based Authentication (Cookies)](#method-3-session-based-authentication-cookies)
- [Method 4: JWT Authentication (JSON Web Tokens)](#method-4-jwt-authentication-json-web-tokens)
- [Method 5: OAuth2 (Delegated Authentication)](#method-5-oauth2-delegated-authentication)
- [Choosing the Right Authentication Method](#choosing-the-right-authentication-method)
- [Frequently Asked Questions and Common Doubts](#frequently-asked-questions-and-common-doubts)
- [Summary: The Full Journey](#summary-the-full-journey)

---

## What This Guide Is About

You have built a FastAPI application. It has endpoints. It works. But right now, anyone in the world can hit your API and do whatever they want. Read any data. Delete any record. Pretend to be anyone.

That is not an application. That is an open database with a fancy door.

Authentication is how you fix this. It is how your API answers the most fundamental question in software: **"Who are you, and can you prove it?"**

This guide does not just show you how to add authentication. It walks you through five different approaches, in the order they were invented, each one solving a problem the previous one could not. By the end, you will not just know how to implement JWT authentication (which is what most modern APIs use). You will understand why JWT exists, what it replaced, what tradeoffs it makes, and when to choose something else entirely.

We will build the same application five times, each time with a different authentication method. Same database. Same endpoints. Different security. This way, the only thing that changes between examples is the authentication layer, and you can see exactly what each approach adds.

---

## The Application We Will Build (And Break)

Before we add any authentication, we need an application to protect. We are going to build a simple notes app. Users can create notes, read their notes, and delete their notes. That is it.

We will use SQLite with Python's built-in `sqlite3` module for storage. Two tables: `users` and `notes`. No ORMs, no Pydantic models, no fancy validation. The focus is entirely on authentication.

### Setting Up the Database

Let us start with a small helper file that creates and connects to our database. Every authentication example in this guide will import from this file, so we write it once.

```python
# database.py -- Shared database setup for all authentication examples

import sqlite3

DATABASE = "notes.db"

def get_db():
    """Create a connection to our SQLite database."""
    conn = sqlite3.connect(DATABASE)
    # This makes rows behave like dictionaries instead of tuples.
    # So we can write row["title"] instead of row[0].
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create the tables if they do not exist yet."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()
```

Two tables. `users` has an id, a unique username, and a password. `notes` has an id, a user_id (who owns this note), a title, and content. The `FOREIGN KEY` links each note to its owner.

We call `init_db()` when the app starts. If the tables already exist, `CREATE TABLE IF NOT EXISTS` does nothing. Clean and simple.

### Version 0: The Unprotected App

Here is our notes app with zero authentication. Read every line. Understand what it does. This is the base that we will add authentication to in every section that follows.

```python
# app_no_auth.py -- The notes app with NO authentication
# Anyone can do anything. This is the "before" picture.

from fastapi import FastAPI, HTTPException
from database import get_db, init_db

app = FastAPI()

# Create tables when the app starts
init_db()


# ──────────────────────────────────────────────
# User registration
# ──────────────────────────────────────────────

@app.post("/register")
def register(username: str, password: str):
    """Create a new user account."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        return {"message": f"User '{username}' created successfully"}
    except Exception:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()


# ──────────────────────────────────────────────
# Notes CRUD
# ──────────────────────────────────────────────

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
```

Run this with `uvicorn app_no_auth:app --reload` and open `http://localhost:8000/docs` to see the Swagger UI.

Now, look at the problems.

The `create_note` endpoint takes a `user_id` as a parameter. That means I can create notes under your account by passing your user_id. There is nothing stopping me.

The `get_notes` endpoint also takes a `user_id`. I can read anyone's notes by guessing or iterating through user IDs. Your private journal? I just need to call `GET /notes?user_id=1`, then `user_id=2`, then `user_id=3`, until I find yours.

The `delete_note` endpoint does not even check who is deleting. I can delete any note in the system.

The `register` endpoint stores passwords in plain text. If someone gets access to the database file, they have every user's password.

This is not a secure application. This is a demonstration of everything that can go wrong. Let us fix it, one step at a time.

---

## Method 1: API Key Authentication

### The Idea

An API key is the simplest form of authentication. It is a secret string that the client must send with every request. If the string matches what the server expects, the request is allowed. If not, it is rejected.

You have used API keys before, even if you did not think of them that way. When you sign up for the OpenAI API, you get a key like `sk-proj-abc123...`. When you use Google Maps in your app, you get a key like `AIzaSyD...`. These are API keys.

The idea is straightforward: the server generates a secret key, gives it to the client, and the client proves it is authorized by including that key in every request.

### Where Does the Key Go?

There are three common ways to send an API key:

**As a query parameter:** `GET /notes?api_key=my-secret-key`
This is the simplest but the worst. Query parameters show up in browser history, server logs, and URL sharing. Your secret key ends up in places you did not intend.

**As a custom header:** `X-API-Key: my-secret-key`
This is better. Headers do not appear in URLs or browser history. The `X-` prefix is a convention for custom headers (it used to be a formal rule, now it is just a convention that stuck).

**As an Authorization header:** `Authorization: Bearer my-secret-key`
This is the most standard approach. The `Authorization` header is built into HTTP for exactly this purpose.

We will use the header approach because it is the cleanest.

### The Implementation

Let us add API key authentication to our notes app. For simplicity, we will use a single API key that all clients share. Later methods will move to per-user authentication.

```python
# app_api_key.py -- Notes app protected with an API key

from fastapi import FastAPI, HTTPException, Header
from database import get_db, init_db

app = FastAPI()
init_db()

# In a real application, this would be stored in an environment variable,
# not hardcoded. We hardcode it here for clarity.
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


# ──────────────────────────────────────────────
# User registration -- no API key needed
# (you need to be able to register without already having a key)
# ──────────────────────────────────────────────

@app.post("/register")
def register(username: str, password: str):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        return {"message": f"User '{username}' created successfully"}
    except Exception:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()


# ──────────────────────────────────────────────
# Notes CRUD -- all protected by API key
# ──────────────────────────────────────────────

@app.post("/notes")
def create_note(user_id: int, title: str, content: str,
                api_key: str = Header(alias="X-Api-Key")):
    """
    We added 'api_key' as a parameter with Header(alias="X-Api-Key").
    But we are duplicating the check. Let us do it properly with
    FastAPI's Depends() in the next step.
    """
    verify_api_key(api_key)
    conn = get_db()
    conn.execute(
        "INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)",
        (user_id, title, content)
    )
    conn.commit()
    conn.close()
    return {"message": "Note created"}


@app.get("/notes")
def get_notes(user_id: int, api_key: str = Header(alias="X-Api-Key")):
    verify_api_key(api_key)
    conn = get_db()
    notes = conn.execute(
        "SELECT * FROM notes WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(note) for note in notes]


@app.delete("/notes/{note_id}")
def delete_note(note_id: int, api_key: str = Header(alias="X-Api-Key")):
    verify_api_key(api_key)
    conn = get_db()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    return {"message": "Note deleted"}
```

This works, but we are repeating ourselves. Every endpoint manually accepts the header and calls `verify_api_key`. FastAPI has a better pattern for this: **dependency injection** with `Depends()`.

### Cleaning It Up with Depends()

```python
# app_api_key_clean.py -- The clean version using Depends()

from fastapi import FastAPI, HTTPException, Depends, Header
from database import get_db, init_db

app = FastAPI()
init_db()

API_KEY = "codeverra-secret-key-2025"


def verify_api_key(x_api_key: str = Header()):
    """
    This function will be called automatically before every endpoint
    that lists it as a dependency. If it raises an exception, the
    endpoint never executes.
    """
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    # We do not return anything because API keys do not identify a user.
    # We just confirm the key is valid and let the request through.


@app.post("/register")
def register(username: str, password: str):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, password)
        )
        conn.commit()
        return {"message": f"User '{username}' created successfully"}
    except Exception:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()


# Notice: Depends(verify_api_key) is all we need. FastAPI calls
# verify_api_key before the endpoint runs. If the key is invalid,
# the endpoint never executes.

@app.post("/notes")
def create_note(user_id: int, title: str, content: str,
                _=Depends(verify_api_key)):
    conn = get_db()
    conn.execute(
        "INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)",
        (user_id, title, content)
    )
    conn.commit()
    conn.close()
    return {"message": "Note created"}


@app.get("/notes")
def get_notes(user_id: int, _=Depends(verify_api_key)):
    conn = get_db()
    notes = conn.execute(
        "SELECT * FROM notes WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(note) for note in notes]


@app.delete("/notes/{note_id}")
def delete_note(note_id: int, _=Depends(verify_api_key)):
    conn = get_db()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    return {"message": "Note deleted"}
```

The `_=Depends(verify_api_key)` pattern is important. The underscore `_` means "I do not care about the return value." We are using `Depends` purely for its side effect: it runs `verify_api_key` before the endpoint, and if the key is wrong, it raises an exception that stops the request.

### Testing It

Run the app: `uvicorn app_api_key_clean:app --reload`

Without the API key:
```bash
curl http://localhost:8000/notes?user_id=1
# Response: 422 -- missing X-Api-Key header
```

With a wrong key:
```bash
curl -H "X-Api-Key: wrong-key" http://localhost:8000/notes?user_id=1
# Response: 401 -- Invalid API key
```

With the correct key:
```bash
curl -H "X-Api-Key: codeverra-secret-key-2025" "http://localhost:8000/notes?user_id=1"
# Response: 200 -- returns the notes
```

It works. Requests without the correct key are rejected.

### What API Keys Cannot Do

But look at the endpoints again. We still have `user_id` as a parameter. Anyone with the API key can pass any user_id. If I have the key, I can read your notes by passing your user_id.

This is the fundamental limitation of API keys: **they identify the application (or the client), not the user.** The API key says "this request comes from a client that has been given access." It does not say "this request comes from Rahul" or "this request comes from Priya."

Everyone who has the key has the same access. There is no way to say "Rahul can read notes but Priya can read and delete." There is no concept of individual users.

This is fine for some use cases. When you use the Google Maps API key in your app, Google does not care which of your users is requesting the map. The key identifies your application for billing and rate limiting. But for our notes app, where each user should only see their own notes, API keys are not enough.

We need a way to identify the individual user making the request. That leads us to the next method.

---

## Method 2: HTTP Basic Authentication

### The Idea

What if, instead of a shared API key, each request carried the user's own username and password? Then the server would know exactly who is making the request and could enforce per-user access.

This is exactly what HTTP Basic Authentication does. It is built into the HTTP protocol itself. The client sends the username and password in the `Authorization` header with every request.

### How It Works Under the Hood

When a client sends a Basic Auth request, here is what the raw HTTP looks like:

```
GET /notes HTTP/1.1
Host: localhost:8000
Authorization: Basic cmFodWw6bXlwYXNzd29yZA==
```

That strange string `cmFodWw6bXlwYXNzd29yZA==` is the username and password encoded in Base64. Let us decode it:

```python
import base64
decoded = base64.b64decode("cmFodWw6bXlwYXNzd29yZA==")
print(decoded)
# Output: b'rahul:mypassword'
```

The format is `username:password`, combined with a colon, and Base64-encoded.

**Critical point: Base64 is NOT encryption.** Base64 is an encoding, like translating English to Hindi. Anyone who sees the encoded string can decode it instantly. There is no secret, no key, no security in the encoding itself. The security of Basic Auth depends entirely on HTTPS encrypting the connection so that nobody can see the Authorization header in transit.

### The Implementation

Let us rebuild our notes app with HTTP Basic Auth. Two big changes from the API key version:

1. We now know WHO the user is, so we can remove the `user_id` parameter from endpoints.
2. We need to actually verify the username and password against the database.

But first, we need to talk about password storage.

### Never Store Passwords in Plain Text

In our Version 0, we stored passwords directly in the database. If someone got access to the database file (through a hack, a backup leak, or a disgruntled employee), they would have every user's password in plain text. And since people reuse passwords, your breach becomes a breach of their email, their bank, their everything.

The solution is **hashing**. A hash function takes any input and produces a fixed-length string that looks like random gibberish. Crucially, you cannot reverse the process: given the hash, you cannot figure out the original password.

```
"mypassword"  -->  hash function  -->  "$2b$12$LJ3m4ys..."
```

When a user registers, we hash their password and store the hash. When they log in, we hash the password they sent and compare it to the stored hash. If they match, the password is correct. At no point do we ever store or see the actual password.

We will use the `bcrypt` library, which is the industry standard for password hashing.

```bash
pip install bcrypt
```

```python
import bcrypt

# When the user registers -- hash the password before storing
password = "mypassword"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
# hashed is something like: b'$2b$12$LJ3m4ys...'
# Store this in the database, not the original password.

# When the user logs in -- check if the password matches the hash
password_attempt = "mypassword"
if bcrypt.checkpw(password_attempt.encode(), hashed):
    print("Password is correct")
else:
    print("Wrong password")
```

`bcrypt.gensalt()` generates a random salt (a random string mixed into the hash). This means even two users with the same password get different hashes. This prevents attackers from using precomputed hash tables (called "rainbow tables") to crack passwords.

### The Full Implementation

```python
# app_basic_auth.py -- Notes app with HTTP Basic Authentication

import bcrypt
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from database import get_db, init_db

app = FastAPI()
init_db()

# FastAPI's HTTPBasic security scheme.
# This tells FastAPI: "endpoints that depend on this will require
# a username and password via the Authorization: Basic header."
# It also adds a login prompt in the Swagger UI.
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


# ──────────────────────────────────────────────
# Registration -- now with password hashing
# ──────────────────────────────────────────────

@app.post("/register")
def register(username: str, password: str):
    # Hash the password before storing it
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed)  # Store the HASH, not the password
        )
        conn.commit()
        return {"message": f"User '{username}' created successfully"}
    except Exception:
        raise HTTPException(status_code=400, detail="Username already exists")
    finally:
        conn.close()


# ──────────────────────────────────────────────
# Notes CRUD -- now we know WHO the user is
# ──────────────────────────────────────────────

@app.post("/notes")
def create_note(title: str, content: str,
                user: dict = Depends(get_current_user)):
    """
    Look at what changed: there is no more 'user_id' parameter.
    The user is identified by their credentials. We get the user
    from get_current_user, and we use user["id"] to link the note
    to the correct owner.

    Nobody can create notes under someone else's account because
    they would need that person's password.
    """
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
```

### What Changed (And Why It Matters)

Compare this to the API key version:

1. **No more `user_id` parameter.** The identity comes from the credentials, not from a parameter the client can fake.
2. **Each user sees only their own notes.** The SQL query filters by `user["id"]`, which comes from the authenticated credentials.
3. **Users can only delete their own notes.** The DELETE query checks `AND user_id = ?`.
4. **Passwords are hashed.** Even if the database is stolen, the passwords are safe.

This is a massive improvement over API keys. We solved the "who is making this request" problem.

### The Problem With Basic Auth

But there is a problem hiding in plain sight: **the client sends the password with every single request.**

Every time you fetch your notes, you send your password. Every time you create a note, you send your password. Every time you delete a note, you send your password.

If you make 50 API calls in a session, your password travels across the network 50 times. Yes, HTTPS encrypts it in transit. But the password is still being transmitted repeatedly. The more times it is transmitted, the more opportunities there are for something to go wrong. A misconfigured proxy that logs headers. A debugging tool that captures requests. A man-in-the-middle attack on a compromised network.

Worse, there is no concept of a "session" or "logout." The password is the session. The only way to "log out" is to stop sending the password. The only way to "expire" a session is to change the password itself.

What we need is a system where the user sends their password once, and then uses something else, something temporary and revocable, for subsequent requests.

That leads us to sessions.

---

## Method 3: Session-Based Authentication (Cookies)

### The Idea

Here is the concept: instead of sending your password with every request, you send it once. The server verifies it, creates a "session" (a record that says "this user is logged in"), and gives you back a **session ID**: a random string that represents your active session.

For every subsequent request, you send the session ID instead of your password. The server looks up the session ID, finds the associated user, and processes the request.

When you want to log out, you tell the server, and it destroys the session. The session ID becomes meaningless.

This is how traditional websites have worked for decades. Every time you log into a website and it "remembers" you as you click from page to page, that is session-based authentication.

### How Sessions Work: Step by Step

**Step 1: Login.** The client sends username and password to a `/login` endpoint. The server verifies them.

**Step 2: Session creation.** The server generates a random session ID (like `a7f3b2c1d9e8...`), stores it in a dictionary (or database or Redis) along with the user's information, and sends the session ID back to the client in a `Set-Cookie` header.

**Step 3: Subsequent requests.** The client's browser automatically includes the cookie in every request to the same server. The server reads the cookie, looks up the session, and identifies the user.

**Step 4: Logout.** The client calls `/logout`. The server deletes the session from its storage. The cookie becomes an orphan: it still exists on the client, but the server no longer recognizes it.

### The Implementation

```python
# app_session.py -- Notes app with session-based authentication

import uuid
import bcrypt
from fastapi import FastAPI, HTTPException, Depends, Response, Cookie
from database import get_db, init_db

app = FastAPI()
init_db()

# This dictionary stores all active sessions.
# Key: session_id (a random string)
# Value: user data (a dictionary with id, username, etc.)
#
# In a real application, you would use Redis or a database table
# for session storage. An in-memory dictionary works for learning
# but is lost when the server restarts.
sessions = {}


def get_current_user(session_id: str = Cookie(default=None)):
    """
    Read the session_id cookie from the request.
    Look it up in our sessions dictionary.
    If found, return the user. If not, reject the request.

    Cookie(default=None) means: if the cookie is missing, set it
    to None instead of raising a 422 error. We handle the "missing
    cookie" case ourselves with a clear error message.
    """
    if session_id is None:
        raise HTTPException(
            status_code=401,
            detail="Not logged in. No session cookie found."
        )

    user = sessions.get(session_id)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Session expired or invalid. Please log in again."
        )

    return user


# ──────────────────────────────────────────────
# Registration -- same as before
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# Login and Logout -- these are new
# ──────────────────────────────────────────────

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
    session_id = str(uuid.uuid4())

    # Store the session in our dictionary.
    # We store the user's id and username -- everything we need
    # to process future requests without touching the database.
    sessions[session_id] = {"id": user["id"], "username": user["username"]}

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
    return {"message": "Logged out"}


# ──────────────────────────────────────────────
# Notes CRUD -- identical logic, different auth
# ──────────────────────────────────────────────

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
```

### The Flow

1. User registers: `POST /register?username=rahul&password=secret123`
2. User logs in: `POST /login?username=rahul&password=secret123`
   - Server creates session `a7f3b2c1...`, stores it, sends cookie
3. User creates a note: `POST /notes?title=My+Note&content=Hello`
   - Browser automatically sends the `session_id` cookie
   - Server looks up `a7f3b2c1...` in the sessions dict, finds Rahul
   - Creates the note under Rahul's user_id
4. User logs out: `POST /logout`
   - Server deletes `a7f3b2c1...` from the sessions dict
5. User tries to create another note:
   - Browser still has the cookie, but the session no longer exists on the server
   - Server returns 401: "Session expired or invalid"

The password was sent exactly once, at login. Everything after that used the session cookie.

### The Problem With Sessions

Sessions work well for traditional web applications. But they have a fundamental issue: **the server must store every active session.**

If you have 10 lakh active users, you have 10 lakh session records. That is manageable. But now imagine you have multiple servers behind a load balancer (which any serious application does). A user logs in and their session is stored on Server A. Their next request might go to Server B. Server B has no idea about that session. The request fails.

There are solutions: you can use a shared session store (Redis), or you can use "sticky sessions" (the load balancer always sends the same user to the same server). But these add infrastructure complexity. Redis becomes a single point of failure. Sticky sessions make scaling harder.

There is also the mobile app problem. Cookies are a browser feature. Mobile apps can handle them, but it is not their natural pattern. Mobile developers prefer sending tokens in headers.

What if the token itself contained all the information the server needs? What if the server did not have to store anything? What if the token was self-contained, carrying the user's identity inside it, signed so it cannot be tampered with?

That is JWT.

---

## Method 4: JWT Authentication (JSON Web Tokens)

### The Idea

JWT (pronounced "jot") is a token format that contains information about the user, encoded and signed into a compact string. The server creates the token when the user logs in, hands it to the client, and the client sends it with every subsequent request.

The critical difference from sessions: **the server does not store the token.** The token itself contains everything the server needs to identify the user. The server just verifies that the token is valid (not tampered with, not expired) and reads the user's information directly from it.

### The Analogy

Think about a government-issued ID card, like your Aadhaar card.

The government (the server) issued it. Your name, photo, and details are printed on it. It has an expiry date. It has a tamper-proof hologram (the signature). When you show it at a bank or a hotel, they do not call the government to verify it. They check the hologram, check the expiry date, and read your details directly from the card.

A JWT works the same way. The server "issues" the token. The user's information is encoded inside it. It has an expiry time. It has a cryptographic signature (the digital hologram). When the client sends it back, the server verifies the signature, checks the expiry, and reads the user's identity from the token itself.

### What Does a JWT Look Like?

A JWT is a string with three parts separated by dots:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6InJhaHVsIiwiZXhwIjoxNzEyNTAwMDAwfQ.3Kk8M7x5_rWHd8G7nPqxJ2sL4ZxV6bN9mQ1Yw8hK0-E
```

It looks like random gibberish, but it has a clear structure.

**Part 1: The Header** (everything before the first dot)
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
```
This is Base64-encoded JSON. Decoded, it says:
```json
{"alg": "HS256", "typ": "JWT"}
```
It tells us: this is a JWT, and the signature algorithm is HS256 (HMAC with SHA-256).

**Part 2: The Payload** (between the two dots)
```
eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6InJhaHVsIiwiZXhwIjoxNzEyNTAwMDAwfQ
```
Decoded:
```json
{"user_id": 1, "username": "rahul", "exp": 1712500000}
```
This is the actual data. It contains the user's ID, username, and expiry timestamp. These fields are called **claims**. You can put anything here, but remember: this is encoded, not encrypted. Anyone who has the token can decode and read the payload. Never put passwords or sensitive data in a JWT.

**Part 3: The Signature** (after the second dot)
```
3Kk8M7x5_rWHd8G7nPqxJ2sL4ZxV6bN9mQ1Yw8hK0-E
```
This is the cryptographic signature. The server creates it by taking the header + payload and signing them with a secret key that only the server knows. If anyone modifies the header or payload, the signature will not match, and the server will reject the token.

Think of it like a wax seal on a letter. You can read the letter (the payload is not encrypted), but you cannot change the contents without breaking the seal.

### Encoding vs Encryption vs Signing

These three concepts are often confused. Let us make them crystal clear because JWT uses all of them differently.

**Encoding** (Base64) is like translating Hindi to English. Anyone can do it, anyone can reverse it. There is no secret involved. JWT's header and payload are Base64-encoded. This is just a way to represent JSON as a URL-safe string. It is NOT security.

**Encryption** is like putting a message in a locked box. Only someone with the key can read it. JWT does NOT encrypt the payload by default. Anyone who has the token can decode and read the payload. This is why you should never put secrets in a JWT.

**Signing** is like stamping a wax seal on a letter. The letter is readable by anyone (no encryption), but the seal proves it came from you and was not tampered with. JWT signs the header and payload using a secret key. If anyone modifies the payload (like changing `"user_id": 1` to `"user_id": 2`), the signature becomes invalid.

A JWT is **signed but not encrypted**. The payload is readable. The payload is tamper-proof. These are different things.

### The Implementation

We need the `PyJWT` library for creating and verifying tokens:

```bash
pip install pyjwt bcrypt
```

```python
# app_jwt.py -- Notes app with JWT authentication

import jwt
import bcrypt
import time
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from database import get_db, init_db

app = FastAPI()
init_db()

# The secret key used to sign tokens.
# In production, this comes from an environment variable, never hardcoded.
# If this key is leaked, anyone can forge valid tokens.
SECRET_KEY = "codeverra-jwt-secret-key-change-this-in-production"

# The algorithm used for signing.
ALGORITHM = "HS256"

# Tokens expire after 30 minutes (1800 seconds).
ACCESS_TOKEN_EXPIRE_SECONDS = 1800


# OAuth2PasswordBearer tells FastAPI:
# "Clients will send a token in the Authorization header as 'Bearer <token>'"
# The tokenUrl is the endpoint where clients can obtain a token (our /login).
# This also adds an "Authorize" button in Swagger UI.
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


# ──────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# Login -- returns a JWT token
# ──────────────────────────────────────────────

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


# ──────────────────────────────────────────────
# Notes CRUD -- protected by JWT
# ──────────────────────────────────────────────

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
```

### Testing the JWT Flow

```bash
# Step 1: Register a user
curl -X POST "http://localhost:8000/register?username=rahul&password=secret123"
# {"message": "User 'rahul' created successfully"}

# Step 2: Login and get a token
curl -X POST "http://localhost:8000/login?username=rahul&password=secret123"
# {"access_token": "eyJhbGciOiJIUzI1NiIs...", "token_type": "bearer"}

# Step 3: Use the token to create a note
curl -X POST "http://localhost:8000/notes?title=My+Note&content=Hello+World" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
# {"message": "Note created"}

# Step 4: Get your notes
curl "http://localhost:8000/notes" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
# [{"id": 1, "user_id": 1, "title": "My Note", "content": "Hello World"}]
```

### Why JWT Is Stateless (And Why That Matters)

Look at the server code. There is no `sessions` dictionary. No database table for sessions. No Redis. When a request comes in, the server:

1. Reads the token from the header
2. Verifies the signature using the secret key (a simple mathematical operation)
3. Reads the user's identity from the payload

No database query. No session lookup. No shared state.

This means you can run 10 copies of this server behind a load balancer, and any server can handle any request. The token contains everything. There is nothing to synchronize between servers.

This is why JWT is the dominant authentication method for modern APIs. It scales effortlessly.

### Adding Role-Based Access Control

JWT tokens can carry any information in their payload. We can use this for role-based access: some users are admins, some are regular users.

```python
# Adding roles to our JWT system

def create_token(user_id: int, username: str, role: str = "user") -> str:
    """Now we include the user's role in the token."""
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,  # "user" or "admin"
        "exp": int(time.time()) + ACCESS_TOKEN_EXPIRE_SECONDS
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def require_admin(user: dict = Depends(get_current_user)):
    """
    A dependency that requires the user to be an admin.
    Use this on admin-only endpoints.
    """
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return user


# An admin-only endpoint
@app.get("/admin/all-notes")
def get_all_notes(admin: dict = Depends(require_admin)):
    """Only admins can see all notes from all users."""
    conn = get_db()
    notes = conn.execute("SELECT * FROM notes").fetchall()
    conn.close()
    return [dict(note) for note in notes]
```

Notice the status code difference: 401 means "you are not logged in" (no valid token). 403 means "you are logged in, but you are not allowed to do this" (you are a regular user trying to access an admin endpoint). This is the 401 vs 403 distinction in practice.

### Access Tokens and Refresh Tokens

Our current tokens expire in 30 minutes. When they expire, the user must log in again with their password. This is a bad user experience.

The solution is the **refresh token** pattern. It uses two tokens:

**Access token:** Short-lived (15-30 minutes). Used for every API request. If stolen, the damage is limited because it expires quickly.

**Refresh token:** Long-lived (7-30 days). Used only to get a new access token. Stored more securely. If the access token expires, the client sends the refresh token to get a fresh access token without re-entering the password.

```python
# Refresh token implementation
# Add these to your existing app_jwt.py file

# Refresh tokens live much longer than access tokens.
# 7 days = the user stays "logged in" for a week without
# re-entering their password, even though their access token
# rotates every 30 minutes.
REFRESH_TOKEN_EXPIRE_SECONDS = 7 * 24 * 3600  # 7 days


def create_refresh_token(user_id: int) -> str:
    """
    Create a long-lived refresh token.

    Notice what is different from the access token:
    - It has a "type" field set to "refresh" so we can tell
      the two apart. Without this, someone could use a refresh
      token as an access token (skipping the 30-minute expiry).
    - It only contains the user_id, not the username. Why?
      Because the username might change during the 7-day lifetime
      of this token. When we issue a new access token from a
      refresh, we will fetch the CURRENT username from the database.
    - It has a much longer expiry (7 days vs 30 minutes).
    """
    payload = {
        "user_id": user_id,
        "type": "refresh",
        "exp": int(time.time()) + REFRESH_TOKEN_EXPIRE_SECONDS
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@app.post("/login")
def login(username: str, password: str):
    """
    Updated login: now returns BOTH an access token and a refresh token.

    The client stores both. It uses the access token for API calls
    (in the Authorization header). It keeps the refresh token somewhere
    safe and only uses it when the access token expires.
    """
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not bcrypt.checkpw(password.encode(), user["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Issue both tokens. The access token is for immediate use.
    # The refresh token is for getting new access tokens later.
    return {
        "access_token": create_token(user["id"], user["username"]),
        "refresh_token": create_refresh_token(user["id"]),
        "token_type": "bearer"
    }


@app.post("/refresh")
def refresh(refresh_token: str):
    """
    Exchange a valid refresh token for a new access token.
    The user does not need to send their password again.

    This endpoint is called when the client gets a 401 "Token expired"
    error on a regular API call. Instead of showing a login screen,
    the client calls this endpoint with the refresh token to silently
    get a new access token.
    """

    # Step 1: Decode and verify the refresh token.
    # jwt.decode checks the signature AND the expiry automatically.
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        # The refresh token itself has expired (after 7 days).
        # The user must log in with their password again.
        # There is no way around this -- it is the security boundary.
        raise HTTPException(
            status_code=401,
            detail="Refresh token expired. Please log in again."
        )
    except jwt.InvalidTokenError:
        # The token is malformed, has a bad signature, etc.
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Step 2: Verify this is actually a refresh token.
    # Without this check, someone could take an expired access token
    # and use it here (since access tokens do not have type="refresh").
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    # Step 3: Look up the user in the database.
    # We do this (instead of just copying data from the token) because:
    #   - The user's username might have changed
    #   - The user might have been deleted or banned
    #   - We want the CURRENT state, not the state when the token was issued
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?", (payload["user_id"],)
    ).fetchone()
    conn.close()

    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")

    # Step 4: Issue a fresh access token with the user's current data.
    # This new token is valid for another 30 minutes.
    new_access_token = create_token(user["id"], user["username"])
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
```

The flow becomes:

1. Login: get access token (30 min) + refresh token (7 days)
2. Use access token for all API calls
3. Access token expires after 30 minutes
4. Send refresh token to `/refresh`, get a new access token
5. Continue making API calls with the new access token
6. Repeat steps 3-5 until the refresh token expires (7 days)
7. When the refresh token expires, the user must log in with their password again

This is how most production applications work. The user logs in once and stays "logged in" for days or weeks, but the actual access tokens rotate every 30 minutes for security.

### Common JWT Mistakes

**Mistake 1: Storing sensitive data in the payload.**
The JWT payload is encoded, not encrypted. Anyone with the token can decode it and read the contents. Never put passwords, credit card numbers, or any secrets in a JWT. Put only what is needed to identify the user: their ID, username, and role.

**Mistake 2: Not setting an expiry time.**
A token without an `exp` claim is valid forever. If it is stolen, the attacker has permanent access. Always set a reasonable expiry.

**Mistake 3: Using a weak secret key.**
The secret key is what makes the signature unforgeable. If your key is something like `"secret"` or `"password123"`, an attacker can guess it and forge valid tokens. Use a long, random string. In production, generate it with `openssl rand -hex 32`.

**Mistake 4: Not validating the token type.**
If you have both access tokens and refresh tokens, always check the `type` claim. Otherwise, someone could use a refresh token as an access token (or vice versa), bypassing your expiry logic.

---

## Method 5: OAuth2 (Delegated Authentication)

### The Idea

Every method we have seen so far requires the user to create a username and password on your application. Your application stores the password (hashed), verifies it at login, and issues credentials.

But what if you did not want to handle passwords at all? What if you could say "I trust Google to verify this user's identity, and I will accept whatever Google tells me"?

That is OAuth2. The user does not create a password on your app. Instead, they click "Sign in with Google" (or GitHub, or Facebook). Google handles the authentication and tells your app who the user is.

### Why OAuth2 Exists

Handling passwords is a liability. You have to hash them correctly, store them securely, handle password resets, deal with breaches, and comply with data protection laws. Every password you store is a responsibility.

OAuth2 lets you delegate this responsibility to companies that specialize in it. Google, GitHub, and Apple have teams of security engineers whose full-time job is protecting user credentials. You probably do not.

From the user's perspective, OAuth2 is also better. They do not need yet another username and password. They already have a Google account. One click and they are in.

### The OAuth2 Flow (Authorization Code Flow)

This is the most common OAuth2 flow, used by "Sign in with Google" buttons everywhere. Let us walk through it step by step.

**Step 1: The redirect.** The user clicks "Sign in with Google" on your app. Your app redirects them to Google's login page, with some parameters: your app's client ID, what permissions you are requesting (like access to the user's email), and where Google should send the user after they log in.

```
https://accounts.google.com/o/oauth2/v2/auth?
  client_id=YOUR_APP_ID
  &redirect_uri=http://localhost:8000/callback
  &response_type=code
  &scope=email profile
```

**Step 2: The user logs into Google.** This happens entirely on Google's website. Your app never sees the user's Google password.

**Step 3: Google redirects back to your app.** After the user logs in, Google redirects them back to your app at the `redirect_uri` you specified, with an authorization code:

```
http://localhost:8000/callback?code=4/P7q7W91a-oMsCeLvIaQm6bTrgtp7
```

This code is a one-time-use proof that the user authenticated with Google.

**Step 4: Your app exchanges the code for a token.** Your backend sends this code to Google's token endpoint, along with your app's client secret (a secret key that Google gave you when you registered your app). Google verifies everything and sends back an access token.

```python
# Your backend makes this request to Google (simplified)
response = requests.post("https://oauth2.googleapis.com/token", data={
    "code": "4/P7q7W91a-oMsCeLvIaQm6bTrgtp7",
    "client_id": "YOUR_APP_ID",
    "client_secret": "YOUR_APP_SECRET",
    "redirect_uri": "http://localhost:8000/callback",
    "grant_type": "authorization_code"
})
google_token = response.json()["access_token"]
```

**Step 5: Your app uses the token to get user info.** You call Google's user info API with the access token:

```python
user_info = requests.get(
    "https://www.googleapis.com/oauth2/v2/userinfo",
    headers={"Authorization": f"Bearer {google_token}"}
)
# Returns: {"email": "rahul@gmail.com", "name": "Rahul Sharma", ...}
```

Now you know who the user is. You can create a local user record (if this is their first visit), generate your own JWT, and proceed as usual.

**Step 6: Issue your own JWT.** Even with OAuth2, you typically issue your own JWT for subsequent API calls. Google's token proved the user's identity at login. Your JWT authorizes them in your system.

### Why We Are Not Implementing This Fully

A complete OAuth2 implementation requires registering your app with Google (getting a client_id and client_secret), setting up redirect URIs, and handling the redirect flow. These steps involve configuration outside of code, and they do not teach authentication concepts that you do not already understand from the JWT section.

The important takeaway is the pattern: **you delegate the "who are you" question to a trusted provider, receive proof that the user is who they claim to be, and then issue your own credentials (JWT) for your API.**

### When to Use OAuth2

OAuth2 is the right choice when your app is consumer-facing (users should not need to create yet another account), when you do not want to handle password storage, when you need to access user data from the provider (like their Google Calendar or GitHub repos), or when you want to offer social login as a convenience.

It is overkill for internal tools, service-to-service APIs, or applications where users expect to create a dedicated account.

### Practical Steps: What You Would Need to Implement OAuth2

We are not building a full OAuth2 flow in this guide because it requires registering with an external provider and setting up redirect URLs -- things that go beyond code. But here is exactly what you would do, step by step, if you wanted to add "Sign in with GitHub" to a FastAPI app. This gives you a concrete roadmap for when you are ready.

**Step 1: Register your app with GitHub.**

Go to GitHub Settings -> Developer Settings -> OAuth Apps -> New OAuth App. You will fill in your app name, homepage URL (`http://localhost:8000`), and the callback URL (`http://localhost:8000/auth/callback`). GitHub gives you a `client_id` and a `client_secret`. Save both. The client_secret is like your JWT secret key -- never expose it publicly.

**Step 2: Install an HTTP client library.**

You need `httpx` (or `requests`) to make server-to-server calls to GitHub's API.

```bash
pip install httpx
```

**Step 3: Create the login redirect endpoint.**

```python
# When the user clicks "Sign in with GitHub", redirect them
# to GitHub's authorization page.

GITHUB_CLIENT_ID = "your_client_id_here"
GITHUB_CLIENT_SECRET = "your_client_secret_here"

@app.get("/auth/github")
def github_login():
    """
    Redirect the user to GitHub's login page.
    GitHub handles the username/password verification.
    We never see or touch the user's GitHub password.
    """
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri=http://localhost:8000/auth/callback"
        f"&scope=user:email"  # We only need their email
    )
    # In a real app, you would return a RedirectResponse here.
    # For an API, you return the URL for the frontend to redirect to.
    return {"auth_url": github_auth_url}
```

**Step 4: Handle the callback.**

```python
import httpx

@app.get("/auth/callback")
async def github_callback(code: str):
    """
    GitHub redirects the user back here with a temporary 'code'.
    We exchange this code for an access token, then use that
    token to fetch the user's profile from GitHub.
    """
    # Exchange the code for a GitHub access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        github_token = token_response.json()["access_token"]

        # Use the token to get the user's GitHub profile
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {github_token}"},
        )
        github_user = user_response.json()
        # github_user contains: login, email, name, avatar_url, etc.

    # Now you have the user's identity from GitHub.
    # From here, the flow is the same as regular JWT:
    # 1. Check if this GitHub user exists in YOUR database
    # 2. If not, create a new user record (using their GitHub username/email)
    # 3. Issue YOUR OWN JWT tokens (access + refresh)
    # 4. Return the tokens to the client

    # This is where OAuth2 meets JWT -- you use OAuth2 for the
    # initial "who are you?" and JWT for everything after that.

    return {
        "github_username": github_user["login"],
        "message": "You would issue a JWT here and redirect the user"
    }
```

**Step 5: Connect it to your existing JWT system.**

The callback endpoint would look up or create the user in your database, then call the same `create_token()` and `create_refresh_token()` functions we built in the JWT section. From the client's perspective, after the initial GitHub login, everything works exactly like password-based JWT auth -- they have an access token and a refresh token, and they use them the same way.

The key insight: OAuth2 replaces the `/login` endpoint (how the user proves who they are), but everything after that (token issuance, protected endpoints, refresh flow) stays exactly the same.

We will do a full OAuth2 implementation as a separate deep dive later in the course, where we will also cover Google OAuth, handling multiple providers, and linking OAuth accounts to existing password-based accounts.

---

## Choosing the Right Authentication Method

You now understand five authentication methods, each with different strengths. Here is how to choose.

### The Decision Framework

**Use API Keys when:**
- Your API is consumed by other programs, not humans
- You need to identify the application (for billing, rate limiting), not the individual user
- Examples: third-party integrations, public APIs, developer platforms

**Use HTTP Basic Auth when:**
- You need a quick, simple way to protect an internal tool
- The client is a script or server (not a browser)
- HTTPS is guaranteed
- Examples: internal admin endpoints, CI/CD webhooks, quick prototypes

**Use Session-based auth when:**
- You are building a traditional server-rendered web application
- The client is always a browser
- You need the ability to invalidate sessions immediately (ban a user, force logout)
- Examples: admin dashboards, content management systems, traditional web apps

**Use JWT when:**
- You are building a modern API consumed by mobile apps, SPAs, or other services
- You need stateless authentication that scales horizontally
- You want your API to work with diverse clients (web, mobile, third-party)
- Examples: most modern APIs, mobile app backends, microservices

**Use OAuth2 when:**
- Your app is consumer-facing and you want "Sign in with Google/GitHub/Apple"
- You do not want to handle password storage
- You need access to user data from the provider
- Examples: SaaS products, consumer apps, developer tools

### Quick Reference Table

| Method | Identifies | Stateless | Scalability | Best For |
|--------|-----------|-----------|-------------|----------|
| API Key | Application | Yes | Excellent | Machine-to-machine APIs |
| Basic Auth | User | Yes | Good | Internal tools, scripts |
| Sessions | User | No (server stores state) | Needs shared store | Traditional web apps |
| JWT | User | Yes | Excellent | Modern APIs, mobile backends |
| OAuth2 | User (via provider) | Depends | Excellent | Consumer-facing apps |

For this course, we will use JWT. It is the standard for modern APIs, it is stateless, it scales well, and FastAPI has excellent support for it.

---

## Frequently Asked Questions and Common Doubts

### JWT Questions

**Q: Can I "log out" a user with JWT?**

This is one of the most common questions about JWT, and the honest answer is: not as cleanly as with sessions.

With sessions, logout is simple: delete the session from the server's storage. Done.

With JWT, the server does not store anything. The token is valid until it expires. You cannot "un-sign" a token. There are workarounds:

1. **Short expiry times.** If your access token expires in 15 minutes, a "logged out" token is only usable for at most 15 more minutes. This is usually acceptable.
2. **Token blacklist.** Store a list of revoked tokens (in Redis or a database) and check every request against it. This works but adds state, partially defeating the purpose of JWT.
3. **Refresh token revocation.** When the user logs out, revoke their refresh token. The access token will expire naturally, and without a valid refresh token, they cannot get a new one.

In practice, most applications use option 1 + 3: short-lived access tokens and revocable refresh tokens.

**Q: Someone told me JWT is insecure. Is that true?**

JWT is not inherently insecure. It is a tool, and like any tool, it can be misused. Common mistakes that make JWT insecure:

- Using `alg: "none"` (disabling signature verification). Always validate the algorithm.
- Using a weak or guessable secret key. Use at least 256 bits of randomness.
- Storing tokens in localStorage (vulnerable to XSS attacks). Use httpOnly cookies for browser-based apps.
- Not setting expiry times. Tokens should always expire.
- Putting sensitive data in the payload. The payload is readable by anyone.

Used correctly, JWT is secure and battle-tested. Major companies (Google, Microsoft, Auth0) rely on it.

**Q: Where should the client store the JWT?**

For browser-based apps, the safest option is an **httpOnly cookie**. JavaScript cannot read httpOnly cookies, so even if your app has an XSS vulnerability, the attacker cannot steal the token.

For mobile apps, use the platform's secure storage: Keychain on iOS, Keystore on Android.

Storing tokens in localStorage or sessionStorage is convenient but vulnerable to XSS attacks. If you must use localStorage, ensure your app is protected against XSS.

**Q: What is the difference between HS256 and RS256?**

**HS256 (HMAC + SHA-256)** uses a single secret key for both signing and verification. The same key that creates the token also verifies it. This is simpler but means anyone who can verify tokens can also create them.

**RS256 (RSA + SHA-256)** uses a public/private key pair. The private key signs the token. The public key verifies it. This means the authentication server (which has the private key) can create tokens, but other services (which only have the public key) can verify tokens without being able to create them.

HS256 is fine for single-server setups. RS256 is better for microservices where multiple services need to verify tokens but only one should issue them.

For this course, HS256 is sufficient.

**Q: Should I build my own JWT auth or use a service like Auth0 or Firebase Auth?**

For learning, build it yourself. That is what this guide is for. Understanding the internals makes you a better developer.

For production, consider managed services if: your team is small, authentication is not your core product, and you need features like social login, multi-factor authentication, password reset flows, and compliance certifications. Auth0, Firebase Auth, Clerk, and Supabase Auth handle all of this for you.

For production where you need full control, build it yourself using the patterns in this guide, but add: rate limiting on login endpoints, password complexity requirements, email verification, account lockout after failed attempts, and HTTPS enforcement.

### Session vs JWT Questions

**Q: If JWT is stateless and scalable, why does anyone still use sessions?**

Sessions have one advantage JWT cannot match: **instant revocation.** If you delete a session from Redis, the user is logged out immediately. With JWT, the token is valid until it expires (unless you maintain a blacklist, which adds state).

For applications where you need to instantly ban a user, force logout all devices, or comply with strict security requirements (banking, healthcare), sessions with Redis are often preferred.

The real-world answer is: many production systems use a hybrid. JWT for the primary authentication flow, with a lightweight server-side check (against a blacklist or a user status flag) for critical operations.

**Q: Can I use sessions with a mobile app?**

Technically yes. Mobile apps can store and send cookies. But it is not the natural pattern. Mobile developers expect to send tokens in the Authorization header, not manage cookies. JWT with header-based tokens is the standard for mobile APIs.

### Password Questions

**Q: Why bcrypt specifically? What about SHA-256 or MD5?**

SHA-256 and MD5 are general-purpose hash functions designed to be fast. That speed is a problem for passwords: an attacker can try billions of SHA-256 hashes per second with modern hardware.

bcrypt is designed to be slow. It has a configurable "work factor" that controls how many rounds of computation are performed. On current hardware, bcrypt with the default work factor takes about 100 milliseconds per hash. That is fine for a single login attempt, but it means an attacker can only try about 10 passwords per second instead of billions.

Other good options: Argon2 (the newest, winner of the Password Hashing Competition) and scrypt. All three are designed to be slow and memory-intensive, making brute-force attacks impractical.

Never use MD5 or plain SHA-256 for passwords.

**Q: If someone steals my SECRET_KEY, what happens?**

If your JWT secret key is compromised, the attacker can forge valid tokens for any user. They can give themselves admin access. They can impersonate anyone. This is a critical breach.

Immediate response: rotate the secret key. This invalidates ALL existing tokens, logging out every user. They will need to log in again. This is disruptive but necessary.

Prevention: never hardcode the key in your source code (use environment variables), never commit it to version control, rotate it periodically, and limit access to the production environment.

### General Questions

**Q: What is the difference between authentication and authorization?**

**Authentication** answers "who are you?" It is the process of verifying identity. Logging in with a username and password is authentication. Sending a JWT token that proves you are Rahul is authentication.

**Authorization** answers "what are you allowed to do?" It is the process of checking permissions. After authentication confirms you are Rahul, authorization checks: can Rahul delete this note? Can Rahul access the admin panel? Can Rahul view this other user's data?

In our examples, `get_current_user` handles authentication (verify the token, identify the user). The `AND user_id = ?` clause in our SQL queries handles authorization (ensure the user can only access their own notes). The `require_admin` dependency handles authorization (ensure only admins can access admin endpoints).

Both are essential. Authentication without authorization means everyone who logs in can do everything. Authorization without authentication means the server does not know who to check permissions for.

**Q: What is CORS and how does it relate to authentication?**

CORS (Cross-Origin Resource Sharing) is a browser security feature that restricts web pages from making requests to a different domain. If your frontend is on `http://localhost:3000` and your API is on `http://localhost:8000`, the browser will block the API requests unless the API explicitly allows it.

This is not directly about authentication, but it affects authentication flows. You need to configure CORS on your FastAPI server to allow your frontend's origin. We will cover this when we build the full application.

**Q: What is HTTPS and why does every auth method assume it?**

HTTPS encrypts the data traveling between client and server. Without it, anyone on the same network (a cafe Wi-Fi, a compromised router) can read your HTTP requests, including your passwords, tokens, and API keys.

Every authentication method in this guide assumes HTTPS is in place. Basic Auth sends passwords in every request (disastrous without HTTPS). JWT tokens sent in plain HTTP can be intercepted and reused. Even API keys in headers are visible without encryption.

During development on `localhost`, HTTPS is not necessary (nobody can intercept traffic between your computer and itself). In production, HTTPS is non-negotiable.

**Q: What about multi-factor authentication (MFA)?**

MFA adds a second layer beyond the password: something you have (a phone with an authenticator app), something you are (biometrics), or something you receive (an SMS code).

MFA is an addition to any authentication method, not a replacement. In our JWT flow, MFA would work like this: the user sends username and password, the server verifies them, then sends a code to their phone. The user sends the code. Only then does the server issue the JWT.

Implementing MFA is beyond the scope of this guide, but it follows the same patterns: verify an additional credential before issuing the token.

---

## Summary: The Full Journey

We started with an unprotected app where anyone could do anything. Then we walked through five authentication methods, each one solving a problem the previous one could not:

**API Keys** gave us a basic lock on the door. But they could not tell us who was behind the door.

**HTTP Basic Auth** told us who was making each request. But it sent the password with every single request.

**Session-based auth** fixed the repeated password problem by sending it once and using a session ID after that. But the server had to remember every session, making it hard to scale.

**JWT** made the token self-contained so the server did not need to remember anything. It is stateless, scalable, and the standard for modern APIs.

**OAuth2** let us delegate the entire "who are you" question to trusted providers like Google and GitHub.

Each method has its place. The right choice depends on what you are building, who your users are, and what trade-offs you are willing to make. For most modern APIs, JWT is the default, and that is what we will use throughout the rest of this course.

---

*This is a Codeverra course. Learn more at learn.codeverra.com*
