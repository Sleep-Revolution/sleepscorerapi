from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from Src.Models.Models import Centre


class AuthenticationRepository:
    def __init__(self, session=None):
        if not session:
            self.engine = create_engine(os.environ['SLEEPSCORER_DB_URL'])
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


    def GetCentreById(self, centreId: int):
        with self.Session() as session:
            return session.query(Centre).filter(Centre.Id == centreId).first()


    def CreateCentre(self, centre: Centre):
        with self.Session() as session:
            session.add(centre)
            session.commit()
            session.refresh(centre)
            return centre