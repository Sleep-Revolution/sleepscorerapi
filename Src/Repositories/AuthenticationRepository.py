from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from Src.Models.Models import Centre
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import func

class AuthenticationRepository:
    def __init__(self, session=None):
        if not session:
            # self.engine = create_engine(os.environ['SLEEPSCORER_DB_URL'])
            self.engine = create_engine(
                os.environ['SLEEPSCORER_DB_URL'], poolclass=QueuePool,
                pool_size=10, max_overflow=20,
                pool_recycle=3600
            )
            self.Session = sessionmaker(bind=self.engine)
        else:
            self.Session = session

    def GetAllCentres(self):
        with self.Session() as session:
            return  session.query(Centre).all()

    def GetCentreByName(self, CentreName: str) -> Centre:
        with self.Session() as session:
            return session.query(Centre).filter(Centre.CentreName == CentreName).first()

    def GetCentreByEmail(self, responsibleEmail: str) -> Centre:
        with self.Session() as session:
            return session.query(Centre).filter(Centre.ResponsibleEmail == responsibleEmail).first()

    def GetCentreByPrefixAndMN(self, prefix, memberNumber):
        with self.Session() as session:
            return session.query(Centre).filter(Centre.Prefix == prefix, Centre.MemberNumber == memberNumber).first()

    def GetCentreById(self, centreId: int) -> Centre:
        with self.Session() as session:
            return session.query(Centre).filter(Centre.Id == centreId).first()

    def SetCentrePassword(self, centreId: int, passwordSalt, passwordHash):
        with self.Session() as session:
            centre = session.query(Centre).filter(Centre.Id == centreId).first()
            if centre:
                centre.PasswordSalt = passwordSalt
                centre.PasswordHash = passwordHash
                session.commit()
            else:
                raise ValueError("Centre not found with the provided ID")
        
    def SetLogin(self, centreId: int):
        with self.Session() as session:
            centre = session.query(Centre).filter(Centre.Id == centreId).first()
            if centre:
                centre.LastLogin = func.now()
                session.commit()
            else:
                raise ValueError("Centre not found with the provided ID")

    def CreateCentre(self, centre: Centre):
        with self.Session() as session:
            session.add(centre)
            session.commit()
            session.refresh(centre)
            return centre

    def UpdateCentre(self, centreId, newCentreName, newCentrePrefix, newCentreMemberNumber, newCentreResponsibleMail, newCentreDescription):
        with self.Session() as session:
            centre = session.query(Centre).filter(Centre.Id == centreId).first()
            if centre:
                centre.CentreName = newCentreName
                centre.Prefix = newCentrePrefix
                centre.MemberNumber = newCentreMemberNumber
                centre.ResponsibleEmail = newCentreResponsibleMail
                centre.Description = newCentreDescription
                session.commit()
            else:
                raise ValueError("Centre not found with the provided ID")
