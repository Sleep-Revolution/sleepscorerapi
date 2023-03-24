from sqlalchemy import Column, Integer, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from Src.Models.Database import Base

class Centre(Base):
    __tablename__ = "Centres"
    Id = Column(Integer, primary_key=True, index=True)
    CentreName = Column(String, unique=True, index=True)
    ResponsibleEmail = Column(String, unique=True, index=True)
    PasswordHash = Column(LargeBinary)
    PasswordSalt = Column(LargeBinary)
    
class CentreCreate(BaseModel):
    CentreName: str
    ResponsibleEmail: str
    Password: str
class AuthCredentials(BaseModel):
    CentreName: str
    Password: str

class RecordingRequest(BaseModel):
    s: str