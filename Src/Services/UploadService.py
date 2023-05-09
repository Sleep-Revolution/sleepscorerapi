import re
from Src.Models.Models import Centre, CentreUpload
from Src.Repositories.AuthenticationRepository import AuthenticationRepository 
from Src.Repositories.UploadsRepository import UploadRepository
from hashids import Hashids
import pika
import os 
import json

UPLOAD_DIR = os.environ['DATA_ROOT_DIR']


class UploadService:
    def __init__(self, authrepo=None):
        if authrepo:
            self.AuthenticationRepository = authrepo
        else:
            self.AuthenticationRepository = AuthenticationRepository()

        self.UploadRepository = UploadRepository()

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


    def CreateUpload(self, centreId, file):
        db_c = self.AuthenticationRepository.GetCentreById(centreId)
        if not db_c:
            raise ValueError(f"Centre with id {centreId}")

        newCentreUpload =  CentreUpload()
        newCentreUpload.CentreId = centreId
        upload = self.UploadRepository.CreateNewUpload(newCentreUpload)
        
        hashids = Hashids(salt=os.environ['HASHIDS_SALT'])
        name = hashids.encode(upload.Id)
        fpath = os.path.join(UPLOAD_DIR,db_c.FolderLocation, name)
        newCentreUpload.Location = os.path.join(db_c.FolderLocation, name)
        if not os.path.exists(fpath):
            os.makedirs(fpath)
        fpath = os.path.join(fpath, file.filename)

        with open(fpath, 'wb+') as file_object:
            file_object.write(file.file.read())

        body = {
            'name':name,
            'path': db_c.FolderLocation,
            'centreId': centreId
        }
    
    def verifyIsRecording(self, path):
        files = os.listdir(path)
        numNdb = len( list(filter(lambda x: x.lower()[-4:] == '.ndb', files)))
        numNdf = len( list(filter(lambda x: x.lower()[-4:] == '.ndf', files)))
        print(f"{path} has {numNdf} Ndf files and {numNdb} ndb files")
        return True

    def RescanLocation(self, path):
        # Take location, and re scan it, location is a folder that has n folders, each of which has some amoujnt of ndb and ndf.
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
        upload = UploadRepository.GetUploadById(uploadId)
        location = os.path.join(self.individualNightWaitingRoom, self.upload.Location)

    def RescanLocations(self):
        for centre in os.listdir(self.individualNightWaitingRoom):
            pwd = os.path.join(self.individualNightWaitingRoom, centre)
            for project in os.listdir(pwd):
                self.RescanLocation(os.path.join(pwd, project))


        #  This is going in another place!
        # connection = pika.BlockingConnection(self.connection_params)
        # channel = connection.channel()
        
        # # Declare the queue
        # channel.queue_declare(queue=os.environ['TASK_QUEUE_NAME'], durable=True)
        # # https://www.rabbitmq.com/tutorials/tutorial-one-python.html
        # channel.basic_publish(
        #     exchange='',
        #     routing_key='task_queue',
        #     body=json.dumps(body),
        #     properties=pika.BasicProperties(
        #     delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        # ))

        # # Close the connection
        # connection.close()