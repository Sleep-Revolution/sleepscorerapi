from sqlalchemy.orm import Session
from Src.Models.Models import Centre, CentreCreate, AuthCredentials
import bcrypt
from Src.Repositories.AuthenticationRepository import AuthenticationRepository 
from Src.Infrastructure.JWT import CreateAccessToken

class AuthenticationService:
    def __init__(self, authrepo=None):
        if authrepo:
            self.AuthenticationRepository = authrepo
        else:
            self.AuthenticationRepository = AuthenticationRepository()

    def GetAllCentres(self):
        return self.AuthenticationRepository.GetAllCentres()

    def GetCentreById(self, centreId: int) -> Centre:
        return self.AuthenticationRepository.GetCentreById(centreId)

    def CreateCentre(self, CentreName: str, ResponsibleEmail: str, Description:str, Password1:str, Password2:str):
        db_c = self.AuthenticationRepository.GetCentreByName(CentreName)
        if db_c:
            raise ValueError("Centre with this name already exists")
        db_c = self.AuthenticationRepository.GetCentreByEmail(ResponsibleEmail)
        if db_c:
            raise ValueError("Centre with this email already exists")

        newCentre =  Centre()
        newCentre.CentreName = CentreName
        newCentre.Description = Description
        newCentre.ResponsibleEmail = ResponsibleEmail
        newCentre.PasswordSalt = bcrypt.gensalt()
        newCentre.PasswordHash = bcrypt.hashpw(Password1.encode('utf-8'), newCentre.PasswordSalt)
        newCentre.FolderLocation = f'{newCentre.CentreName}'
        newCentre.IsAdministrator = False
        return self.AuthenticationRepository.CreateCentre(newCentre)
    
    def UpdateCentrePassword(self, centreId: int, newPassword: str):
        db_centre = self.AuthenticationRepository.GetCentreById(centreId)
        if not db_centre:
            raise ValueError("Credentials not found in our systems.")
        salt = bcrypt.gensalt()
        hash = bcrypt.hashpw(newPassword.encode('utf-8'), salt)
        self.AuthenticationRepository.SetCentrePassword(centreId, salt, hash)


    def AuthenticateCentre(self, centre: AuthCredentials):
        # db_centre = self.AuthenticationRepository.GetCentreByName(centre.CentreName)
        db_centre = self.AuthenticationRepository.GetCentreByEmail(centre.Email)
        if(db_centre == None):
            raise ValueError("Credentials not found in our systems.")
        
        testHash = bcrypt.hashpw(centre.Password.encode('utf-8'), db_centre.PasswordSalt)
        if testHash != db_centre.PasswordHash:
            raise ValueError("Credentials not found in our systems.")
        self.AuthenticationRepository.SetLogin(db_centre.Id)
        return CreateAccessToken(db_centre.Id)