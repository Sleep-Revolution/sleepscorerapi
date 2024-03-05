import io
import shutil
from sqlalchemy.inspection import inspect
import re
from urllib.request import HTTPBasicAuthHandler
from zipfile import ZipFile
from Src.Infrastructure.Utils import GetRecordingIdentifierForNight, GetRecordingIdentifierForUpload
from Src.Models.Models import Centre, CentreUpload, Night
from Src.Repositories.AuthenticationRepository import AuthenticationRepository 
from Src.Repositories.UploadsRepository import UploadRepository
from Src.Repositories.AnalyticsRepository import AnalyticsRepository
from hashids import Hashids
import pika
import os 
import json
from pyzabbix import ZabbixMetric, ZabbixSender
import requests
from pyzabbix import ZabbixMetric, ZabbixSender
from Src.Services.AnalyticsService import AnalyticsService

UPLOAD_DIR = os.environ['DATA_ROOT_DIR']
DATASET_DIR = os.environ['DATASET_DIR']

class UploadService:
    def __init__(self, authrepo=None):
        if authrepo:
            self.AuthenticationRepository = authrepo
        else:
            self.AuthenticationRepository = AuthenticationRepository()

        self.UploadRepository = UploadRepository()
        # self.AnalyticsRepository = AnalyticsRepository() 
        self.AnalyticsService = AnalyticsService()
        self.creds = pika.PlainCredentials('server', 'server')
        self.connection_params = pika.ConnectionParameters(os.environ['RABBITMQ_SERVER'], 5672, '/', self.creds)
        self.individualNightWaitingRoom = os.environ['INDIVIDUAL_NIGHT_WAITING_ROOM']

    def GetUploadByName(self, name):
        uploadId = Hashids(salt=os.environ['HASHIDS_SALT']).decode(name)
        return self.UploadRepository.GetUploadById(uploadId)
        
    def GetUploadById(self, id):
        x = self.UploadRepository.GetUploadById(id)
        for _ in x.Nights:
            _.CompressedLogs = AnalyticsService.GroupUploadLogs(None, _.Logs)
        return x

    def GetAllUploads(self):
        pass
        # return self.AuthenticationRepository.GetAllCentres()

    def GetAllCentres(self):
        x = self.UploadRepository.GetAllCentres()
        for centre in x:
            for upload in centre.CentreUploads:
                upload.CompressedLogs = AnalyticsService.GroupUploadLogs(None, upload.Logs)
        return x

    async def GetUploadFeed(self):
        return await self.UploadRepository.GetLastNRecordings(10)

    async def CreateUpload(self, centreId, file, recordingNumber, isFollowup):
        db_c = self.AuthenticationRepository.GetCentreById(centreId)
        if not db_c:
            raise ValueError(f"Centre with id {centreId} does not exist")
        CentreName = db_c.CentreName
        existingUploads = self.UploadRepository.GetAllUploadsForCentre(centreId)
        if recordingNumber in [_.RecordingNumber for _ in existingUploads] and not isFollowup:
            raise ValueError(f"Recording with number {recordingNumber} already exists for this center.")
        if recordingNumber not in [_.RecordingNumber for _ in existingUploads] and isFollowup:
            raise ValueError(f"Recording with number {recordingNumber} does not exist for this center.")
        if recordingNumber in [_.RecordingNumber for _ in existingUploads] and isFollowup:
            existingUploads = list(filter(lambda x: x.RecordingNumber == recordingNumber and x.IsFollowup, existingUploads))
            if len(existingUploads) > 0:
                raise Exception(f"Recording Number {recordingNumber} already has a returning visit.")

        if recordingNumber < 1:
            raise ValueError(f"Recording number must be greater than 0") 

        newCentreUpload =  CentreUpload()
        newCentreUpload.CentreId = centreId
        newCentreUpload.IsFollowup = isFollowup
        newCentreUpload.RecordingNumber = recordingNumber
        newCentreUpload.RecordingIdentifier = GetRecordingIdentifierForUpload(newCentreUpload, db_c) #f'{db_c.Prefix}{str(db_c.MemberNumber).zfill(2)}-{str(recordingNumber).zfill(2)}'
        newCentreUpload.Location = os.path.join(db_c.FolderLocation, newCentreUpload.RecordingIdentifier)
        fpath = os.path.join(UPLOAD_DIR,db_c.FolderLocation)
        if not os.path.exists(fpath):
            os.makedirs(fpath)
        # Centre path
        cpath = os.path.join(self.individualNightWaitingRoom, db_c.FolderLocation)
        # Create the centre path if it does not exist
        if not os.path.exists(cpath):
            os.makedirs(cpath)
        # Create the recording path if it does not exist
        zip_bytes = await file.read()
        zip_file_path = os.path.join(fpath, f"{newCentreUpload.RecordingIdentifier}.zip")  # Construct the path for the ZIP file
        with open(zip_file_path, 'wb') as zf:
            zf.write(zip_bytes)
        # Create the upload in the database
        upload = self.UploadRepository.CreateNewUpload(newCentreUpload)
        # Create a job for the upload
        self.createJobForUpload(upload.Id)
        try:

            zabbix_server = '130.208.209.7'
            # Create metrics
            metrics = [ZabbixMetric('sleepwell.sleep.ru.is', 'ESADA.upload', CentreName)]
            # Create a ZabbixSender instance
            zbx = ZabbixSender(zabbix_server)
            # Send metrics to zabbix
            zbx.send(metrics)
        except Exception as e:
            print(f"Failed to send metrics to zabbix: {e}")

        #send_to_zabbix([Metric('sleepwell.sleep.ru.is', 'ESADA.upload',  db_c.CentreName)], zabbix_server, 10051)

    def createJobForUpload(self, uploadId: int): 
        upload = self.UploadRepository.GetUploadById(uploadId)
        db_c = self.AuthenticationRepository.GetCentreById(upload.CentreId)
        recordingIdentifier = GetRecordingIdentifierForUpload(upload, db_c)
        if not os.path.isfile(os.path.join(
                UPLOAD_DIR,
                db_c.FolderLocation,
                recordingIdentifier + '.zip'
            )):
            raise Exception("Did not find a zip file with the name " + os.path.join(
                UPLOAD_DIR, db_c.FolderLocation, recordingIdentifier + '.zip'
            ))

        body = {
            'name': f"{recordingIdentifier}.zip", 'path': db_c.FolderLocation,
            'isFollowup': upload.IsFollowup, 'dataset': False,
            'centreId': db_c.Id, 'uploadId': upload.Id
        }
        connection = pika.BlockingConnection(self.connection_params)
        channel = connection.channel()
        # # Declare the queue
        channel.queue_declare(queue=os.environ['SPLITTER_QUEUE_NAME'], durable=True)
        # # https://www.rabbitmq.com/tutorials/tutorial-one-python.html
        channel.basic_publish(
            exchange='',
            routing_key=os.environ['SPLITTER_QUEUE_NAME'],
            body=json.dumps(body),
            properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ))
        # # Close the connection
        connection.close()


    def getAllUploadsForCentre(self, centreId: int):
        uploads = self.UploadRepository.GetAllUploadsForCentre(centreId)
        centre = self.AuthenticationRepository.GetCentreById(centreId)
        jobs = self.AnalyticsService.GetJobsForUploadsInQueue()
        for i in range(len(uploads)):
            uploads[i].RecordingIdentifier = GetRecordingIdentifierForUpload(uploads[i], centre) #f"{centre.Prefix}{str(centre.MemberNumber).zfill(2)}{str(uploads[i].RecordingNumber).zfill(2)}" 
            # uploads[i].IsInQueue is true if a job exists for this upload
            uploads[i].IsInQueue = True if len(list(filter(lambda x: x['uploadId'] == uploads[i].Id, jobs))) > 0 else False
        return uploads

    def addNightToUpload(self, uploadId: int, nightNumber:int):
        db_u = self.UploadRepository.GetUploadById(uploadId)
        if not db_u:
            raise ValueError("No upload found for this night")

        db_c = self.AuthenticationRepository.GetCentreById(db_u.CentreId)
        if not db_c:
            raise ValueError(f"Found upload that does not have a valid centre! Centre with id {db_u.CentreId} does not exist")

        newNight = Night()
        newNight.IsFollowup = db_u.IsFollowup
        newNight.UploadId = uploadId
        newNight.NightNumber = nightNumber
        db_night = self.UploadRepository.AddNightToUpload(newNight)
        print("Creating jobbo")
        self.CreateJobForNight(db_night.Id)
        

    def CreateJobForNight(self, nightId):
        db_n = self.UploadRepository.GetNightById(nightId)
        db_c = self.AuthenticationRepository.GetCentreById(db_n.Upload.CentreId)
        db_u = self.UploadRepository.GetUploadById(db_n.UploadId)
        recordingIdentifier = GetRecordingIdentifierForNight(db_n, db_c, db_u)
        nightLocation = os.path.join(os.environ['INDIVIDUAL_NIGHT_WAITING_ROOM'], db_c.FolderLocation, recordingIdentifier)
        body = {
            'name': os.path.basename(nightLocation),
            'path': db_c.FolderLocation,
            'dataset': False,
            'centreId': db_c.Id,
            'uploadId': db_n.UploadId,
            'nightId': db_n.Id
        }
        connection = pika.BlockingConnection(self.connection_params)
        channel = connection.channel()
        # # Declare the queue
        channel.queue_declare(queue=os.environ['TASK_QUEUE_NAME'], durable=True)
        # # https://www.rabbitmq.com/tutorials/tutorial-one-python.html
        channel.basic_publish(
            exchange='', routing_key=os.environ['TASK_QUEUE_NAME'],
            body=json.dumps(body), properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ))
        # # Close the connection
        connection.close()

    async def createDataset(self, file, datasetName):
        fpath = os.path.join(UPLOAD_DIR,"DATASETS", datasetName)
        zip_bytes = await file.read()
        zip_file = io.BytesIO(zip_bytes)        
        with ZipFile(zip_file, 'r') as zip_obj:
            file_list = zip_obj.infolist()
            # Create a progress bar using tqdm
            for file_info in file_list:
                extracted_file_name = os.path.join(fpath, file_info.filename)
                zip_obj.extract(file_info, fpath)
                    # pbar.update(1)  # Update the progress bar

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

    def listDataset(self, name):
        fpath = os.path.join(DATASET_DIR, name)
        r = []
        jobs = self.AnalyticsService.GetJobsInQueue()
        for d in os.listdir(fpath):
            dd = os.path.join(fpath, d)
            j = self.AnalyticsService.CheckJobStatusForRecordingInDataset(name, d, jobs)
            j['job_history'] = self.AnalyticsService.group_job_history(j['job_history'])
            x = self.verifyIsRecording(dd)
            r.append({"recording": d, "valid": x, "meta": j})
        return r
    
    def CreateJobsForDataset(self, datasetname):
        connection = pika.BlockingConnection(self.connection_params)
        channel = connection.channel()
        # # Declare the queue
        channel.queue_declare(queue=os.environ['TASK_QUEUE_NAME'], durable=True)
        fpath = os.path.join(DATASET_DIR, datasetname)
        for d in os.listdir(fpath):
            body = {
                'name': d, 'path': f"{datasetname}",
                'dataset': True, 'centreId': 9999
            }
            # https://www.rabbitmq.com/tutorials/tutorial-one-python.html
            channel.basic_publish(
                exchange='', routing_key=os.environ['TASK_QUEUE_NAME'],
                body=json.dumps(body), properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ))
        # # Close the connection
        connection.close()

    def RescanLocation(self, path):
        # Take location, and re scan it, location is a folder that has n folders, each of which has some amount of ndb and ndf.
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

    def DeleteUpload(self, uploadId):
        # Get the upload. 
        upload = self.UploadRepository.GetUploadById(uploadId)
        if upload is None:
            raise ValueError(f"Upload with id {uploadId} does not exist")
        self.AnalyticsService.DeleteAllLogsForUpload(uploadId)
        # for each night, delete the night
        for night in upload.Nights:
            self.DeleteNight(night.Id)
        # then delete the upload
        self.UploadRepository.DeleteUpload(uploadId)
        # delete the zip file
        fpath = os.path.join(UPLOAD_DIR,upload.Centre.FolderLocation)
        zip_file_path = os.path.join(fpath, f"{upload.RecordingIdentifier}.zip") 
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)
        else:
            print(f"Could not find {zip_file_path} to delete it.")
            
    def DeleteNight(self, nightId):
        # get the night or fail
        night = self.UploadRepository.GetNightById(nightId)
        if night is None:
            raise ValueError(f"Night with id {nightId} does not exist")
        db_u = self.UploadRepository.GetUploadById(night.UploadId)
        db_c = self.AuthenticationRepository.GetCentreById(db_u.CentreId)
        # delete all logs for night
        self.AnalyticsService.DeleteAllLogsForNight(nightId)
        # delete the night
        self.UploadRepository.DeleteNight(nightId)
        # delete the folder
        nightLocation = os.path.join(os.environ['INDIVIDUAL_NIGHT_WAITING_ROOM'], night.Upload.Centre.FolderLocation, GetRecordingIdentifierForNight(night, db_c, db_u))
        if os.path.exists(nightLocation):
            # os.rmdir(nightLocation)
            shutil.rmtree(nightLocation)
        else:
            print(f"Could not find {nightLocation} to delete it.")
