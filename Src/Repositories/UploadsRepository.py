from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
import os
from Src.Models.Models import CentreUpload, Centre, Night

class UploadRepository:
    def __init__(self, session=None):
        if not session:
            # self.engine = create_engine(os.environ['SLEEPSCORER_DB_URL'])
            # self.Session = sessionmaker(bind=self.engine)
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

    def CreateNewUpload(self, newCentreUpload: CentreUpload):
        with self.Session() as session:
            session.add(newCentreUpload)
            session.commit()
            session.refresh(newCentreUpload)
            return newCentreUpload
    
    def AddNightToUpload(self, newNight: Night):
        with self.Session() as session:
            session.add(newNight)
            session.commit()
            session.refresh(newNight)
            return newNight

    def GetAllUploadsForCentre(self, centreId):
        with self.Session() as session:
            uploads = session.query(CentreUpload).filter(CentreUpload.CentreId == centreId).all()
            return uploads

    def GetAllCentres(self):
        with self.Session() as session:
            centres = session.query(Centre).all()
            for centre in centres:
                centre.CentreUploads

            return centres

    def GetNightsForUpload(self, uploadId):
        with self.Session() as session:
            return session.query(Night).filter(Night.UploadId == uploadId).all()


    def DeleteUpload(self, uploadId):
        with self.Session() as session:
            centre = session.query(CentreUpload).filter(CentreUpload.Id == uploadId).one()
            session.delete(centre)
            session.commit()

    def GetUploadById(self, uploadId) -> CentreUpload:
        with self.Session() as session:
            cu = session.query(CentreUpload).filter(CentreUpload.Id == uploadId).one()
            cu.Nights
            cu.Centre
            cu.ESR = f'{cu.Centre.Prefix}{str(cu.Centre.MemberNumber).zfill(2)}{str(cu.RecordingNumber).zfill(2)}'
            return cu