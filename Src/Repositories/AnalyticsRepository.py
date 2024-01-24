from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
import os
from Src.Models.Models import NightLogDataEntry, UploadLogDataEntry

    
class AnalyticsRepository:
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


    def GetAllLogsForNight(self, nightId):
        with self.Session() as session:
            return session.query(NightLogDataEntry).filter(NightLogDataEntry.NightId == nightId).all()
        
    def GetAllLogsForUpload(self, uploadId):
        with self.Session() as session:
            return session.query(UploadLogDataEntry).filter(UploadLogDataEntry.UploadId == uploadId).all()


    def AddLogToNight(self, log: NightLogDataEntry):
        with self.Session() as session:
            session.add(log)
            session.commit()
            session.refresh(log)
            return log
    
    def AddLogToUpload(self, log: UploadLogDataEntry):
        print(log.__dict__)

        with self.Session() as session:
            session.add(log)
            session.commit()
            session.refresh(log)
            return log
        
    def DeleteNightLog(self, log: NightLogDataEntry):
        with self.Session() as session:
            session.query(NightLogDataEntry).filter(NightLogDataEntry.Id == log.Id).delete()
            session.commit()

    def DeleteUploadLog(self, log: UploadLogDataEntry):
        with self.Session() as session:
            session.query(UploadLogDataEntry).filter(UploadLogDataEntry.Id == log.Id).delete()
            session.commit()
    