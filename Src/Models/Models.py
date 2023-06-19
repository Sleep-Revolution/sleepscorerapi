import datetime
from sqlalchemy import Column, Integer, String, LargeBinary, ForeignKey, Boolean, DateTime
from pydantic import BaseModel
from sqlalchemy.orm import relationship
from Src.Models.Database import Base

class Centre(Base):
    __tablename__ = "Centres"
    Id = Column(Integer, primary_key=True, index=True)
    CentreName = Column(String, unique=True, index=True)
    ResponsibleEmail = Column(String, unique=True, index=True)
    FolderLocation = Column(String, unique=True, index=True)
    IsAdministrator = Column(Boolean)
    PasswordHash = Column(LargeBinary)
    PasswordSalt = Column(LargeBinary)

    CentreUploads = relationship("CentreUpload", back_populates="Centre")


class CentreUpload(Base):
    __tablename__ = "CentreUploads"
    Id = Column(Integer, primary_key=True, index=True)
    RecordingNumber = Column(Integer)
    CentreId = Column(Integer, ForeignKey("Centres.Id"))
    Timestamp = Column(DateTime, default=datetime.datetime.now())
    Location = Column(String, unique=True)
    Centre = relationship("Centre", back_populates="CentreUploads")
    Nights = relationship("Night", back_populates="Upload")
    ESR = ""#f"{CentreId}{RecordingNumber}"

class Night(Base):
    __tablename__ = "Nights"
    Id = Column(Integer, primary_key=True, index=True)
    UploadId = Column(Integer, ForeignKey("CentreUploads.Id"))
    NightNumber = Column(Integer)
    Location = Column(String)
    IsFaulty = Column(Boolean)
    Upload = relationship("CentreUpload", back_populates="")


class CentreCreate(BaseModel):
    CentreName: str
    ResponsibleEmail: str
    Password: str
class AuthCredentials(BaseModel):
    Email: str
    Password: str
