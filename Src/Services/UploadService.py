from Src.Models.Models import Centre, CentreUpload
from Src.Repositories.AuthenticationRepository import AuthenticationRepository 
from Src.Repositories.UploadsRepository import UploadRepository
from hashids import Hashids
import pika
import os 

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


    def GetUploadByName(self, name):
        uploadId = Hashids(salt=os.environ['HASHIDS_SALT']).decode(name)
        return self.UploadRepository.GetUploadById(uploadId)
        

    def GetAllUploads(self):
        pass
        # return self.AuthenticationRepository.GetAllCentres()

    def GetUploadById(self, centreId: int) -> Centre:
        pass 

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
        
        if not os.path.exists(fpath):
            os.makedirs(fpath)
        fpath = os.path.join(fpath, file.filename)

        with open(fpath, 'wb+') as file_object:
            file_object.write(file.file.read())


        connection = pika.BlockingConnection(self.connection_params)
        channel = connection.channel()
        
        # Declare the queue
        channel.queue_declare(queue=os.environ['TASK_QUEUE_NAME'], durable=True)
        # https://www.rabbitmq.com/tutorials/tutorial-one-python.html
        channel.basic_publish(
            exchange='',
            routing_key='task_queue',
            body=fpath,
            properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ))

        # Close the connection
        connection.close()