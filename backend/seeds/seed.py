from sqlmodel import Session

from app.db import engine, init_db


def main() -> None:
    init_db()
    with Session(engine):
        print("Database initialized. Seed loader implementation follows data-model milestone.")


if __name__ == "__main__":
    main()

