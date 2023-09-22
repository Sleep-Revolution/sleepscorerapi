import io
import re
from urllib.request import HTTPBasicAuthHandler
from zipfile import ZipFile
from Src.Models.Models import Centre, CentreUpload, Night
from Src.Repositories.AuthenticationRepository import AuthenticationRepository 
from Src.Repositories.UploadsRepository import UploadRepository
from Src.Repositories.AnalyticsRepository import AnalyticsRepository
from hashids import Hashids
import pika
import os 
import json
# from tqdm import tqdm
from pyzabbix import ZabbixMetric, ZabbixSender
import requests
from pyzabbix import ZabbixMetric, ZabbixSender

from requests.auth import HTTPBasicAuth

UPLOAD_DIR = os.environ['DATA_ROOT_DIR']
DATASET_DIR = os.environ['DATASET_DIR']

class UploadService:
    def __init__(self, authrepo=None):
        if authrepo:
            self.AuthenticationRepository = authrepo
        else:
            self.AuthenticationRepository = AuthenticationRepository()

        self.UploadRepository = UploadRepository()
        self.AnalyticsRepository = AnalyticsRepository() 

        self.creds = pika.PlainCredentials('server', 'server')
        self.connection_params = pika.ConnectionParameters(os.environ['RABBITMQ_SERVER'], 5672, '/', self.creds)
        self.individualNightWaitingRoom = os.environ['INDIVIDUAL_NIGHT_WAITING_ROOM']


    

    def GetUploadByName(self, name):
        uploadId = Hashids(salt=os.environ['HASHIDS_SALT']).decode(name)
        return self.UploadRepository.GetUploadById(uploadId)
        
    def GetUploadById(self, id):
        return self.UploadRepository.GetUploadById(id)

    def GetAllUploads(self):
        pass
        # return self.AuthenticationRepository.GetAllCentres()

    def GetAllCentres(self):
        return self.UploadRepository.GetAllCentres()


    async def CreateUpload(self, centreId, file, recordingNumber):
        db_c = self.AuthenticationRepository.GetCentreById(centreId)
        if not db_c:
            raise ValueError(f"Centre with id {centreId} does not exist")

        newCentreUpload =  CentreUpload()
        newCentreUpload.CentreId = centreId
        newCentreUpload.RecordingNumber = recordingNumber
        newCentreUpload.ESR = f'{db_c.Prefix}{str(db_c.MemberNumber).zfill(2)}{str(recordingNumber).zfill(2)}'
        newCentreUpload.Location = os.path.join(db_c.FolderLocation, newCentreUpload.ESR)

        # newCentreUpload.ParticipantAge = ParticipantAge
        # newCentreUpload.ParticipantHeight = ParticipantHeight
        # newCentreUpload.ParticipantWeight = ParticipantWeight 
        # newCentreUpload.ParticipantSex = ParticipantSex
        # newCentreUpload.ParticipantMedicalHistory = ParticipantMedicalHistory

        upload = self.UploadRepository.CreateNewUpload(newCentreUpload)
        
        # hashids = Hashids(salt=os.environ['HASHIDS_SALT'])
        # name = hashids.encode(upload.Id)
        # newCentreUpload.Location = os.path.join(db_c.FolderLocation, name)
        fpath = os.path.join(UPLOAD_DIR,db_c.FolderLocation, newCentreUpload.ESR)

        #if not exists, create path in individualnightwaitingroom for centre.
        
        if not os.path.exists(fpath):
            os.makedirs(fpath)
        
        cpath = os.path.join(self.individualNightWaitingRoom, db_c.FolderLocation)
        if not os.path.exists(cpath):
            os.makedirs(cpath)
        
        # fpath = os.path.join(fpath, newC)

        # with open(fpath, 'wb+') as file_object:
        #     file_object.write(file.file.read())
        zip_bytes = await file.read()

        # Create an in-memory file-like object
        zip_file = io.BytesIO(zip_bytes)

        # Open the zip file
        with ZipFile(zip_file, 'r') as zip_obj:
            # Extract and save each file in the zip
            dirs = zip_obj.infolist()
            base_folder_names = set()

            for file_info in zip_obj.infolist():
                base_folder_name = os.path.dirname(file_info.filename)
                base_folder_names.add(base_folder_name)

            if len(base_folder_names) != 1:
                raise ValueError({"message": "Invalid zip file. There should be only one base folder."})

            base_folder_name = base_folder_names.pop()
            print(f"~\tBase folder: {base_folder_name}")
            for file_info in zip_obj.infolist():
                if file_info.is_dir():
                    continue
                if not file_info.filename.startswith(f"{base_folder_name}/"):
                    continue
                print(f"\t z:{file_info.filename}")
                file_content = zip_obj.read(file_info)
                extracted_file_name = os.path.basename(file_info.filename)
                
                file_name = file_info.filename
                # Save the file content or process it as needed
                # For example, save it to disk
                with open(os.path.join(fpath, extracted_file_name), "wb") as output_file:
                    output_file.write(file_content)

        zabbix_server = '130.208.209.7'

        # Create metrics
        metrics = [ZabbixMetric('sleepwell.sleep.ru.is', 'ESADA.upload', db_c.CentreName)]

        # Create a ZabbixSender instance
        zbx = ZabbixSender(zabbix_server)

        # Send metrics to zabbix
        zbx.send(metrics)
        #send_to_zabbix([Metric('sleepwell.sleep.ru.is', 'ESADA.upload',  db_c.CentreName)], zabbix_server, 10051)
        #  This is going in another place!
        

    def addNightToUpload(self, uploadId: int, nightLocation:str, quality:str, metadata:str):
        
        db_u = self.UploadRepository.GetUploadById(uploadId)
        if not db_u:
            raise ValueError("No upload found for this night")

        db_c = self.AuthenticationRepository.GetCentreById(db_u.CentreId)
        if not db_c:
            raise ValueError(f"Found upload that does not have a valid centre! Centre with id {db_u.CentreId} does not exist")


        newNight = Night()
        newNight.IsFaulty = False if quality == 'good'  else True
        newNight.UploadId = uploadId
        newNight.Location = nightLocation
        newNight.metadata = metadata
        newNight.NightNumber = int(nightLocation[-2:])

        self.UploadRepository.AddNightToUpload(newNight)
        # Id = Column(Integer, primary_key=True, index=True)
        # UploadId = Column(Integer, ForeignKey("CentreUploads.Id"))
        # NightNumber = Column(Integer)
        # Location = Column(String)
        # IsFaulty = Column(Boolean)
        # Reviewed = Column(Boolean)
        # Upload = relationship("CentreUpload", back_populates="")

        body = {
            'name': os.path.basename(nightLocation),
            'path': db_c.FolderLocation,
            'dataset': False,
            'centreId': db_c.Id
        }
        connection = pika.BlockingConnection(self.connection_params)
        channel = connection.channel()
        # # Declare the queue
        channel.queue_declare(queue=os.environ['TASK_QUEUE_NAME'], durable=True)
        # # https://www.rabbitmq.com/tutorials/tutorial-one-python.html
        channel.basic_publish(
            exchange='',
            routing_key=os.environ['TASK_QUEUE_NAME'],
            body=json.dumps(body),
            properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ))
        # # Close the connection
        connection.close()

    async def createDataset(self, file, datasetName):
        
        fpath = os.path.join(UPLOAD_DIR,"DATASETS", datasetName)
        zip_bytes = await file.read()

        # Create an in-memory file-like object
        zip_file = io.BytesIO(zip_bytes)
        # with ZipFile(zip_file, 'r') as zip_obj:
        #     for file_info in zip_obj.infolist():
        #         extracted_file_name = os.path.join(fpath, file_info.filename)
        #         zip_obj.extract(file_info, fpath)
        
        with ZipFile(zip_file, 'r') as zip_obj:
            file_list = zip_obj.infolist()
            # Create a progress bar using tqdm
            # with tqdm(total=len(file_list), desc="Extracting files", unit="file") as pbar:
            for file_info in file_list:
                extracted_file_name = os.path.join(fpath, file_info.filename)
                zip_obj.extract(file_info, fpath)
                    # pbar.update(1)  # Update the progress bar


        # Open the zip file
        # with ZipFile(zip_file, 'r') as zip_obj:
        #     # Extract and save each file in the zip
        #     dirs = zip_obj.infolist()
        #     base_folder_names = set()

        #     for file_info in zip_obj.infolist():
        #         base_folder_name = os.path.dirname(file_info.filename)
        #         base_folder_names.add(base_folder_name)

            
        #     for file_info in zip_obj.infolist():
        #         print(f"\t z:{file_info.filename}")
        #         file_content = zip_obj.read(file_info)
        #         extracted_file_name = os.path.basename(file_info.filename)
                
        #         file_name = file_info.filename
        #         # Save the file content or process it as needed
        #         # For example, save it to disk
        #         with open(os.path.join(fpath, extracted_file_name), "wb") as output_file:
        #             output_file.write(file_content)

    def listDatasets(self):
        fpath = os.path.join(DATASET_DIR)
        return list(os.listdir(fpath))




    def verifyIsRecording(self, path):
        files = os.listdir(path)
        numNdb = len( list(filter(lambda x: x.lower()[-4:] == '.ndb', files)))
        numNdf = len( list(filter(lambda x: x.lower()[-4:] == '.ndf', files)))
        # print(f"{path} has {numNdf} Ndf files and {numNdb} ndb files")
        reason = ""
        reason += f"The Folder has {numNdb} ndb files."
        reason += f"The folder has {numNdf} Ndf files."
        valid = True
        if numNdb != 1:
            valid = False
        if numNdf == 0:
            valid = False
        return valid, reason

    def group_job_history(self, job_history):
        grouped_history = {}

        for entry in job_history:

            print(entry)
            step = entry['StepNumber']
            progress = entry['Progress']
            task_title = entry['TaskTitle']
            message = entry['Message']

            # If step not in grouped history or the current progress is termination (1, -1, 2)
            if step not in grouped_history or progress in [1, -1, 2]:
                grouped_history[step] = {
                    'TaskTitle': task_title,
                    'Message': message if progress == -1 else task_title  # Error message if failed
                }
        
        return grouped_history
    
    def listDataset(self, name):
        fpath = os.path.join(DATASET_DIR, name)
        r = []
        jobs = self.GetJobsInQueue()
        for d in os.listdir(fpath):
            dd = os.path.join(fpath, d)
            j = self.CheckJobStatusForRecordingInDataset(name, d, jobs)
            j['job_history'] = self.group_job_history(j['job_history'])
            x = self.verifyIsRecording(dd)
            r.append({"recording": d, "valid": x, "jobstatus": j})
        return r

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

    
    def CheckJobStatusForRecordingInDataset(self, datasetName, recordingName, jobs):
        def create_status_object(is_error=False, job_exists=False, job_history=[]):
            return {
                "is_error": is_error,
                "job_exists": job_exists,
                "job_history": job_history
            }

        is_in_queue = any(job.get("name") == recordingName and job.get("path") == f"DATASETS/{datasetName}" for job in jobs)
        
        job_history = self.GetHistory(recordingName, datasetName)
        
        cleaned_job_history = []
        for entry in job_history:
            clean_dict = {k: v for k, v in entry.__dict__.items() if not k.startswith('_')}
            cleaned_job_history.append(clean_dict)

        if is_in_queue:
            return create_status_object(job_exists=True, job_history=cleaned_job_history)
        
        if not cleaned_job_history:
            return create_status_object(is_error=True)
        
        return create_status_object(job_exists=False, job_history=cleaned_job_history)

    def GetHistory(self, recordingName, datasetName):
        return self.AnalyticsRepository.GetAllLogsForFile(recordingName, datasetName)

    def GetLastJobStatus(self, recordingName, datasetName):
        status_obj = {
            "message": "wat",
            "is_error": False,
            "additional_info": None
        }
        log = self.AnalyticsRepository.GetLastLogForFile(recordingName, datasetName)
        if log is None:
            status_obj["message"] = None
            return status_obj   
        if log.Progress == 2:
            status_obj["message"] = "Job finished successfully"
        elif log.Progress == -1:
            status_obj["message"] = f"Job failed in task '{log.TaskTitle}' with the message '{log.Message}'"
            status_obj["is_error"] = True
        elif log.Progress == 0:
            status_obj["message"] = f"Job started task '{log.TaskTitle}'"
        elif log.Progress == 1:
            status_obj["message"] = f"Job finished task '{log.TaskTitle}'"
        return status_obj

    

    def CreateJobsForDataset(self, datasetname):

        connection = pika.BlockingConnection(self.connection_params)
        channel = connection.channel()
        # # Declare the queue
        channel.queue_declare(queue=os.environ['TASK_QUEUE_NAME'], durable=True)

        fpath = os.path.join(DATASET_DIR, datasetname)

        for d in os.listdir(fpath):
            body = {
                'name': d,
                'path': f"{datasetname}",
                'dataset': True,
                'centreId': 9999
            }
        # # https://www.rabbitmq.com/tutorials/tutorial-one-python.html
            channel.basic_publish(
                exchange='',
                routing_key=os.environ['TASK_QUEUE_NAME'],
                body=json.dumps(body),
                properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ))
        # # Close the connection
        connection.close()



    def RescanLocation(self, path):
        # Take location, and re scan it, location is a folder that has n folders, each of which has some amount of ndb and ndf.
        # p = os.path.join(path)
        folders = os.listdir(path)
        for folder in folders:
            p = os.path.join(path, folder)
            if not os.path.isdir(p):
                raise Exception(f"Found something that is not a folder in project root directory: {p}")

            if not self.verifyIsRecording(p):
                raise Exception(f"Found something that is not a folder in project root directory: {p}")

            regx = re.compile(r"\d{2}\d{2}-\d{2}")
            # if not regx.fullmatch()
        pass

    def RescanLocationsForUpload(self, uploadId):
        upload = self.UploadRepository.GetUploadById(uploadId)
        if not upload:
            raise ValueError(f"No upload found with Id {uploadId}")
        #find location of nights for centre.
        location = os.path.join(self.individualNightWaitingRoom, upload.Centre.FolderLocation)
        if not os.path.exists(location):
            print("No location exists.")
            return []
        esrMatch = list(filter(lambda x: os.path.basename(x)[:4] == upload.ESR, os.listdir(location)))
        
        return [{'ESR': x, 'isValid': self.verifyIsRecording(os.path.join(location, x) )} for x in esrMatch] 

    def RescanLocations(self):
        for centre in os.listdir(self.individualNightWaitingRoom):
            pwd = os.path.join(self.individualNightWaitingRoom, centre)
            for project in os.listdir(pwd):
                self.RescanLocation(os.path.join(pwd, project))


    def get_active_connections(self, queue_name):
        api_url = 'http://130.208.209.2:15672/api/queues/%2F/{0}'.format(queue_name)
        auth = ('monitor', 'monitor')  # RabbitMQ default credentials

        try:
            response = requests.get(api_url, auth=auth)
            if response.status_code == 200:
                queue_info = response.json()
                return queue_info['consumer_details']
            else:
                print('Error: {0} - {1}'.format(response.status_code, response.text))
                return []
        except requests.exceptions.RequestException as e:
            print('Error: {0}'.format(str(e)))
            return []
            # text:'{"error":"not_authorised","reason":"Not management user"}'
