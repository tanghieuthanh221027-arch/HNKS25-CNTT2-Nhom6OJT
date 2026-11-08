from db.database import Base 

from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Enum as SQLEnum
from sqlalchemy.orm import relationship

class Role(str , Enum):
    ADMIN = "ADMIN"
    STAFF = "STAFF"
    CASHIER = "CASHIER"
    TRAINER = "TRAINER"
    MEMBER = "MEMBER"

class Status(str , Enum):
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"

class User(Base):
    id = Column(Integer , primary_key= True , index= True)
    full_name = Column(String(150) , nullable= False)
    email = Column(String(255) , unique= True , )