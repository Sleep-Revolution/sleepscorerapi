''' This is an ugly work in progress..... '''

import json
from fastapi.testclient import TestClient
import os
import sys
import sqlite3
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
import jwt
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Src.Models.Models import Centre, CentreCreate, AuthCredentials, Base
from Src.Repositories.AuthenticationRepository import AuthenticationRepository
from Src.Services.AuthenticationService import AuthenticationService


os.environ["SLEEPSCORER_DB_URL"] = "sqlite:///:memory:"
os.environ["JWT_KEY"] = "sqlite://"

engine = create_engine('sqlite:///:memory:')

Base.metadata.create_all(bind=engine)


from main import app


# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

client = TestClient(app)

def  test_authenticate_function():
    print("ASDsadasd")
    repo = AuthenticationRepository(SessionLocal)
    service = AuthenticationService(repo)
    cemail = 'asdf'
    cname = 'asdfasd'
    cpass = "bassword"
    centre = CentreCreate
    centre.CentreName = cname
    centre.ResponsibleEmail = cemail
    centre.Password = cpass
    service.CreateCentre(centre)
    # Act
    ac = AuthCredentials(CentreName=cname,Password=cpass)
    c = service.AuthenticateCentre(ac)
    # Assert
    payload = jwt.decode(c, os.environ["JWT_KEY"], algorithms=["HS256"])    
    assert payload['centreId'] == 1

