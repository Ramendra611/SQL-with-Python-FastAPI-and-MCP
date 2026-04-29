# Pydantic: A Complete Deep Dive

## From Basics to Advanced Features

---

**Course:** SQL with Python, FastAPI and MCP
**Platform:** Codeverra (learn.codeverra.com)
**Type:** Standalone reference document. Read alongside the course or independently.

---

## Table of Contents

- [What This Document Covers](#what-this-document-covers)
- [1. Why Pydantic Exists](#1-why-pydantic-exists)
- [2. Your First Pydantic Model](#2-your-first-pydantic-model)
- [3. Field Types and the Basics](#3-field-types-and-the-basics)
- [4. Optional Fields and Default Values](#4-optional-fields-and-default-values)
- [5. The Field Function: Complete Reference](#5-the-field-function-complete-reference)
- [6. Specialised Types](#6-specialised-types)
- [7. Nested Models](#7-nested-models)
- [8. Lists, Dicts, and Collections](#8-lists-dicts-and-collections)
- [9. Union Types and Optional](#9-union-types-and-optional)
- [10. Custom Validators](#10-custom-validators)
- [11. Model Validators](#11-model-validators)
- [12. Serialisation and Exporting Data](#12-serialisation-and-exporting-data)
- [13. Model Configuration](#13-model-configuration)
- [14. Aliases: Handling Different Naming Conventions](#14-aliases-handling-different-naming-conventions)
- [15. Strict vs Lax Mode](#15-strict-vs-lax-mode)
- [16. Computed Fields](#16-computed-fields)
- [17. Discriminated Unions](#17-discriminated-unions)
- [18. Generic Models](#18-generic-models)
- [19. Pydantic Settings: Configuration Management](#19-pydantic-settings-configuration-management)
- [20. JSON Schema Generation](#20-json-schema-generation)
- [21. Pydantic v1 vs v2](#21-pydantic-v1-vs-v2)
- [22. Common Patterns and Pitfalls](#22-common-patterns-and-pitfalls)
- [Exercises](#exercises)
- [Solutions](#solutions)

---

## What This Document Covers

Pydantic is a data validation library for Python. It is the foundation of FastAPI, the standard tool for managing application configuration, and one of the most downloaded Python packages. Despite its importance, many developers learn just enough Pydantic to use FastAPI and never explore what it can really do.

This document is for you if:
- You have seen Pydantic models in FastAPI code and want to understand them deeply
- You want to use Pydantic outside FastAPI (for data validation, configuration, or ETL pipelines)
- You want a complete reference covering every major feature
- You want to go from beginner to comfortable user in one document

We use **Pydantic v2** throughout. Where relevant, we note the differences from v1.

---

## 1. Why Pydantic Exists

### Data Validation Is Everywhere

Before we look at any code, let us think about where data validation shows up in real life:

- **Bank statement download:** A customer selects a start date and end date. What if the start date is after the end date? What if the date is in the future? What if they type "32nd January"? The bank's system must reject these before querying the database.

- **Online train booking (IRCTC):** A user selects the number of passengers. What if they enter -3? What if they enter 200? What if the "age" field for a passenger contains "young"? Every field must be validated before the booking proceeds.

- **UPI payment:** You enter a phone number and an amount. What if the phone number has 8 digits instead of 10? What if the amount is 0? What if the amount has three decimal places (INR 150.567)? The payment app must catch these before sending to the bank.

- **Job application form:** A candidate enters their email, years of experience, and expected salary. What if the expected salary is less than their current salary? What if the email is missing the @ symbol? What if years of experience is 200?

- **AI agent calling a tool:** An AI agent decides to search for flights with departure date "yesterday" and passengers "minus two." Without validation, the tool executes with nonsense inputs and returns garbage (or crashes).

In every case, bad data entering the system leads to one of three outcomes: a crash, a wrong result, or a security vulnerability. Validation is not optional. The question is: how do we do it cleanly?

### The Problem: Python Does Not Enforce Types

Python lets you write code like this:

```python
def create_user(name, age, email):
    return {"name": name, "age": age, "email": email}

user = create_user("Rahul", "twenty-five", "not-an-email")
# Python happily creates this user with age as a string and an invalid email.
```

Python does not stop you. The type hints you might add (`age: int`) are just documentation -- Python ignores them at runtime.

For small scripts, this is fine. But in real applications, data comes from unreliable sources: user input, API requests, configuration files, external services. If you do not validate this data at the boundary (where it enters your system), bad data propagates through your code and causes crashes in strange places far from the source.

### The Old Way: Manual Validation

Before Pydantic, validation looked like this:

```python
def create_user(name, age, email):
    # Validate name
    if not isinstance(name, str):
        raise ValueError("name must be a string")
    if len(name) < 1:
        raise ValueError("name cannot be empty")
    if len(name) > 100:
        raise ValueError("name is too long")
    
    # Validate age
    if not isinstance(age, int):
        raise ValueError("age must be an integer")
    if age < 0 or age > 150:
        raise ValueError("age must be between 0 and 150")
    
    # Validate email
    if not isinstance(email, str):
        raise ValueError("email must be a string")
    if "@" not in email:
        raise ValueError("invalid email format")
    # ... many more checks
    
    return {"name": name, "age": age, "email": email}
```

This is tedious, error-prone, and clutters the business logic. Every function that accepts data needs similar validation. When requirements change ("emails must now be lowercase"), you update every function that touches emails.

### What About Dataclasses?

Python 3.7 introduced `dataclasses`, which solve part of the problem. A dataclass gives you a structured object with named fields and type hints:

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int
    email: str

user = User(name="Rahul", age=25, email="rahul@example.com")
print(user.name)   # "Rahul"
print(user.age)    # 25
```

This is much cleaner than passing around raw dictionaries. But there is a critical limitation: **dataclasses do not validate.**

```python
# Dataclass accepts completely invalid data without complaint
user = User(name=12345, age="twenty-five", email="not-an-email")
print(user.name)    # 12345 (not a string)
print(user.age)     # "twenty-five" (not an int)
print(user.email)   # "not-an-email" (no validation)
# No error. No warning. Python does not care.
```

The type hints on a dataclass are documentation, nothing more. Python does not enforce them at runtime. You get a nice structured object, but any garbage can go into it.

You could add a `__post_init__` method to validate manually:

```python
@dataclass
class User:
    name: str
    age: int
    email: str

    def __post_init__(self):
        if not isinstance(self.name, str):
            raise ValueError("name must be a string")
        if not isinstance(self.age, int):
            raise ValueError("age must be an integer")
        if self.age < 0 or self.age > 150:
            raise ValueError("age must be between 0 and 150")
        if "@" not in self.email:
            raise ValueError("invalid email")
```

But now we are back to writing manual validation code. The dataclass gave us structure, but not validation. And it does not give us type coercion (converting `"25"` to `25`), serialisation (`to_dict()`, `to_json()`), or JSON schema generation.

Here is how the three approaches compare:

| Feature | Plain Function | Dataclass | Pydantic |
|---------|---------------|-----------|----------|
| Structured object | No (returns dict) | Yes | Yes |
| Type hints enforced at runtime | No | No | Yes |
| Automatic type coercion (str to int) | No | No | Yes |
| Built-in validation (min_length, ge, le) | No | No | Yes |
| Custom validators | Manual code | Manual `__post_init__` | `@field_validator` decorator |
| Cross-field validation | Manual code | Manual `__post_init__` | `@model_validator` decorator |
| Serialisation to dict/JSON | Manual | Manual or `asdict()` (no control over output) | `model_dump()` with include/exclude/alias |
| JSON Schema generation | No | No | Yes (automatic) |
| API documentation (OpenAPI) | No | No | Yes (powers FastAPI's Swagger) |
| Error messages | One at a time (first failure) | One at a time | All errors collected and reported together |
| Performance (v2) | Depends on code | Fast (no overhead) | Very fast (Rust core) |

Dataclasses are great for internal data structures where you trust the source (e.g., data your own code creates). Pydantic is for data that crosses a boundary: API requests, configuration files, external services, user input, or anything where you do not control the source.

### The Pydantic Way

Pydantic provides a declarative approach. You describe what valid data looks like. Pydantic handles the validation.

```python
from pydantic import BaseModel, EmailStr, Field

class User(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=0, le=150)
    email: EmailStr

# Valid data: creates the user
user = User(name="Rahul", age=25, email="rahul@example.com")

# Invalid data: raises a clear error
user = User(name="Rahul", age="twenty-five", email="not-an-email")
# Pydantic raises ValidationError with details about what failed
```

The model is shorter, clearer, and declarative. The validation logic is separated from the business logic. When requirements change, you update the model in one place.

### What Pydantic Actually Does

When you create a Pydantic model instance:
1. **Parsing:** Pydantic attempts to convert input values to the declared types. If you pass `"25"` where `int` is expected, Pydantic converts it to `25` (unless strict mode is on).
2. **Validation:** Each field is checked against its constraints (min_length, ge, le, etc.).
3. **Error collection:** If multiple fields fail, Pydantic collects all errors and raises them together, not one at a time.
4. **Object creation:** If everything passes, you get a Python object with attribute access (`user.name`) and type-safe methods.

This happens automatically every time you create a model instance. The validation is exhaustive and the errors are structured.

---

## 2. Your First Pydantic Model

### Installation

```bash
pip install pydantic
```

For features that need optional dependencies (like email validation):

```bash
pip install "pydantic[email]"
```

### The Smallest Possible Model

```python
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: float
    in_stock: bool

# Create an instance
product = Product(name="Cutting Chai", price=15.0, in_stock=True)

# Access the fields
print(product.name)        # "Cutting Chai"
print(product.price)       # 15.0
print(product.in_stock)    # True

# Convert to dictionary
print(product.model_dump())
# {"name": "Cutting Chai", "price": 15.0, "in_stock": True}

# Convert to JSON string
print(product.model_dump_json())
# '{"name":"Cutting Chai","price":15.0,"in_stock":true}'
```

That is it. Three lines define a validated data structure. Pydantic inherits from `BaseModel`, you declare fields with Python type hints, and you get validation, serialisation, and automatic documentation.

### What Happens with Invalid Data

```python
# Missing a required field
product = Product(name="Samosa", price=15.0)
# pydantic_core._pydantic_core.ValidationError:
# 1 validation error for Product
# in_stock: Field required

# Wrong type that cannot be converted
product = Product(name="Samosa", price="not a number", in_stock=True)
# ValidationError:
# price: Input should be a valid number, unable to parse string as a number

# Multiple errors at once
product = Product(name=None, price="abc", in_stock="maybe")
# ValidationError (3 errors):
# name: Input should be a valid string
# price: Input should be a valid number
# in_stock: Input should be a valid boolean
```

Pydantic reports all errors, not just the first one. This is useful for APIs that need to tell the client every problem with their request in one response.

### Type Coercion: "Parse, Don't Validate"

Pydantic tries to convert input to the expected type when reasonable:

```python
# Integer as a string -- converted to int
product = Product(name="Chai", price="15", in_stock=True)
print(type(product.price))   # <class 'float'>
print(product.price)         # 15.0

# "true"/"false" strings -- converted to bool
product = Product(name="Chai", price=15.0, in_stock="true")
print(product.in_stock)      # True

# Integer to float -- converted
product = Product(name="Chai", price=15, in_stock=True)
print(product.price)         # 15.0
```

This behaviour is useful when data comes from sources that do not preserve types (like query parameters, environment variables, or CSV files). If you want to reject type mismatches instead of converting, use **strict mode** (covered in section 15).

---

## 3. Field Types and the Basics

Pydantic supports all Python built-in types plus many specialised ones. Here are the common types you will use most often.

### Primitive Types

```python
from pydantic import BaseModel

class Example(BaseModel):
    # Text
    name: str           # Any string
    
    # Numbers
    age: int            # Integer
    price: float        # Floating-point number
    
    # Boolean
    is_active: bool     # True or False
    
    # Bytes
    data: bytes         # Binary data (file contents, etc.)
```

### Dates and Times

```python
from datetime import datetime, date, time, timedelta
from pydantic import BaseModel

class Event(BaseModel):
    scheduled_at: datetime   # Date and time: 2024-09-15T14:30:00
    event_date: date         # Date only: 2024-09-15
    start_time: time         # Time only: 14:30:00
    duration: timedelta      # Duration: P2H30M (2 hours 30 minutes)

# Pydantic accepts multiple formats
event = Event(
    scheduled_at="2024-09-15T14:30:00",    # ISO 8601 string
    event_date="2024-09-15",                # ISO date string
    start_time="14:30:00",                  # ISO time string
    duration=9000                           # Seconds (9000s = 2h30m)
)
```

ISO 8601 is the standard format for dates and times in APIs. Pydantic parses these strings into proper datetime objects.

### UUID

```python
from uuid import UUID, uuid4
from pydantic import BaseModel

class Transaction(BaseModel):
    id: UUID
    amount: float

# Pass a UUID string or a UUID object
t = Transaction(id="550e8400-e29b-41d4-a716-446655440000", amount=100.0)
t = Transaction(id=uuid4(), amount=100.0)
```

### Enums

Use enums to restrict a field to specific values:

```python
from enum import Enum
from pydantic import BaseModel

class OrderStatus(str, Enum):
    PENDING = "pending"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"

class Order(BaseModel):
    id: int
    status: OrderStatus

# Valid: accepts the enum value or its string value
order = Order(id=1, status="pending")          # Works
order = Order(id=1, status=OrderStatus.READY)  # Works

# Invalid: any other value rejected
order = Order(id=1, status="cooking")
# ValidationError: Input should be 'pending', 'preparing', 'ready' or 'delivered'
```

Inheriting from both `str` and `Enum` makes the enum JSON-serialisable. This is the pattern to use for APIs.

---

## 4. Optional Fields and Default Values

### Required vs Optional

By default, every field in a Pydantic model is **required**. If a field is missing when creating the model, Pydantic raises an error.

To make a field optional, use `Optional` or `| None` and provide a default:

```python
from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    username: str                    # Required
    email: str                        # Required
    bio: Optional[str] = None         # Optional, defaults to None
    # Equivalent syntax in modern Python:
    # bio: str | None = None

# Works: bio uses the default
user = User(username="rahul", email="rahul@example.com")
print(user.bio)  # None

# Works: bio is provided
user = User(username="rahul", email="rahul@example.com", bio="Python dev")
print(user.bio)  # "Python dev"
```

Just adding `Optional[str]` without a default does NOT make the field optional. It only widens the type to allow None. The field is still required (but can be None).

```python
class User(BaseModel):
    bio: Optional[str]   # Still required, but allows None

user = User()
# ValidationError: bio: Field required

user = User(bio=None)   # Works
```

This is a common source of confusion. To make a field truly optional (allowing it to be omitted), you need a default value.

### Default Values

```python
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: float
    is_available: bool = True          # Default value
    stock_count: int = 0                # Default value
    tags: list[str] = []                # Mutable default (see below)
    metadata: dict = {}                 # Mutable default

product = Product(name="Samosa", price=15.0)
print(product.is_available)   # True
print(product.stock_count)    # 0
```

### The Mutable Default Problem (Solved in Pydantic)

In regular Python, using mutable defaults in function signatures is dangerous:

```python
# DANGEROUS in regular Python
def add_item(item, tags=[]):
    tags.append(item)
    return tags

add_item("a")  # ['a']
add_item("b")  # ['a', 'b'] !!! All calls share the same list
```

Pydantic handles this correctly. Mutable defaults are safe:

```python
class Product(BaseModel):
    tags: list[str] = []

p1 = Product(name="A", price=10)
p1.tags.append("hot")

p2 = Product(name="B", price=20)
print(p2.tags)  # [] -- not affected by p1
```

Pydantic creates a new empty list for each instance, not sharing the default across instances.

### Default Factory: For Dynamic Defaults

When you need a default that is computed each time (like the current timestamp), use `default_factory`:

```python
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field

class Event(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    name: str

e1 = Event(name="First")
e2 = Event(name="Second")

print(e1.id)           # Different UUID
print(e2.id)           # Different UUID
print(e1.created_at)   # Timestamp when e1 was created
print(e2.created_at)   # Different timestamp
```

`default_factory` accepts a callable (a function with no arguments) that returns the default value.

---

## 5. The Field Function: Complete Reference

The `Field()` function adds constraints and metadata to fields. You have seen `min_length`, `max_length`, `ge`, and `le`. Here is the complete reference.

### String Constraints

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    username: str = Field(
        ...,                   # ... means "required" (no default)
        min_length=3,
        max_length=50,
        pattern=r"^[a-z0-9_]+$"   # Regex pattern
    )
    bio: str = Field(
        default="",
        max_length=500
    )
```

- `min_length` / `max_length`: Minimum/maximum string length
- `pattern`: Regex pattern the string must match

### Numeric Constraints

```python
class Product(BaseModel):
    price: float = Field(
        ...,
        gt=0,                  # Greater than 0
        le=10000               # Less than or equal to 10000
    )
    rating: int = Field(
        default=0,
        ge=0,                   # Greater than or equal to 0
        le=5                    # Less than or equal to 5
    )
    discount_percent: float = Field(
        default=0,
        ge=0,
        lt=100                  # Less than 100 (not equal)
    )
```

- `gt` / `ge`: Greater than / greater than or equal
- `lt` / `le`: Less than / less than or equal
- `multiple_of`: Value must be a multiple of this number

### Collection Constraints

```python
class Order(BaseModel):
    items: list[str] = Field(
        ...,
        min_length=1,          # At least one item
        max_length=20           # At most 20 items
    )
    tags: set[str] = Field(
        default=set(),
        max_length=10
    )
```

### Metadata Fields

`Field()` also accepts metadata that does not affect validation but appears in the JSON Schema (used by FastAPI's Swagger docs):

```python
class Product(BaseModel):
    name: str = Field(
        ...,
        description="The product name, displayed to customers",
        examples=["Cutting Chai", "Samosa", "Masala Chai"]
    )
    price: float = Field(
        ...,
        description="Price in INR",
        gt=0,
        examples=[15.0, 20.0, 30.0]
    )
    sku: str = Field(
        ...,
        alias="productCode",    # Accept "productCode" in input
        description="Stock-keeping unit identifier"
    )
```

These show up in the auto-generated API documentation when using FastAPI.

### The `...` Syntax

`Field(...)` means "this field is required and has no default value." The three dots are Python's `Ellipsis` constant. You might wonder why not just leave the default out. The reason: if you need to use `Field()` to add constraints or metadata to a required field, you need some placeholder for the default position. `...` is the convention.

```python
# These are equivalent for a required field:
name: str                            # Required, no constraints
name: str = Field(...)               # Required, no constraints
name: str = Field(..., min_length=1) # Required, with constraint
```

You cannot write `name: str = Field(min_length=1)` without `...` because Pydantic treats that as "default is the Field object itself," which is not what you want.

---

## 6. Specialised Types

Pydantic provides types for common validation patterns beyond primitives.

### Email, URL, and Other Network Types

```python
from pydantic import BaseModel, EmailStr, HttpUrl, IPvAnyAddress

class Contact(BaseModel):
    email: EmailStr              # Validates email format (requires email-validator package)
    website: HttpUrl             # Validates URL format
    server_ip: IPvAnyAddress     # IPv4 or IPv6 address

contact = Contact(
    email="rahul@example.com",
    website="https://rahul.dev",
    server_ip="192.168.1.1"
)

# Invalid email rejected
contact = Contact(email="not-an-email", website="https://a.com", server_ip="0.0.0.0")
# ValidationError: email: value is not a valid email address
```

To use `EmailStr`, install the email-validator extra: `pip install "pydantic[email]"`.

### Positive and Negative Numbers

```python
from pydantic import BaseModel, PositiveInt, NegativeInt, NonNegativeInt, NonNegativeFloat

class Measurements(BaseModel):
    quantity: PositiveInt         # Must be > 0
    temperature_c: NegativeInt    # Must be < 0
    count: NonNegativeInt          # Must be >= 0
    weight_kg: NonNegativeFloat    # Must be >= 0
```

These are shortcuts for `Field(gt=0)`, `Field(lt=0)`, `Field(ge=0)`, etc. They make models more readable.

### Constrained Types with Annotated

Imagine you have a "username" field that appears in 5 different models: User, Assignment, Comment, Review, Profile. In each model, the username must follow the same rules: 3-50 characters, lowercase alphanumeric with underscores. Do you copy the same `Field(min_length=3, max_length=50, pattern=...)` into all 5 models?

You could create a separate Pydantic model for just a username, but that feels heavy. A username is not a complex object -- it is just a string with rules. What you want is a way to say "this is a str, but with these specific constraints" and reuse that definition everywhere.

That is exactly what `Annotated` does. `Annotated` is a Python typing feature (from `typing`) that lets you attach extra information (metadata) to a type. Pydantic reads this metadata and uses it for validation.

```python
from typing import Annotated
from pydantic import BaseModel, Field

# Annotated[base_type, metadata] means:
# "This is a base_type, but with this additional metadata (constraints)."

# Define reusable constrained types.
# Username is just a str, but with specific rules attached.
Username = Annotated[str, Field(min_length=3, max_length=50, pattern=r"^[a-z0-9_]+$")]
Password = Annotated[str, Field(min_length=8, max_length=128)]
Percentage = Annotated[float, Field(ge=0, le=100)]

# Now use these types in any model.
# The validation rules are baked into the type itself.
class User(BaseModel):
    username: Username      # Validated: 3-50 chars, lowercase alphanumeric
    password: Password      # Validated: 8-128 chars
    completion_percent: Percentage  # Validated: 0-100

class Assignment(BaseModel):
    assigned_to: Username   # Same validation as User.username -- guaranteed consistent
    progress: Percentage     # Same validation as User.completion_percent
```

**Why not a separate Pydantic class?** Because a username is not a complex structured object. It is a string with rules. Creating a `class Username(BaseModel): value: str = Field(...)` would mean every field that uses it becomes a nested object instead of a simple string. `Annotated` keeps it as a plain `str` in the input and output, but with validation rules attached.

**Why not just copy `Field(...)` everywhere?** Because when you need to change the rules (say, increase max_length from 50 to 60), you update it in one place instead of hunting through every model.

This keeps validation rules consistent across models and makes the intent clear: `Username` is not just any string, it is a string that follows specific rules.

### File-Related Types

```python
from pathlib import Path
from pydantic import BaseModel, FilePath, DirectoryPath

class Config(BaseModel):
    log_file: FilePath            # Path must exist and be a file
    data_dir: DirectoryPath       # Path must exist and be a directory
    output_path: Path              # Any path (no validation of existence)
```

---

## 7. Nested Models

Pydantic models can contain other Pydantic models as fields. This is how you handle complex, structured data.

### Basic Nesting

```python
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    state: str
    pincode: str

class User(BaseModel):
    name: str
    email: str
    address: Address   # Nested model

# Create with nested dict
user = User(
    name="Rahul Sharma",
    email="rahul@example.com",
    address={
        "street": "123 MG Road",
        "city": "Bangalore",
        "state": "Karnataka",
        "pincode": "560001"
    }
)

# Access nested fields
print(user.address.city)       # "Bangalore"
print(user.address.pincode)    # "560001"

# The nested dict is converted to an Address instance
print(type(user.address))      # <class '__main__.Address'>
```

When you pass a dict for a nested field, Pydantic creates the nested model instance automatically and validates it.

### Deeply Nested Models

```python
class Coordinates(BaseModel):
    latitude: float
    longitude: float

class Location(BaseModel):
    address: Address
    coordinates: Coordinates

class Restaurant(BaseModel):
    name: str
    cuisine: str
    location: Location
    rating: float

restaurant = Restaurant(
    name="Paradise Biryani",
    cuisine="Hyderabadi",
    location={
        "address": {
            "street": "Shop 5, Paradise Circle",
            "city": "Hyderabad",
            "state": "Telangana",
            "pincode": "500003"
        },
        "coordinates": {
            "latitude": 17.4342,
            "longitude": 78.4489
        }
    },
    rating=4.5
)

print(restaurant.location.coordinates.latitude)  # 17.4342
```

Each level of nesting is validated independently. Errors are reported with the full path (e.g., `location.coordinates.latitude`).

### When to Use Nested Models

Use nesting when the data has clear substructure that might be used independently:
- A user has an address (the address might be used elsewhere)
- A restaurant has a location (latitude/longitude is a reusable concept)
- An order has a shipping address and a billing address

Do not nest just because you can. If a field has only two sub-fields that are always used together (like `first_name` and `last_name`), just put them directly on the parent model.

---

## 8. Lists, Dicts, and Collections

### Lists

```python
from pydantic import BaseModel

class Post(BaseModel):
    title: str
    tags: list[str]                    # List of strings
    view_counts: list[int]              # List of integers

post = Post(
    title="My First Post",
    tags=["python", "tutorial", "beginners"],
    view_counts=[100, 150, 200]
)

# Validation: wrong types in the list are rejected
post = Post(title="...", tags=["ok", 123, "ok"], view_counts=[1, 2, 3])
# ValidationError: tags.1: Input should be a valid string
```

### Lists of Models

```python
class Comment(BaseModel):
    author: str
    text: str

class Post(BaseModel):
    title: str
    comments: list[Comment]

post = Post(
    title="Hello World",
    comments=[
        {"author": "Alice", "text": "Great post!"},
        {"author": "Bob", "text": "Thanks for sharing"},
    ]
)

print(post.comments[0].author)  # "Alice"
print(type(post.comments[0]))   # <class '__main__.Comment'>
```

Each dict in the list is converted to a Comment instance and validated.

### Dictionaries

```python
class Product(BaseModel):
    name: str
    attributes: dict[str, str]           # Keys and values are strings
    prices_by_size: dict[str, float]    # Keys are strings, values are floats

product = Product(
    name="T-Shirt",
    attributes={"color": "blue", "material": "cotton"},
    prices_by_size={"S": 499, "M": 599, "L": 699}
)
```

### Sets and Tuples

```python
class Config(BaseModel):
    allowed_ips: set[str]                  # Unique values, order does not matter
    dimensions: tuple[int, int, int]        # Fixed-length tuple (width, height, depth)
    point: tuple[float, float]              # 2D point

config = Config(
    allowed_ips={"192.168.1.1", "192.168.1.2"},
    dimensions=(100, 200, 50),
    point=(17.4342, 78.4489)
)
```

Sets automatically remove duplicates. Tuples have fixed structure.

### Nested Collections

```python
class Classroom(BaseModel):
    students_by_section: dict[str, list[str]]
    # {"A": ["Rahul", "Priya"], "B": ["Amit", "Sneha"]}

class Matrix(BaseModel):
    values: list[list[float]]
    # [[1.0, 2.0], [3.0, 4.0]]
```

Type hints compose naturally. `dict[str, list[str]]` means "a dictionary with string keys and list-of-strings values."

---

## 9. Union Types and Optional

### Union: Accept Multiple Types

```python
from pydantic import BaseModel

class Response(BaseModel):
    # Accepts either an integer or a string
    code: int | str
    # Pre-3.10 syntax: Union[int, str] from typing

response = Response(code=200)      # int
response = Response(code="OK")     # str
response = Response(code=[])       # ValidationError
```

When Pydantic parses a union, it tries each type in order and uses the first one that works. You can control this order with `discriminated unions` (covered in section 17).

### Optional: The Most Common Union

`Optional[X]` is shorthand for `X | None`:

```python
from typing import Optional

class User(BaseModel):
    name: str
    # These are equivalent:
    bio: Optional[str] = None
    nickname: str | None = None
```

Both allow the field to be a string or None, with None as the default.

---

## 10. Custom Validators

When Pydantic's built-in validation is not enough, you write custom validators using decorators.

### @field_validator

A field validator runs on a specific field:

```python
from pydantic import BaseModel, field_validator

class User(BaseModel):
    username: str
    email: str

    @field_validator("username")
    @classmethod
    def username_must_be_lowercase(cls, v: str) -> str:
        """Ensure username is lowercase and has no spaces."""
        if " " in v:
            raise ValueError("Username cannot contain spaces")
        return v.lower()

    @field_validator("email")
    @classmethod
    def email_must_be_lowercase(cls, v: str) -> str:
        """Normalise email to lowercase."""
        return v.lower().strip()

user = User(username="Rahul_Dev", email="RAHUL@example.com  ")
print(user.username)  # "rahul_dev"
print(user.email)     # "rahul@example.com"

user = User(username="has spaces", email="test@a.com")
# ValidationError: Username cannot contain spaces
```

Key points:
- The decorator takes the field name(s) as argument
- The method must be a `@classmethod`
- `v` is the value being validated
- Return the (possibly modified) value
- Raise `ValueError` for validation failures

### Validating Multiple Fields with One Validator

```python
class Post(BaseModel):
    title: str
    summary: str
    content: str

    @field_validator("title", "summary", "content")
    @classmethod
    def no_trailing_whitespace(cls, v: str) -> str:
        """Strip whitespace from all text fields."""
        return v.strip()
```

### Validator Modes: Before vs After

By default, validators run **after** Pydantic's built-in validation and type coercion. You can run them **before** with `mode="before"`:

```python
class Product(BaseModel):
    price: float

    @field_validator("price", mode="before")
    @classmethod
    def parse_rupee_string(cls, v):
        """Accept prices as strings like 'Rs 15' or '15 INR'."""
        if isinstance(v, str):
            # Remove non-numeric characters
            cleaned = "".join(c for c in v if c.isdigit() or c == ".")
            return float(cleaned)
        return v

product = Product(price="Rs 15.50")
print(product.price)  # 15.5

product = Product(price="15 INR")
print(product.price)  # 15.0

product = Product(price=20)
print(product.price)  # 20.0
```

`mode="before"` validators receive the raw input (before type coercion). They are useful for cleaning data. `mode="after"` (the default) validators receive the validated, type-coerced value.

---

## 11. Model Validators

Field validators work on a single field at a time. When you need to validate across multiple fields, use a **model validator**.

### @model_validator: Validate the Whole Model

```python
from pydantic import BaseModel, model_validator
from typing import Self

class DateRange(BaseModel):
    start_date: str
    end_date: str

    @model_validator(mode="after")
    def check_dates(self) -> Self:
        """Ensure start_date is before end_date."""
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self

# Valid
dr = DateRange(start_date="2024-01-01", end_date="2024-12-31")

# Invalid: start after end
dr = DateRange(start_date="2024-12-31", end_date="2024-01-01")
# ValidationError: start_date must be before end_date
```

Key points:
- `mode="after"`: Runs after all fields are validated. You access `self.field_name`.
- Must return `self`
- Type hint the return as `Self` (imported from typing)

### @model_validator(mode="before"): Validate the Raw Input

```python
from pydantic import BaseModel, model_validator

class User(BaseModel):
    username: str
    email: str

    @model_validator(mode="before")
    @classmethod
    def check_username_or_email(cls, data):
        """Require at least one of username or email."""
        if isinstance(data, dict):
            if not data.get("username") and not data.get("email"):
                raise ValueError("Must provide at least one of username or email")
        return data
```

`mode="before"` receives the raw input (a dict). Useful when you need to inspect or modify the data before validation.

### Cross-Field Validation Example

```python
class Password(BaseModel):
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

# Valid
p = Password(password="secret123", confirm_password="secret123")

# Invalid
p = Password(password="secret123", confirm_password="different")
# ValidationError: Passwords do not match
```

---

## 12. Serialisation and Exporting Data

Once you have a validated model, you often need to export it: to JSON for an API response, to a dict for internal use, or to a database.

### model_dump(): Convert to Dictionary

```python
class User(BaseModel):
    id: int
    username: str
    email: str
    bio: str | None = None

user = User(id=1, username="rahul", email="rahul@example.com", bio="Developer")

# Convert to dict
data = user.model_dump()
print(data)
# {"id": 1, "username": "rahul", "email": "rahul@example.com", "bio": "Developer"}
```

### model_dump_json(): Convert to JSON String

```python
json_str = user.model_dump_json()
print(json_str)
# '{"id":1,"username":"rahul","email":"rahul@example.com","bio":"Developer"}'

# Pretty-printed
print(user.model_dump_json(indent=2))
# {
#   "id": 1,
#   "username": "rahul",
#   ...
# }
```

### Include and Exclude Fields

```python
# Only include specific fields
user.model_dump(include={"id", "username"})
# {"id": 1, "username": "rahul"}

# Exclude specific fields
user.model_dump(exclude={"email", "bio"})
# {"id": 1, "username": "rahul"}

# For nested models
class Post(BaseModel):
    title: str
    author: User

post = Post(title="Hello", author=user)
post.model_dump(exclude={"author": {"email"}})
# {"title": "Hello", "author": {"id": 1, "username": "rahul", "bio": "Developer"}}
```

### exclude_unset: Only Explicitly Set Fields

```python
class User(BaseModel):
    id: int
    username: str
    bio: str | None = None
    is_active: bool = True

# Only username and id are set; others have defaults
user = User(id=1, username="rahul")

user.model_dump()
# {"id": 1, "username": "rahul", "bio": None, "is_active": True}

user.model_dump(exclude_unset=True)
# {"id": 1, "username": "rahul"}
# Fields with defaults are excluded
```

This is very useful for PATCH endpoints in FastAPI: you only want to update the fields the client actually sent, not overwrite with defaults.

### exclude_defaults and exclude_none

```python
# Exclude fields whose value equals their default
user.model_dump(exclude_defaults=True)
# {"id": 1, "username": "rahul"}  -- bio=None and is_active=True are defaults

# Exclude fields whose value is None
user.model_dump(exclude_none=True)
# {"id": 1, "username": "rahul", "is_active": True}  -- bio is excluded
```

### Custom Serialisation with @field_serializer

```python
from datetime import datetime
from pydantic import BaseModel, field_serializer

class Event(BaseModel):
    name: str
    scheduled_at: datetime
    price: float

    @field_serializer("scheduled_at")
    def serialize_datetime(self, value: datetime) -> str:
        """Format datetime as 'DD/MM/YYYY HH:MM'."""
        return value.strftime("%d/%m/%Y %H:%M")

    @field_serializer("price")
    def serialize_price(self, value: float) -> str:
        """Format price as 'INR 1,500.00'."""
        return f"INR {value:,.2f}"

event = Event(name="Conference", scheduled_at=datetime(2024, 9, 15, 14, 30), price=1500.0)
print(event.model_dump())
# {"name": "Conference", "scheduled_at": "15/09/2024 14:30", "price": "INR 1,500.00"}
```

Field serialisers let you customise how each field appears in the output without affecting how the data is stored internally.

---

## 13. Model Configuration

Pydantic models have configuration options that change their behaviour. In v2, you configure models using `ConfigDict`:

```python
from pydantic import BaseModel, ConfigDict

class User(BaseModel):
    model_config = ConfigDict(
        # Allow creating from object attributes (not just dicts)
        from_attributes=True,
        
        # Validate when values are assigned to fields
        validate_assignment=True,
        
        # Make instances immutable (frozen)
        frozen=True,
        
        # Control how extra fields in input are handled
        extra="forbid",  # or "allow" or "ignore"
        
        # Accept enum values instead of enum instances
        use_enum_values=True,
        
        # Strip whitespace from strings
        str_strip_whitespace=True,
        
        # Convert strings to lowercase
        str_to_lower=False
    )
    
    username: str
    email: str
```

### from_attributes: Working with ORMs

By default, Pydantic creates model instances from dictionaries:

```python
user = User(id=1, username="rahul", email="rahul@example.com")     # keyword arguments
user = User(**{"id": 1, "username": "rahul", "email": "rahul@example.com"})  # unpacked dict
```

But when you use an ORM like SQLAlchemy, your database queries do not return dictionaries. They return Python objects with attributes:

```python
# When you query the database with SQLAlchemy:
db_user = db.query(UserModel).filter(UserModel.id == 1).first()

# db_user is NOT a dict. It is a SQLAlchemy object.
# You access data via attributes: db_user.id, db_user.username, db_user.email
# You CANNOT do db_user["id"] -- that would raise a TypeError.
```

Now you want to return this from a FastAPI endpoint as a Pydantic response model. The problem: Pydantic does not know how to read data from object attributes. It only knows dictionaries. So it fails.

`model_validate()` is Pydantic's method for creating a model instance from external data (like a dict, a JSON string, or an object). Without `from_attributes`, it can only read dicts. With `from_attributes=True`, it can also read object attributes:

```python
from pydantic import BaseModel, ConfigDict

# A SQLAlchemy-like object (simplified for this example)
class DBUser:
    def __init__(self):
        self.id = 1
        self.username = "rahul"
        self.email = "rahul@example.com"

# WITHOUT from_attributes:
class UserSchema(BaseModel):
    id: int
    username: str
    email: str

db_user = DBUser()
# user = UserSchema.model_validate(db_user)
# ERROR: Pydantic tries to read db_user as a dict, fails because
# it is an object with attributes, not a dict with keys.

# WITH from_attributes:
class UserSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # This tells Pydantic: "When validating, try reading from object
    # attributes (obj.id, obj.username) not just dict keys (obj["id"])."
    id: int
    username: str
    email: str

db_user = DBUser()
user = UserSchema.model_validate(db_user)  # Now it works!
print(user.username)  # "rahul"
```

This is essential when using FastAPI with SQLAlchemy. FastAPI automatically calls `model_validate()` on your return value when you set a `response_model`. If the return value is a SQLAlchemy object and the schema does not have `from_attributes=True`, the endpoint crashes.

### validate_assignment

By default, Pydantic only validates when you create the instance. Setting fields later bypasses validation:

```python
class Product(BaseModel):
    price: float = Field(..., gt=0)

product = Product(price=100.0)
product.price = -5.0   # No validation by default
print(product.price)   # -5.0 (invalid but accepted)
```

With `validate_assignment=True`, every assignment is validated:

```python
class Product(BaseModel):
    model_config = ConfigDict(validate_assignment=True)
    price: float = Field(..., gt=0)

product = Product(price=100.0)
product.price = -5.0   # ValidationError: Input should be greater than 0
```

### frozen: Immutable Models

`frozen=True` makes instances immutable (like namedtuples):

```python
class Point(BaseModel):
    model_config = ConfigDict(frozen=True)
    x: float
    y: float

p = Point(x=1.0, y=2.0)
p.x = 5.0  # TypeError: Cannot change field 'x' of frozen model
```

Frozen models are also hashable, so they can be used as dictionary keys or in sets.

### extra: Handling Unknown Fields

```python
# extra="ignore" (default): unknown fields are silently dropped
class User(BaseModel):
    username: str

u = User(username="rahul", unknown_field="ignored")
print(u.model_dump())  # {"username": "rahul"}

# extra="forbid": unknown fields cause validation errors
class StrictUser(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str

u = StrictUser(username="rahul", unknown_field="fail")
# ValidationError: unknown_field: Extra inputs are not permitted

# extra="allow": unknown fields are kept
class FlexibleUser(BaseModel):
    model_config = ConfigDict(extra="allow")
    username: str

u = FlexibleUser(username="rahul", custom_field="value")
print(u.model_dump())  # {"username": "rahul", "custom_field": "value"}
```

Use `forbid` for strict APIs where unknown fields indicate client errors. Use `allow` for flexible data structures. The default `ignore` is a middle ground.

---

## 14. Aliases: Handling Different Naming Conventions

APIs often use camelCase or snake_case or some other convention that does not match Python's snake_case. Aliases let you accept one name and use another internally.

### Basic Alias

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    user_id: int = Field(alias="userId")
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")

# Input uses camelCase
user = User(**{
    "userId": 1,
    "firstName": "Rahul",
    "lastName": "Sharma"
})

# Access using Python snake_case
print(user.user_id)      # 1
print(user.first_name)   # "Rahul"
```

### Populate by Name

By default, aliases replace the field name. If you want to accept either the alias or the original name:

```python
class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    user_id: int = Field(alias="userId")

# Both work now:
u1 = User(userId=1)      # By alias
u2 = User(user_id=1)     # By field name
```

### Separate Input and Output Aliases

You can have different aliases for input (validation) and output (serialisation):

```python
class User(BaseModel):
    first_name: str = Field(
        alias="firstName",              # Input: accepts "firstName"
        serialization_alias="fname"     # Output: produces "fname"
    )

user = User(firstName="Rahul")
print(user.model_dump(by_alias=True))   # {"fname": "Rahul"}
```

### AliasChoices: Multiple Input Names

Accept any of several names for the same field:

```python
from pydantic import AliasChoices, BaseModel, Field

class User(BaseModel):
    email: str = Field(
        alias=AliasChoices("email", "emailAddress", "email_address")
    )

# All work:
User(email="a@b.com")
User(emailAddress="a@b.com")
User(email_address="a@b.com")
```

This is useful when integrating with multiple APIs that use different conventions for the same field.

---

## 15. Strict vs Lax Mode

By default, Pydantic tries to convert input to the expected type. This is called **lax mode**. In **strict mode**, Pydantic rejects type mismatches instead of converting.

### Lax Mode (Default)

```python
class Product(BaseModel):
    price: float

# These all work in lax mode
Product(price=15)          # int -> float
Product(price="15.0")       # str -> float
Product(price="15")         # str -> float
```

### Strict Mode at the Field Level

```python
from pydantic import BaseModel, StrictInt, StrictFloat, StrictStr, StrictBool

class Product(BaseModel):
    price: StrictFloat     # Only accepts float, rejects int and str
    quantity: StrictInt    # Only accepts int
    name: StrictStr         # Only accepts str

Product(price=15.0, quantity=10, name="Samosa")  # Works

Product(price=15, quantity=10, name="Samosa")
# ValidationError: price: Input should be a valid number (strict)

Product(price="15.0", quantity=10, name="Samosa")
# ValidationError: price: Input should be a valid number (strict)
```

### Strict Mode at the Model Level

```python
from pydantic import BaseModel, ConfigDict

class Product(BaseModel):
    model_config = ConfigDict(strict=True)
    
    price: float
    quantity: int
    name: str

Product(price="15.0", quantity=10, name="Samosa")
# ValidationError: price: Input should be a valid number
```

### When to Use Strict Mode

- **APIs with rigid contracts:** When the client should send data in exact types
- **Internal services:** When data comes from another trusted system that should send correct types
- **Financial or critical data:** Where type coercion could introduce subtle bugs

Use lax mode for:
- **Web forms:** Browsers send everything as strings
- **Query parameters:** Same reason
- **CSV files:** All values are strings
- **Environment variables:** Always strings

---

## 16. Computed Fields

A computed field is a field whose value is calculated from other fields. It appears in the output but is not stored.

```python
from pydantic import BaseModel, computed_field

class Rectangle(BaseModel):
    width: float
    height: float

    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height

    @computed_field
    @property
    def perimeter(self) -> float:
        return 2 * (self.width + self.height)

r = Rectangle(width=5.0, height=3.0)
print(r.area)        # 15.0
print(r.perimeter)   # 16.0

print(r.model_dump())
# {"width": 5.0, "height": 3.0, "area": 15.0, "perimeter": 16.0}
```

Computed fields:
- Appear in `model_dump()` and `model_dump_json()` output
- Are read-only (you cannot set them)
- Are not validated (they are always derived from other fields)
- Show up in JSON Schema

### Real-World Example: User Full Name

```python
class User(BaseModel):
    first_name: str
    last_name: str

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @computed_field
    @property
    def initials(self) -> str:
        return f"{self.first_name[0]}.{self.last_name[0]}."

user = User(first_name="Rahul", last_name="Sharma")
print(user.full_name)  # "Rahul Sharma"
print(user.initials)   # "R.S."

print(user.model_dump())
# {
#   "first_name": "Rahul",
#   "last_name": "Sharma",
#   "full_name": "Rahul Sharma",
#   "initials": "R.S."
# }
```

---

## 17. Discriminated Unions

When a field can be one of several models, and you can distinguish them by a specific field, use a discriminated union. This is more efficient and produces better error messages than regular unions.

### The Problem

Suppose a notification can be an email, SMS, or push notification, each with different fields:

```python
from typing import Literal
from pydantic import BaseModel

class EmailNotification(BaseModel):
    type: Literal["email"]
    email_address: str
    subject: str
    body: str

class SmsNotification(BaseModel):
    type: Literal["sms"]
    phone_number: str
    message: str

class PushNotification(BaseModel):
    type: Literal["push"]
    device_token: str
    title: str
    body: str
```

### Without Discriminator (Regular Union)

```python
class NotificationRequest(BaseModel):
    notification: EmailNotification | SmsNotification | PushNotification

# Pydantic tries each type in order until one works.
# Error messages are complicated and slow for large unions.
```

### With Discriminator

```python
from typing import Union
from pydantic import BaseModel, Field

class NotificationRequest(BaseModel):
    notification: Union[EmailNotification, SmsNotification, PushNotification] = Field(
        ..., discriminator="type"
    )
    # The "type" field distinguishes which model to use

# Pydantic looks at the "type" field and directly picks the right model.
# Faster validation and clearer error messages.

# Valid
NotificationRequest(notification={
    "type": "email",
    "email_address": "rahul@example.com",
    "subject": "Hello",
    "body": "Hi!"
})

# Wrong type field
NotificationRequest(notification={"type": "fax", ...})
# ValidationError: Input tag 'fax' found using 'type' does not match any of the expected tags
```

### Why This Matters

- **Performance:** Pydantic does not try each type -- it goes directly to the right one
- **Error messages:** Errors reference the correct type, not all possibilities
- **JSON Schema:** Generated schemas properly document the discriminated union

---

## 18. Generic Models

### The Idea: One Template, Many Types

Imagine you are building an API. Every endpoint returns a response in the same wrapper:

```json
{
    "success": true,
    "data": { ... the actual content ... },
    "error": null
}
```

The wrapper is always the same: `success`, `data`, `error`. But the `data` field is different for every endpoint. For `/users/1`, `data` is a User. For `/posts/5`, `data` is a Post. For `/tags`, `data` is a list of Tags.

Without generics, you end up writing a separate wrapper for every type:

```python
# You write this once...
class UserResponse(BaseModel):
    success: bool
    data: User | None
    error: str | None

# ...and then copy-paste for every new type
class PostResponse(BaseModel):
    success: bool
    data: Post | None     # Only this line changes
    error: str | None

class CommentResponse(BaseModel):
    success: bool
    data: Comment | None  # Only this line changes
    error: str | None

# 10 resources = 10 nearly identical classes. Tedious.
```

What you want is a way to say: "The wrapper is always the same. Only the type of `data` changes. Let me define the wrapper once and fill in the type later."

That is what generics do.

### What is TypeVar?

`TypeVar` creates a **type placeholder** -- a blank slot that gets filled in when you use the model. Think of it like a blank in a fill-in-the-blank sentence:

"The response contains a `____` in the data field."

```python
from typing import TypeVar, Generic

# T is a placeholder. It does not represent any specific type yet.
# It means "some type, to be decided later."
T = TypeVar("T")
```

When you write `ApiResponse[User]`, the `T` placeholder gets replaced with `User`. When you write `ApiResponse[Post]`, `T` gets replaced with `Post`. Same template, different type filled in.

### Building a Generic Model

```python
from typing import TypeVar, Generic, Optional
from pydantic import BaseModel

# Step 1: Create the type placeholder
T = TypeVar("T")

class User(BaseModel):
    id: int
    name: str

class Post(BaseModel):
    id: int
    title: str

# Step 2: Define the generic model.
# Generic[T] tells Python and Pydantic that this class has a type placeholder T.
# The 'data' field uses T -- its actual type will be decided when the model is used.
class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None    # <-- T is the placeholder. Could be User, Post, anything.
    error: Optional[str] = None

# Step 3: Use it by filling in the placeholder.
# ApiResponse[User] means: "ApiResponse where T = User"
# So 'data' becomes Optional[User] -- Pydantic validates it as a User.
user_response = ApiResponse[User](
    success=True,
    data=User(id=1, name="Rahul")    # Pydantic validates this as a User
)

# ApiResponse[Post] means: "ApiResponse where T = Post"
# So 'data' becomes Optional[Post] -- Pydantic validates it as a Post.
post_response = ApiResponse[Post](
    success=True,
    data=Post(id=5, title="Hello World")   # Pydantic validates this as a Post
)

# You can also pass dicts -- Pydantic creates the inner model from the dict:
user_response = ApiResponse[User](
    success=True,
    data={"id": 1, "name": "Rahul"}   # Dict is validated and converted to User
)

# ApiResponse[list[User]] means: "ApiResponse where T = list[User]"
# So 'data' becomes Optional[list[User]].
users_response = ApiResponse[list[User]](
    success=True,
    data=[
        {"id": 1, "name": "Rahul"},
        {"id": 2, "name": "Priya"}
    ]
)

# Error response (no data)
error_response = ApiResponse[User](
    success=False,
    error="User not found"
)
```

One definition (`ApiResponse`), used with any type. Pydantic validates `data` against the actual type each time. If you pass a Post dict where a User is expected, Pydantic rejects it.

### Pagination Example

A paginated list is another common wrapper. The page metadata (page number, total, etc.) is always the same. Only the item type changes.

```python
from pydantic import BaseModel, Field, computed_field
from typing import TypeVar, Generic

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """A page of results. Works with any item type.
    
    PaginatedResponse[User] = a page of users.
    PaginatedResponse[Post] = a page of posts.
    """
    items: list[T]                              # The actual items on this page
    page: int = Field(..., ge=1)                # Current page number (1-based)
    page_size: int = Field(..., ge=1, le=100)   # Items per page
    total: int = Field(..., ge=0)               # Total items across all pages

    @computed_field
    @property
    def total_pages(self) -> int:
        """Calculate how many pages exist."""
        if self.total == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    @computed_field
    @property
    def has_next(self) -> bool:
        """Is there a next page?"""
        return self.page < self.total_pages

    @computed_field
    @property
    def has_previous(self) -> bool:
        """Is there a previous page?"""
        return self.page > 1

# Use with Users
users_page = PaginatedResponse[User](
    items=[
        User(id=1, name="Rahul"),
        User(id=2, name="Priya")
    ],
    page=1,
    page_size=10,
    total=25      # 25 total users across all pages
)

print(users_page.total_pages)    # 3
print(users_page.has_next)       # True (page 1 of 3)
print(users_page.has_previous)   # False (already on page 1)

# Use with Posts -- same wrapper, different item type
posts_page = PaginatedResponse[Post](
    items=[Post(id=10, title="My First Post")],
    page=3,
    page_size=10,
    total=25
)
print(posts_page.has_next)       # False (page 3 of 3)
print(posts_page.has_previous)   # True
```

The wrapper (pagination metadata, computed fields) is defined once. The item type changes each time you use it. This is the power of generics: you write the pattern once and reuse it everywhere.

---

## 19. Pydantic Settings: Configuration Management

Pydantic Settings is a separate package for managing application configuration from environment variables, `.env` files, and other sources.

### Installation

```bash
pip install pydantic-settings
```

### Basic Usage

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Required settings (will error if missing)
    database_url: str
    secret_key: str
    
    # Optional with defaults
    debug: bool = False
    log_level: str = "INFO"
    max_connections: int = 100

# Load settings from environment and .env file
settings = Settings()

print(settings.database_url)
print(settings.debug)
```

With a `.env` file:

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost/mydb
SECRET_KEY=super-secret-key
DEBUG=true
LOG_LEVEL=DEBUG
MAX_CONNECTIONS=200
```

Pydantic automatically:
- Reads the `.env` file
- Matches variables (case-insensitive by default): `DATABASE_URL` becomes `database_url`
- Parses types: `"true"` becomes `True`, `"200"` becomes `200`
- Raises errors for missing required fields

### Environment Variables Take Priority

```bash
# Terminal
export DATABASE_URL=postgresql://prod-server/proddb
python app.py
```

Environment variables override `.env` file values. This lets you use `.env` for development defaults and real environment variables in production.

### Nested Settings

```python
class DatabaseSettings(BaseSettings):
    host: str = "localhost"
    port: int = 5432
    name: str
    user: str
    password: str

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_nested_delimiter="__"
    )
    
    app_name: str = "MyApp"
    debug: bool = False
    database: DatabaseSettings

# In .env:
# APP_NAME=BlogPlatform
# DATABASE__HOST=db.example.com
# DATABASE__NAME=blogdb
# DATABASE__USER=admin
# DATABASE__PASSWORD=secret
```

The `__` delimiter lets you set nested fields through environment variables.

### Singleton Pattern

Loading settings involves reading the `.env` file, parsing values, and validating them. You do not want to do this every time a function needs a configuration value. You want to load settings once, at startup, and reuse the same instance everywhere.

This is called the **singleton pattern**: create one instance and share it. In Python, the simplest way is `lru_cache`, which remembers the result of a function call and returns the cached result on subsequent calls:

```python
# config.py
from functools import lru_cache

@lru_cache()
def get_settings() -> Settings:
    """Load settings once and cache the result.
    
    The first call creates a Settings instance (reads .env, validates).
    Every subsequent call returns the exact same instance without
    re-reading the file or re-validating.
    """
    return Settings()

# Anywhere in your app:
from config import get_settings

settings = get_settings()  # First call: reads .env, creates Settings
settings = get_settings()  # Second call: returns the cached instance (instant)

# In a FastAPI dependency:
from fastapi import Depends

def get_db_url(settings: Settings = Depends(get_settings)):
    return settings.database_url
```

---

## 20. JSON Schema Generation

Pydantic models automatically generate JSON Schema, a standard way to describe data structure. This is how FastAPI produces its OpenAPI documentation.

### Generating Schema

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int = Field(..., description="Unique user ID")
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="User's email address")
    is_active: bool = True

schema = User.model_json_schema()
print(schema)
```

Output:

```json
{
    "properties": {
        "id": {"description": "Unique user ID", "type": "integer"},
        "username": {"maxLength": 50, "minLength": 3, "type": "string"},
        "email": {"description": "User's email address", "type": "string"},
        "is_active": {"default": true, "type": "boolean"}
    },
    "required": ["id", "username", "email"],
    "type": "object"
}
```

### What This Schema Enables

- **API documentation:** Tools like Swagger UI render this as interactive docs
- **Client code generation:** Tools can generate typed clients in TypeScript, Java, Go, etc.
- **Validation in other languages:** JSON Schema is a standard; any language can validate data against it
- **API testing:** Tools generate test cases from the schema

This is a major reason Pydantic is widely used. You write one model and get validation, serialisation, and documentation automatically.

---

## 21. Pydantic v1 vs v2

Pydantic 2.0 was released in 2023 and introduced breaking changes. If you encounter older code or tutorials, here is what changed.

### Major Changes

| Pydantic v1 | Pydantic v2 |
|------------|-------------|
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `.parse_obj(data)` | `.model_validate(data)` |
| `.parse_raw(json_str)` | `.model_validate_json(json_str)` |
| `class Config:` | `model_config = ConfigDict(...)` |
| `@validator` | `@field_validator` |
| `@root_validator` | `@model_validator` |
| `orm_mode = True` | `from_attributes = True` |
| `validate_assignment` (class Config) | `validate_assignment=True` (ConfigDict) |

### Performance

Pydantic v2's core is written in Rust, making it 5-50x faster than v1 for validation. This matters for high-throughput APIs where Pydantic is on the hot path.

### Migration

If you have v1 code, install both and use the migration tool:

```bash
pip install "pydantic>=2.0"
pip install bump-pydantic
bump-pydantic your_project/
```

This handles most automatic conversions. Complex custom validators might need manual changes.

---

## 22. Common Patterns and Pitfalls

### Pattern: Separate Input and Output Models

For APIs, use separate models for what the client sends and what the server returns:

```python
class UserCreate(BaseModel):
    username: str
    email: str
    password: str    # Client sends plaintext password

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    # No password field -- server never returns it

class UserUpdate(BaseModel):
    email: str | None = None
    bio: str | None = None
    # All optional for partial updates
```

This protects against:
- Leaking passwords in responses
- Clients being able to set internal fields like `id` or `created_at`
- Accepting unwanted fields in updates

### Pitfall: Forgetting the Default for Optional Fields

```python
# This field is required but allows None
class User(BaseModel):
    bio: Optional[str]  # Required!

User()  # Error: bio is required

# This is a truly optional field
class User(BaseModel):
    bio: Optional[str] = None  # Optional

User()  # Works, bio is None
```

### Pattern: Validators That Normalise Data

```python
class User(BaseModel):
    email: str
    phone: str

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v: str) -> str:
        return v.strip().lower() if isinstance(v, str) else v

    @field_validator("phone", mode="before")
    @classmethod
    def normalise_phone(cls, v: str) -> str:
        if isinstance(v, str):
            # Remove all non-digits
            return "".join(c for c in v if c.isdigit())
        return v

user = User(email="  RAHUL@EXAMPLE.COM  ", phone="+91-987-654-3210")
print(user.email)  # "rahul@example.com"
print(user.phone)  # "919876543210"
```

Use `mode="before"` validators to clean data before type checking.

### Pattern: Validating Business Rules

```python
class BankAccount(BaseModel):
    account_type: Literal["savings", "current"]
    balance: float
    credit_limit: float = 0

    @model_validator(mode="after")
    def validate_business_rules(self) -> Self:
        if self.account_type == "savings" and self.credit_limit > 0:
            raise ValueError("Savings accounts cannot have a credit limit")
        if self.balance < -self.credit_limit:
            raise ValueError("Balance cannot exceed credit limit")
        return self
```

Keep data validation separate from domain logic, but use Pydantic for rules that are universal to the data shape.

### Pitfall: Circular References

Pydantic models that reference each other can cause import issues:

```python
# file1.py
from file2 import Post

class User(BaseModel):
    name: str
    posts: list[Post]

# file2.py
from file1 import User  # Circular import!

class Post(BaseModel):
    title: str
    author: User
```

Solutions:
1. **Define them in the same file** (simplest)
2. **Use forward references** with `model_rebuild()`:

```python
# Same file
class User(BaseModel):
    name: str
    posts: list["Post"] = []  # Forward reference as string

class Post(BaseModel):
    title: str
    author: "User"  # Forward reference

# Resolve forward references
User.model_rebuild()
Post.model_rebuild()
```

---

## Exercises

Work through these to solidify your understanding. Solutions are in the next section.

### Exercise 1: Basic Model

Define a `Book` model with:
- `title`: required string, 1-200 characters
- `author`: required string
- `isbn`: required string matching the pattern `^[0-9]{10}$|^[0-9]{13}$` (10 or 13 digit ISBN)
- `pages`: positive integer
- `price`: float, between 0 and 10000
- `in_stock`: boolean, default True

Create one valid instance and demonstrate that invalid values are rejected.

### Exercise 2: Nested Models

Create an `Order` system:
- `Address` model: street, city, state, pincode (6 digits)
- `OrderItem` model: product_name, quantity (>= 1), price (> 0)
- `Order` model: order_id, customer_name, shipping_address (nested Address), items (list of OrderItems, at least one)
- Computed field `total_amount`: sum of (quantity * price) for all items

### Exercise 3: Custom Validators

Create a `JobApplication` model:
- `email`: string
- `phone`: string
- `years_experience`: int (>= 0)
- `expected_salary`: float (> 0)
- `current_salary`: float (>= 0)

Add validators that:
1. Normalise email to lowercase and strip whitespace
2. Extract only digits from phone (remove +, -, spaces)
3. Ensure expected_salary >= current_salary (use a model validator)
4. Ensure years_experience <= 60

### Exercise 4: Input vs Output Models

Design models for a user registration API:
- `UserCreate`: what the client sends (username, email, password, confirm_password)
  - password and confirm_password must match
  - password must be at least 8 characters and contain at least one digit
- `UserResponse`: what the server returns (id, username, email, created_at)
  - No password visible
- `UserUpdate`: for profile updates (all fields optional: email, bio)
  - bio max 500 characters

### Exercise 5: Discriminated Union

Build a `PaymentMethod` system supporting three types:
- `CreditCard`: type, card_number (16 digits), cvv (3 digits), expiry_month, expiry_year
- `UPI`: type, upi_id (must match pattern like `name@provider`)
- `NetBanking`: type, bank_name, account_number (9-18 digits)

Create a `PaymentRequest` model with:
- `amount`: float > 0
- `payment_method`: discriminated union of the three types above

### Exercise 6: Settings Management

Create a `Settings` class that loads from environment variables:
- `database_url`: required string
- `api_key`: required string, min 32 characters
- `debug_mode`: boolean, default False
- `max_workers`: int, default 4, between 1 and 32
- `allowed_origins`: list of strings, default empty list

Also include a nested `EmailConfig`:
- `smtp_host`: string, default "localhost"
- `smtp_port`: int, default 587
- `from_email`: email string, required

### Exercise 7: Generic Model for API Responses

Create a generic `ApiResponse[T]` model with:
- `success`: boolean
- `data`: optional T
- `message`: optional string
- `timestamp`: datetime, default to now
- Computed field `has_data`: True if data is not None

Create a generic `PaginatedResponse[T]` that wraps a list with:
- `items`: list of T
- `page`: int >= 1
- `page_size`: int between 1 and 100
- `total`: int >= 0
- Computed fields: `total_pages`, `has_next`, `has_previous`

Demonstrate usage with a `Product` model.

---

## Solutions

### Solution 1

```python
from pydantic import BaseModel, Field

class Book(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1)
    isbn: str = Field(..., pattern=r"^[0-9]{10}$|^[0-9]{13}$")
    pages: int = Field(..., gt=0)
    price: float = Field(..., gt=0, lt=10000)
    in_stock: bool = True

# Valid book
book = Book(
    title="Clean Code",
    author="Robert C. Martin",
    isbn="0132350882",
    pages=464,
    price=499.0
)
print(book.model_dump())

# Invalid: ISBN wrong length
# Book(title="Test", author="Author", isbn="12345", pages=100, price=100.0)
# ValidationError: isbn: String should match pattern

# Invalid: negative pages
# Book(title="Test", author="Author", isbn="0132350882", pages=-1, price=100.0)
# ValidationError: pages: Input should be greater than 0
```

### Solution 2

```python
from pydantic import BaseModel, Field, computed_field

class Address(BaseModel):
    street: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)
    pincode: str = Field(..., pattern=r"^\d{6}$")

class OrderItem(BaseModel):
    product_name: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
    price: float = Field(..., gt=0)

    @computed_field
    @property
    def subtotal(self) -> float:
        return self.quantity * self.price

class Order(BaseModel):
    order_id: str
    customer_name: str
    shipping_address: Address
    items: list[OrderItem] = Field(..., min_length=1)

    @computed_field
    @property
    def total_amount(self) -> float:
        return sum(item.quantity * item.price for item in self.items)

# Example
order = Order(
    order_id="ORD-001",
    customer_name="Rahul Sharma",
    shipping_address={
        "street": "123 MG Road",
        "city": "Bangalore",
        "state": "Karnataka",
        "pincode": "560001"
    },
    items=[
        {"product_name": "Laptop", "quantity": 1, "price": 50000},
        {"product_name": "Mouse", "quantity": 2, "price": 500}
    ]
)
print(order.total_amount)  # 51000.0
```

### Solution 3

```python
from pydantic import BaseModel, field_validator, model_validator
from typing import Self

class JobApplication(BaseModel):
    email: str
    phone: str
    years_experience: int = Field(..., ge=0, le=60)
    expected_salary: float = Field(..., gt=0)
    current_salary: float = Field(..., ge=0)

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("phone", mode="before")
    @classmethod
    def extract_digits(cls, v):
        if isinstance(v, str):
            return "".join(c for c in v if c.isdigit())
        return v

    @model_validator(mode="after")
    def validate_salaries(self) -> Self:
        if self.expected_salary < self.current_salary:
            raise ValueError("Expected salary must be at least current salary")
        return self

# Valid
app = JobApplication(
    email="  RAHUL@EXAMPLE.COM  ",
    phone="+91-987-654-3210",
    years_experience=5,
    expected_salary=1500000,
    current_salary=1200000
)
print(app.email)  # "rahul@example.com"
print(app.phone)  # "919876543210"
```

### Solution 4

```python
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Self

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8)
    confirm_password: str

    @field_validator("password")
    @classmethod
    def password_has_digit(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

class UserUpdate(BaseModel):
    email: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)

# Valid registration
user = UserCreate(
    username="rahul_dev",
    email="rahul@example.com",
    password="secure1234",
    confirm_password="secure1234"
)

# Invalid: passwords don't match
# UserCreate(username="test", email="a@b.com", password="abc12345", confirm_password="different123")
```

### Solution 5

```python
from typing import Literal, Union
from pydantic import BaseModel, Field

class CreditCard(BaseModel):
    type: Literal["credit_card"]
    card_number: str = Field(..., pattern=r"^\d{16}$")
    cvv: str = Field(..., pattern=r"^\d{3}$")
    expiry_month: int = Field(..., ge=1, le=12)
    expiry_year: int = Field(..., ge=2024, le=2100)

class UPI(BaseModel):
    type: Literal["upi"]
    upi_id: str = Field(..., pattern=r"^[\w.-]+@[\w.-]+$")

class NetBanking(BaseModel):
    type: Literal["net_banking"]
    bank_name: str
    account_number: str = Field(..., pattern=r"^\d{9,18}$")

class PaymentRequest(BaseModel):
    amount: float = Field(..., gt=0)
    payment_method: Union[CreditCard, UPI, NetBanking] = Field(
        ..., discriminator="type"
    )

# Credit card payment
p1 = PaymentRequest(
    amount=1500.0,
    payment_method={
        "type": "credit_card",
        "card_number": "1234567812345678",
        "cvv": "123",
        "expiry_month": 12,
        "expiry_year": 2026
    }
)

# UPI payment
p2 = PaymentRequest(
    amount=500.0,
    payment_method={"type": "upi", "upi_id": "rahul@paytm"}
)

# Net banking
p3 = PaymentRequest(
    amount=10000.0,
    payment_method={
        "type": "net_banking",
        "bank_name": "HDFC Bank",
        "account_number": "12345678901"
    }
)
```

### Solution 6

```python
from pydantic import BaseModel, Field, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class EmailConfig(BaseModel):
    smtp_host: str = "localhost"
    smtp_port: int = 587
    from_email: EmailStr

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore"
    )
    
    database_url: str
    api_key: str = Field(..., min_length=32)
    debug_mode: bool = False
    max_workers: int = Field(4, ge=1, le=32)
    allowed_origins: list[str] = []
    email: EmailConfig

# .env file:
# DATABASE_URL=postgresql://localhost/mydb
# API_KEY=your-very-long-secret-api-key-here-32chars
# DEBUG_MODE=true
# MAX_WORKERS=8
# ALLOWED_ORIGINS=["http://localhost:3000","https://myapp.com"]
# EMAIL__SMTP_HOST=smtp.gmail.com
# EMAIL__SMTP_PORT=465
# EMAIL__FROM_EMAIL=noreply@example.com

# Usage
# settings = Settings()
# print(settings.database_url)
# print(settings.email.smtp_host)
```

### Solution 7

```python
from datetime import datetime
from typing import TypeVar, Generic, Optional
from pydantic import BaseModel, Field, computed_field

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    @computed_field
    @property
    def has_data(self) -> bool:
        return self.data is not None

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total: int = Field(..., ge=0)

    @computed_field
    @property
    def total_pages(self) -> int:
        if self.total == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size

    @computed_field
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @computed_field
    @property
    def has_previous(self) -> bool:
        return self.page > 1

# Demo
class Product(BaseModel):
    id: int
    name: str
    price: float

# Single product response
response1: ApiResponse[Product] = ApiResponse(
    success=True,
    data={"id": 1, "name": "Samosa", "price": 15.0}
)
print(response1.has_data)  # True

# Empty response
response2: ApiResponse[Product] = ApiResponse(success=False, message="Not found")
print(response2.has_data)  # False

# Paginated list
products_page: PaginatedResponse[Product] = PaginatedResponse(
    items=[
        {"id": 1, "name": "Samosa", "price": 15.0},
        {"id": 2, "name": "Chai", "price": 10.0}
    ],
    page=1,
    page_size=10,
    total=25
)
print(products_page.total_pages)   # 3
print(products_page.has_next)       # True
print(products_page.has_previous)   # False

# Wrap the paginated response in the API response
wrapped: ApiResponse[PaginatedResponse[Product]] = ApiResponse(
    success=True,
    data=products_page
)
```

---

## Final Thoughts

Pydantic is deceptively simple on the surface and remarkably powerful underneath. Most developers learn just enough to use it with FastAPI and miss features that would save them significant time: computed fields, discriminated unions, generics, settings management, and custom validators.

### Pydantic Beyond FastAPI

The patterns you learned here apply far beyond FastAPI:

- **Data validation in ETL pipelines:** When you read data from CSVs, APIs, or databases, Pydantic validates and cleans it before it enters your system
- **Configuration management:** Pydantic Settings replaces scattered `os.getenv()` calls with a typed, validated configuration object
- **Input validation for CLI tools:** Validate command-line arguments and config files with clear error messages
- **Message validation in microservices:** When services communicate via queues (RabbitMQ, Kafka), Pydantic ensures messages conform to the expected schema
- **Testing fixtures with type safety:** Create test data with guaranteed structure

### Pydantic in the World of AI and Agents

One of the most important emerging use cases for Pydantic is in AI applications, particularly with LLM agents.

When you ask an LLM to generate structured data (not just free text), you need a way to define the expected structure and validate the output. LLMs are probabilistic -- they do not always return exactly what you ask for. Pydantic solves this.

**Structured output from LLMs:**

Imagine you ask an LLM to extract information from a blog post:

```python
class BlogAnalysis(BaseModel):
    """The structure we expect the LLM to return."""
    tags: list[str] = Field(..., min_length=1, max_length=10)
    summary: str = Field(..., max_length=200)
    sentiment: Literal["positive", "negative", "neutral"]
    reading_time_minutes: int = Field(..., ge=1, le=60)
```

You send this schema to the LLM (via function calling or structured output), and the LLM returns JSON that matches it. Pydantic validates the response. If the LLM returns something unexpected (like `reading_time_minutes: -5` or `sentiment: "kinda good"`), Pydantic catches it immediately.

**AI agent tool definitions:**

AI agents (like those built with LangChain, CrewAI, or custom frameworks) use tools -- functions that the agent can call to interact with the real world. Each tool needs a clear definition of what inputs it accepts:

```python
class SearchTicketsInput(BaseModel):
    """Input schema for the ticket search tool."""
    query: str = Field(..., description="Search query for finding tickets")
    status: Literal["open", "closed", "all"] = "all"
    assigned_to: str | None = None
    max_results: int = Field(10, ge=1, le=50)

class SendEmailInput(BaseModel):
    """Input schema for the email sending tool."""
    to: EmailStr
    subject: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    priority: Literal["low", "normal", "high"] = "normal"
```

The agent reads these Pydantic schemas to understand what parameters each tool accepts, what types they are, and what constraints they have. When the agent decides to call a tool, the input is validated through Pydantic before the tool executes. This prevents the agent from passing invalid data to real-world systems.

**Why this matters:**

Without Pydantic, every tool would need manual validation of the agent's input. With agents making dozens of tool calls in a single run, invalid inputs would cause crashes deep in the workflow. Pydantic catches these at the boundary, before any real action is taken.

This pattern (define expected structure as a Pydantic model, validate all inputs and outputs) is becoming the standard in the AI ecosystem. Libraries like LangChain, Instructor, Marvin, and Anthropic's own SDK all use Pydantic models for tool definitions and structured output.

If you master Pydantic, a lot of boilerplate code in your Python projects disappears. You write declarative models instead of procedural validation. You get type safety, clear error messages, and automatic documentation. And because Pydantic v2 is implemented in Rust, it is fast enough for production workloads at any scale.

---

*This is a Codeverra course. Learn more at codeverra.com*
