from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from Src.Models.Models import CentreUpload, Centre, Nights


class UploadRepository:
    def __init__(self, session=None):
        if not session:
            self.engine = create_engine(os.environ['SLEEPSCORER_DB_URL'])
            self.Session = sessionmaker(bind=self.engine)
        else:
            self.Session = session

    def CreateNewUpload(self, newCentreUpload: CentreUpload):
        with self.Session() as session:
            session.add(newCentreUpload)
            session.commit()
            session.refresh(newCentreUpload)
            return newCentreUpload
    
    def GetAllUploadsForCentre(self, centreId):
        with self.Session() as session:
            return session.query(CentreUpload).filter(CentreUpload.CentreId == centreId).all()

    def GetAllCentres(self):
        with self.Session() as session:
            centres = session.query(Centre).all()
            for centre in centres:
                centre.CentreUploads

            return centres

    def GetNightsForUpload(self, uploadId):
        with self.Session() as session:
            return session.query(Nights).filter(Nights.registry == uploadId).all()


    def DeleteUpload(self, uploadId):
        with self.Session() as session:
            centre = session.query(CentreUpload).filter(CentreUpload.Id == uploadId).one()
            session.delete(centre)
            session.commit()

    def GetUploadById(self, uploadId) -> CentreUpload:
        with self.Session() as session:
            return session.query(CentreUpload).filter(CentreUpload.Id == uploadId).one()