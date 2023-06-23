from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from Src.Models.Models import Centre
from sqlalchemy.pool import QueuePool

class AuthenticationRepository:
    def __init__(self, session=None):
        if not session:
            # self.engine = create_engine(os.environ['SLEEPSCORER_DB_URL'])
            self.engine = create_engine(
                os.environ['SLEEPSCORER_DB_URL'],
                poolclass=QueuePool,
                pool_size=10,  # Set an appropriate pool size for your application
                max_overflow=20,# Set the maximum number of connections allowed to overflow
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


    def GetCentreById(self, centreId: int) -> Centre:
        with self.Session() as session:
            return session.query(Centre).filter(Centre.Id == centreId).first()


    def CreateCentre(self, centre: Centre):
        with self.Session() as session:
            session.add(centre)
            session.commit()
            session.refresh(centre)
            return centre