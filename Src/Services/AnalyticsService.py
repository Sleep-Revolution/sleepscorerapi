from sqlalchemy.orm import Session
from Src.Models.Models import Centre, CentreCreate, AuthCredentials, LogDataEntry, LogEntity
import bcrypt
from Src.Repositories.AnalyticsRepository import AnalyticsRepository 
from Src.Infrastructure.JWT import CreateAccessToken

class AnalyticsService:
    def __init__(self, analyticsRepo=None):
        if analyticsRepo:
            self.AnalyticsRepository = analyticsRepo
        else:
            self.AnalyticsRepository = AnalyticsRepository()

    # def GetAllLogs(self):
    #     return self.AnalyticsRepository.GetAllCentres()

    def AddLog(self, log:LogEntity):
        l = log.ToEntry()
        return self.AnalyticsRepository.AddLog(l)

    