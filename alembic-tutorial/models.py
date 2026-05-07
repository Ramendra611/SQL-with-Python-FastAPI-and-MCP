from sqlalchemy import (
    create_engine, Column, Integer, String, Float, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker

# DATABASE_URL = "sqlite:///school.db"
# DATABASE_URL =  "postgresql://neondb_owner:npg_haHZP4CLmb0l@ep-steep-mountain-amo3hk3t.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"

DATABASE_URL = "mysql+pymysql://root:SdryjoPGOuxENhXAAPLrFTgQiyuyQMOw@trolley.proxy.rlwy.net:36820/railway"
 
engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class Student(Base):
    """A student enrolled in the school."""
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    roll_number = Column(String(50), nullable=False, unique=True)
    standard = Column(Integer, nullable=False)     # Class/grade (1-12)
    section = Column(String(50), nullable=False)        # A, B, C, etc.
    email = Column(String(50), unique = True)


class Teacher(Base):
    """A teacher at the school."""
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    subject = Column(String(50), nullable=False)
    phone = Column(String(50), nullable=False, unique=True)
    email = Column(String(50), unique=True)


class Subject(Base):
    """A subject taught at the school."""
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Mathematics, Science, etc.
    name = Column(String(50), nullable=False)
    # Which class this applies to
    standard = Column(Integer, nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))  # Who teaches it
