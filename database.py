from sqlalchemy import create_engine, Column, Integer, ForeignKey, Integer, Date, Float, String
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import date

# Define Database URL (Change it based on your DB)
DATABASE_URL = "sqlite:///database.db"  # SQLite
# DATABASE_URL = "mysql+pymysql://user:password@localhost/mydb"
# DATABASE_URL = "postgresql://user:password@localhost/mydb"

engine = create_engine(DATABASE_URL, echo=True)

Base = declarative_base()

class Plant(Base):
    __tablename__ = "plant"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    species = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    height = relationship("Height", back_populates="plant")
    water_frequency = Column(Integer, nullable=False)
    fertiliser = Column(String, nullable=True)
    fertiliser_type = Column(String, nullable=True)
    fertiliser_frequency = Column(Integer, nullable=True)

class Height(Base):
    __tablename__ = "height"

    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey("plant.id"))  #foreign key linking to Plant
    date_recorded = Column(Date, nullable=False)
    height_value = Column(Float, nullable=False)  #height value in cm
    
    # Define the relationship back to Plant
    plant = relationship("Plant", back_populates="height")

class DB():
    def __init__(self):
        pass

    def get_user_plants(self) -> list[Plant]:
        all_plants = session.query(Plant).all()

        return all_plants


Base.metadata.create_all(engine)

local_session = sessionmaker(bind=engine)
session = local_session()

if __name__ == "__main__":
    new_plant = Plant(name="Nathan", species="Cactus", birth_date=date(2024, 2, 1), water_frequency=365)

    session.add(new_plant)

    session.commit()

    height1 = Height(plant_id=new_plant.id, date_recorded=date(2024, 3, 1), height_value=162)
    height2 = Height(plant_id=new_plant.id, date_recorded=date(2024, 3, 2), height_value=170)

    session.add_all([height1, height2])

    session.commit()

session.close()