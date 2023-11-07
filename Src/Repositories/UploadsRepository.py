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

    def GetNightById(self, nightId : int):
        with self.Session() as session:
            night = session.query(Night).filter(Night.Id == nightId).first()
            if night:
                night.Logs
                night.Upload
                night.Upload.Centre
            return night

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
            for upload in uploads:
                upload.Logs
                
            return uploads

    def GetAllCentres(self):
        with self.Session() as session:
            centres = session.query(Centre).all()
            for centre in centres:
                centre.CentreUploads
                for upload in centre.CentreUploads:
                    upload.Nights
                    upload.Logs

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
            cu = session.query(CentreUpload).filter(CentreUpload.Id == uploadId).first()
            if not cu:
                return None
            cu.Nights
            cu.Centre
            cu.Logs
            for night in cu.Nights:
                night.Logs
                night.RecordingIdentifier = f'{cu.Centre.Prefix}{str(cu.Centre.MemberNumber).zfill(2)}-{str(cu.RecordingNumber).zfill(3)}-{str(night.NightNumber).zfill(2)}'
            cu.RecordingIdentifier = f'{cu.Centre.Prefix}{str(cu.Centre.MemberNumber).zfill(2)}-{str(cu.RecordingNumber).zfill(3)}'
            return cu
    
    def GetNightsForUpload(self, uploadId):
        with self.Session() as session:
            nights = session.query(Night).filter(Night.UploadId == uploadId).all()
            for night in nights:
                night.Logs
                night.Upload
                night.Upload.Centre
            return nights