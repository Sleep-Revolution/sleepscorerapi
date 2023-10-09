from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
import os
from Src.Models.Models import NightLogDataEntry

import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

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


    # def GetAllLogsForCentre(self, centreId):
    #     with self.Session() as session:
    #         return session.query(LogDataEntry).filter(LogDataEntry.CentreId == centreId).all()

    # def GetAllLogsForFile(self, filename, datasetName):
    #     with self.Session() as session:
    #         return session.query(LogDataEntry).filter(LogDataEntry.FileName == filename, LogDataEntry.DatasetName == datasetName).all()

    # def GetLastLogForFile(self, filename, datasetName) -> LogDataEntry:
    #     with self.Session() as session:
    #         return session.query(LogDataEntry).filter(LogDataEntry.FileName == filename, LogDataEntry.DatasetName == datasetName).order_by(LogDataEntry.Id.desc()).first()
                            

    # def GetAllLogsForUploadedRecording(self, ESR):
    #     with self.Session() as session:
    #         return session.query(LogDataEntry).filter(LogDataEntry.FileName == ESR).order_by(LogDataEntry.Id.desc()).all()

    

    def GetAllLogsForNight(self, nightId):
        with self.Session() as session:
            return session.query(NightLogDataEntry).filter(NightLogDataEntry.NightId == nightId).all()

    def AddLogToNight(self, log: NightLogDataEntry):
        print(log.__dict__)

        with self.Session() as session:
            session.add(log)
            session.commit()
            session.refresh(log)
            return log
    
    