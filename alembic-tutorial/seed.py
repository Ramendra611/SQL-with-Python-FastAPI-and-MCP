from models import engine, Base, SessionLocal, Student, Teacher

Base.metadata.create_all(engine)

session = SessionLocal()

students = [
    Student(name="Rahul Sharma", roll_number="GF2024001",
            standard=10, section="A"),
    Student(name="Priya Reddy", roll_number="GF2024002",
            standard=10, section="A"),
    Student(name="Arjun Nair", roll_number="GF2024003",
            standard=10, section="B"),
    Student(name="Ananya Iyer", roll_number="GF2024004",
            standard=9, section="A"),
    Student(name="Vikram Singh", roll_number="GF2024005",
            standard=9, section="B"),
]

teachers = [
    Teacher(name="Mrs. Lakshmi Menon", subject="Mathematics",
            phone="9876543210"),
    Teacher(name="Mr. Rajesh Kumar", subject="Science",
            phone="9876543211"),
    Teacher(name="Ms. Fatima Sheikh", subject="English",
            phone="9876543212"),
]


session.add_all(students + teachers)
session.commit()
session.close()
