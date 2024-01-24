import json
from sqlalchemy.orm import Session
from Src.Models.Models import Centre, CentreCreate, AuthCredentials, NightLogDataEntry, NightLogEntity, UploadLogDataEntry, UploadLogEntity
import bcrypt
from Src.Repositories.AnalyticsRepository import AnalyticsRepository 
from Src.Infrastructure.JWT import CreateAccessToken
import requests
from requests.auth import HTTPBasicAuth
import os 
from typing import List

class JobLogEntry():
    TaskTitle:str
    TaskDuration: float
    TaskNumber: int
    Success:bool 

class AnalyticsService:
    def __init__(self, analyticsRepo=None):
        if analyticsRepo:
            self.AnalyticsRepository = analyticsRepo
        else:
            self.AnalyticsRepository = AnalyticsRepository()

    # def GetAllLogs(self):
    #     return self.AnalyticsRepository.GetAllCentres()

    def AddLogToNight(self, log:NightLogDataEntry):
        l = log.ToEntry()
        return self.AnalyticsRepository.AddLogToNight(l)

    def AddLogToUpload(self, log:UploadLogEntity):
        l = log.ToEntry()
        return self.AnalyticsRepository.AddLogToUpload(l)

    def CheckIfJobExistsForUpload(self, uploadId):
        jobs = self.GetJobsForUploadsInQueue()
        return any(job.get("uploadId") == uploadId for job in jobs)

    def CheckIfJobExistsForNight(self, nightId, jobs = None):
        if jobs is None:
            jobs = self.GetJobsForNightsInQueue()
        return any(job.get("nightId") == nightId for job in jobs)

    def GetJobsForUploadsInQueue(self):
        get_messages_url = f"http://130.208.209.2:15672/api/queues/%2f/{ os.environ['SPLITTER_QUEUE_NAME'] }/get"
        data = {
            "count": -1,
            "ackmode": "ack_requeue_true",
            "encoding": "auto"
        }
        response = requests.post(get_messages_url, headers={"content-type": "application/json"},
                                data=json.dumps(data), auth=HTTPBasicAuth("server", "server"))

        if response.status_code != 200:
            return []

        messages = response.json()

        jobs = []
        for msg in messages:
            payload = msg.get("payload")
            if payload:
                body = json.loads(payload)
                jobs.append(body)
        return jobs

    def GetJobsForNightsInQueue(self):
        get_messages_url = f"http://130.208.209.2:15672/api/queues/%2f/{ os.environ['TASK_QUEUE_NAME'] }/get"
        data = {
            "count": -1,
            "ackmode": "ack_requeue_true",
            "encoding": "auto"
        }
        response = requests.post(get_messages_url, headers={"content-type": "application/json"},
                                data=json.dumps(data), auth=HTTPBasicAuth("server", "server"))

        if response.status_code != 200:
            return []

        messages = response.json()
        jobs = []
        for msg in messages:
            payload = msg.get("payload")
            if payload:
                body = json.loads(payload)
                jobs.append(body)
        return jobs



    

    def DeleteAllLogsForNight(self, nightId):
        # make sure that night exists
        logs = self.AnalyticsRepository.GetAllLogsForNight(nightId)
        if logs is None:
            return
        for log in logs:
            self.AnalyticsRepository.DeleteNightLog(log)

    def DeleteAllLogsForUpload(self, uploadId):
        logs = self.AnalyticsRepository.GetAllLogsForUpload(uploadId)
        if logs is None:
            return
        for log in logs:
            self.AnalyticsRepository.DeleteUploadLog(log)

    def GroupUploadLogs(self, job_history):
        grouped_history = {}
        # UploadLogDataEntry.TaskTitle
        for entry in job_history:
            step = entry.StepNumber
            progress = entry.Progress
            task_title = entry.TaskTitle
            message = entry.Message
            grouped_history[step] = {
                'TaskTitle': task_title,
                'Message': 'Fail' if progress == -1 else ('Success' if message is None else message),  # Error message if failed
                'Progress': progress
            }
        return grouped_history

    # todo fix this, but idk how lol lmao.....
    # def NewGroup(self, job_history):
    #     first_of_type = job_history[0]
    #     last_of_type = null
    #     jobs = []
    #     for job in job_history[1:]:
    #         if job.task_title == first_of_type.TaskTitle:
    #             last_of_type = job
    #             continue
    #         else:
    #             # this means that first and last of type should be collated. 
    #             n = JobLogEntry()
    #             n.Success = last_of_type.progress != -1
    #             n.TaskDuration = 
            
    def GroupNightLogs(self, job_history ):
        grouped_history = {}
        # UploadLogDataEntry.TaskTitle
        for entry in job_history:
            step = entry.StepNumber
            progress = entry.Progress
            task_title = entry.TaskTitle
            message = entry.Message
            # Always store/overwrite the step with the latest message
            # This ensures that only the final message for each step is recorded
            grouped_history[step] = {
                'TaskTitle': task_title,
                'Message': 'Fail' if progress == -1 else ('Success' if message is None else message),  # Error message if failed
                'Progress': progress
            }
        return grouped_history

    def CheckJobStatusForUploadedRecording(self, uploadId :int, RecordingIdentifier:str, jobs):
        def create_status_object(is_error=False, job_exists=False, job_history=[]):
            return {
                "is_error": is_error,
                "job_exists": job_exists,
                "job_history": job_history
            }
        is_in_queue = any(job.get("name") == RecordingIdentifier for job in jobs)
        job_history = self.AnalyticsRepository.GetAllLogsForNight(uploadId)
        cleaned_job_history = []
        for entry in job_history:
            clean_dict = {k: v for k, v in entry.__dict__.items() if not k.startswith('_')}
            cleaned_job_history.append(clean_dict)
        if is_in_queue:
            return create_status_object(job_exists=True, job_history=cleaned_job_history)
        if not cleaned_job_history:
            return create_status_object(is_error=True)
        cleaned_job_history = self.GroupUploadLogs(cleaned_job_history)
        return create_status_object(job_exists=False, job_history=cleaned_job_history)

