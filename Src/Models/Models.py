import datetime
from sqlalchemy import Column, Integer, String, LargeBinary, ForeignKey, Boolean, DateTime, Float
from pydantic import BaseModel
from sqlalchemy.orm import relationship
from Src.Models.Database import Base
from sqlalchemy.sql import func

class Centre(Base):
    __tablename__ = "Centres"
    Id = Column(Integer, primary_key=True, index=True)
    CentreName = Column(String, unique=True, index=True)
    Description = Column(String, unique=False, index=False)
    ResponsibleEmail = Column(String, unique=True, index=True)
    Prefix = Column(String)
    MemberNumber = Column(Integer)
    FolderLocation = Column(String, unique=True, index=True)
    IsAdministrator = Column(Boolean)
    PasswordHash = Column(LargeBinary)
    PasswordSalt = Column(LargeBinary)
    LastLogin = Column(DateTime(timezone=True))
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



# class Dataset(Base):
#     __tablename__ = "Datasets"
#     Id = Column(Integer, primary_key=True, index=True)
#     Id = Column(String)

class CentreCreate(BaseModel):
    CentreName: str
    Description: str
    ResponsibleEmail: str
    Password: str
    

class AuthCredentials(BaseModel):
    Email: str
    Password: str

class LogEntity(BaseModel):
    CentreId: int
    FileName: str
    StepNumber: int
    TaskTitle: str
    Progress: int
    Message: str
    DatasetName: str

    def ToEntry(self):
        d = LogDataEntry()
        d.CentreId=self.CentreId
        d.Message=self.Message
        d.Progress=self.Progress
        d.TaskTitle=self.TaskTitle
        d.StepNumber=self.StepNumber
        d.FileName=self.FileName
        d.DatasetName=self.DatasetName
        return d

#
class LogDataEntry(Base):
    __tablename__ = 'Logs'
    
    Id = Column(Integer, primary_key=True)
    FileName = Column(String)
    Timestamp = Column(DateTime, default=func.now())
    StepNumber = Column(Integer)
    TaskTitle = Column(String)
    Progress = Column(Integer)
    Message = Column(String)
    DatasetName = Column(String)
    CentreId = Column(Integer)