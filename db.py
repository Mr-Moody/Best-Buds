from sqlalchemy import create_engine, Column, Integer, ForeignKey, Integer, Date, Float, String
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import date

# Define Database URL (Change it based on your DB)
DATABASE_URL = "sqlite:///database.db"  # SQLite
# DATABASE_URL = "mysql+pymysql://user:password@localhost/mydb"
# DATABASE_URL = "postgresql://user:password@localhost/mydb"

# Create Engine
engine = create_engine(DATABASE_URL, echo=True)

# Create a Base class
Base = declarative_base()

#user table model
class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class Plant(Base):
    __tablename__ = "plant"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    species = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    height = relationship("Height", nullable=False)
    water_freq = Column(String, nullable=False)
    fertiliser = Column(String, nullable=False)
    fertiliser_type = Column(String, nullable=False)
    fertiliser_freq = Column(String, nullable=False)

class Height(Base):
    __tablename__ = "height"

    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey("plant.id"))  #foreign key linking to Plant
    date_recorded = Column(Date, nullable=False)
    height_value = Column(Float, nullable=False)  #height value in cm
    
    # Define the relationship back to Plant
    plant = relationship("Plant", back_populates = "heights")

class Plant():
    def __init__(self):
        self.name = None
        self.species = None
        self.birthday = None
        self.height = None
        self.water_freq = None

        self.fertiliser = None
        self.fert_type = None
        self.fert_freq = None


#make tables
Base.metadata.create_all(engine)

local_session = sessionmaker(bind=engine)
session = local_session()

# Add Data
new_user = User(name="Alice", age=25)
session.add(new_user)
session.commit()

# Query Data
users = session.query(User).all()
for user in users:
    print(user.name, user.age)

# Close the session
session.close()
