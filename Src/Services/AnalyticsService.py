import json
from sqlalchemy.orm import Session
from Src.Models.Models import Centre, CentreCreate, AuthCredentials, NightLogDataEntry, NightLogEntity, UploadLogDataEntry, UploadLogEntity
import bcrypt
from Src.Repositories.AnalyticsRepository import AnalyticsRepository 
from Src.Infrastructure.JWT import CreateAccessToken
import requests
from requests.auth import HTTPBasicAuth

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

    def GetJobsInQueue(self):
        get_messages_url = f"http://130.208.209.2:15672/api/queues/%2f/dev_task_queue/get"
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


    # def CheckJobStatusForUploadedRecording(self, ESR):
    #     def create_status_object(is_error=False, job_exists=False, job_history=[]):
    #         return {
    #             "is_error": is_error,
    #             "job_exists": job_exists,
    #             "job_history": job_history
    #         }

    #     is_in_queue = any(job.get("name") == recordingName and job.get("path") == f"DATASETS/{datasetName}" for job in jobs)
        
    #     job_history = self.GetHistory(recordingName, datasetName)
        
    #     cleaned_job_history = []
    #     for entry in job_history:
    #         clean_dict = {k: v for k, v in entry.__dict__.items() if not k.startswith('_')}
    #         cleaned_job_history.append(clean_dict)

    #     if is_in_queue:
    #         return create_status_object(job_exists=True, job_history=cleaned_job_history)
        
    #     if not cleaned_job_history:
    #         return create_status_object(is_error=True)
        
    #     return create_status_object(job_exists=False, job_history=cleaned_job_history)
    
    def group_job_history(self, job_history):
        grouped_history = {}

        for entry in job_history:
            step = entry['StepNumber']
            progress = entry['Progress']
            task_title = entry['TaskTitle']
            message = entry['Message']

            # Always store/overwrite the step with the latest message
            # This ensures that only the final message for each step is recorded
            grouped_history[step] = {
                'TaskTitle': task_title,
                'Message': 'Fail' if progress == -1 else 'Success',  # Error message if failed
                'Progress': progress
            }
        
        return grouped_history



    def CheckJobStatusForRecordingInDataset(self, datasetName, recordingName, jobs):
        def create_status_object(is_error=False, job_exists=False, job_history=[]):
            return {
                "is_error": is_error,
                "job_exists": job_exists,
                "job_history": job_history
            }

        is_in_queue = any(job.get("name") == recordingName and job.get("path") == f"DATASETS/{datasetName}" for job in jobs)
        
        job_history = self.GetHistoryForRecordingInDataset(recordingName, datasetName)
        
        cleaned_job_history = []
        for entry in job_history:
            clean_dict = {k: v for k, v in entry.__dict__.items() if not k.startswith('_')}
            cleaned_job_history.append(clean_dict)

        if is_in_queue:
            return create_status_object(job_exists=True, job_history=cleaned_job_history)

        if not cleaned_job_history:
            return create_status_object(is_error=True)
        
        return create_status_object(job_exists=False, job_history=cleaned_job_history)


    def CheckJobStatusForUploadedRecording(self, ESR, jobs):
        def create_status_object(is_error=False, job_exists=False, job_history=[]):
            return {
                "is_error": is_error,
                "job_exists": job_exists,
                "job_history": job_history
            }

        is_in_queue = any(job.get("name") == ESR for job in jobs)
        
        job_history = self.GetHistoryForUploadedRecording(ESR)
        
        cleaned_job_history = []
        for entry in job_history:
            clean_dict = {k: v for k, v in entry.__dict__.items() if not k.startswith('_')}
            cleaned_job_history.append(clean_dict)

        if is_in_queue:
            return create_status_object(job_exists=True, job_history=cleaned_job_history)
        
        if not cleaned_job_history:
            return create_status_object(is_error=True)
        
        cleaned_job_history = self.group_job_history(cleaned_job_history)
        return create_status_object(job_exists=False, job_history=cleaned_job_history)


    def GetHistoryForRecordingInDataset(self, recordingName, datasetName):
        pass
        # return self.AnalyticsRepository.GetAllLogsForFile(recordingName, datasetName)


    def GetHistoryForUploadedRecording(self, ESR):
        pass
        # return self.AnalyticsRepository.GetAllLogsForUploadedRecording(ESR)


    # def GetLastJobStatus(self, recordingName, datasetName):
    #     raise Exception("I hate myself.")
    #     status_obj = {
    #         "message": "wat",
    #         "is_error": False,
    #         "additional_info": None
    #     }
    #     log = self.AnalyticsRepository.GetLastLogForFile(recordingName, datasetName)
    #     if log is None:
    #         status_obj["message"] = None
    #         return status_obj   
    #     if log.Progress == 2:
    #         status_obj["message"] = "Job finished successfully"
    #     elif log.Progress == -1:
    #         status_obj["message"] = f"Job failed in task '{log.TaskTitle}' with the message '{log.Message}'"
    #         status_obj["is_error"] = True
    #     elif log.Progress == 0:
    #         status_obj["message"] = f"Job started task '{log.TaskTitle}'"
    #     elif log.Progress == 1:
    #         status_obj["message"] = f"Job finished task '{log.TaskTitle}'"
    #     return status_obj

    