import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.exc import IntegrityError

from database import SessionLocal, engine
from models import Base, Contact

fake = Faker()

def seed_database():
    Base.metadata.create_all(engine)

    with SessionLocal() as session:
        # Create sample contacts
        contacts = []
        for _ in range(20):
            contact = Contact(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.unique.email(),
                phone=fake.phone_number(),
                birthday=fake.date_of_birth(minimum_age=18, maximum_age=80),
                additional_data=fake.text(max_nb_chars=100) if random.choice([True, False]) else None
            )
            contacts.append(contact)

        session.add_all(contacts)
        try:
            session.commit()
            print("Database seeded successfully with sample contacts.")
        except IntegrityError:
            session.rollback()
            print("Seed data contained duplicates. Please rerun seed.py if necessary.")
        else:
            print(f"Created {len(contacts)} sample contacts.")

if __name__ == "__main__":
    seed_database()