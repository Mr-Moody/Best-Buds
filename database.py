from sqlalchemy import create_engine, Column, Integer, ForeignKey, Integer, Date, Float, String, Boolean
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, date

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
    fertiliser_needed = Column(Boolean, nullable=False)
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
        self.session = local_session()

    def __del__(self):
        self.session.close()

    def get_user_plants(self) -> list[Plant]:
        all_plants = self.session.query(Plant).all()

        return all_plants
    
    def new_plant_record(self, name:str=None, species:str=None, birth_date:date=None, height:float=None, water_frequency:int=None, fertiliser_needed:bool=None, fertiliser_type:str=None, fertiliser_frequency=None) -> None:
        new_plant = Plant(name=name, species=species, birth_date=birth_date, water_frequency=water_frequency, fertiliser_needed=fertiliser_needed, fertiliser_type=fertiliser_type, fertiliser_frequency=fertiliser_frequency)
        
        self.session.add(new_plant)
        self.session.commit()

        new_height = Height(plant_id=new_plant.id, date_recorded=datetime.today(), height_value=height)

        self.session.add(new_height)
        self.session.commit

Base.metadata.create_all(engine)

local_session = sessionmaker(bind=engine)
session = local_session()

# if __name__ == "__main__":
    # new_plant = Plant(name="Red Rose", species="Roses", birth_date=datetime.date(2024, 2, 28), water_frequency=2, fertiliser_needed=False)

    # session.add(new_plant)

    # session.commit()

    # height1 = Height(plant_id=new_plant.id, date_recorded=date(2024, 3, 1), height_value=140)
    # height2 = Height(plant_id=new_plant.id, date_recorded=date(2024, 3, 2), height_value=170)

    # session.add_all([height1, height2])

    # session.commit()

session.close()