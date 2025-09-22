from sqlalchemy import create_engine
from .models import Base


def main():
    engine = create_engine("sqlite:///mi_base.db", echo=True)
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    main()