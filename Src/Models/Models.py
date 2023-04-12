from sqlalchemy import Column, Integer, String, LargeBinary, ForeignKey, Boolean
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
    CentreId = Column(Integer, ForeignKey("Centres.Id"))
    Centre = relationship("Centre", back_populates="CentreUploads")

class CentreCreate(BaseModel):
    CentreName: str
    ResponsibleEmail: str
    Password: str
class AuthCredentials(BaseModel):
    Email: str
    Password: str
