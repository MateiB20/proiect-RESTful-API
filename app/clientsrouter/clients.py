from fastapi import APIRouter, FastAPI, HTTPException, status, Response, Request, Depends, Header
from fastapi.security import HTTPBearer
security = HTTPBearer()
import json
import os
from app.databases.dbs import db
from peewee import SqliteDatabase, MySQLDatabase, Model, CharField, IntegerField, ForeignKeyField, CompositeKey, AutoField
from fastapi.responses import JSONResponse
from app.databases.mongo_db import mongo_db
from enum import Enum
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError


from pymongo import MongoClient
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
db = MySQLDatabase(
    'event_manager',
    user='root',
    password='password',
    host='localhost',
    port=3306
)

class SQLBaseModel(Model):
    class Meta:
        database = db

class Evenimente(SQLBaseModel):
    ID = AutoField(primary_key=True)
    ID_OWNER = IntegerField()
    nume = CharField()
    locatie = CharField()
    descriere = CharField()
    numarLocuri = IntegerField()



class Pachete(SQLBaseModel):
    ID = AutoField(primary_key=True)
    ID_OWNER = IntegerField()
    nume = CharField()
    locatie = CharField()
    descriere = CharField()
    numarLocuri = IntegerField()



class Bilete(SQLBaseModel):
    COD = CharField(primary_key=True)
    PachetID = IntegerField()
    EvenimentID = IntegerField()



class Join_PE(SQLBaseModel):
    PachetID = IntegerField()
    EvenimentID = IntegerField()






class RoluriEnum(str, Enum):
    ADMIN = "administrator aplicatie"
    OWNER = "owner-event"
    CLIENT = "client"



class Utilizatori(SQLBaseModel):
    ID = AutoField(primary_key=True)
    email = CharField(unique=True)
    parola = CharField()
    rol = CharField(choices=[(role.value, role.value) for role in RoluriEnum])

SECRET_KEY = "secretul_tau_super_secret"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60
def create_jwt_token(user_id: int, email: str, role: str):
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "ID_OWNER": user_id,  
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token



def decode_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload 
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401)

import grpc
from concurrent import futures
import sys
import os
router = APIRouter()
client = MongoClient("mongodb://localhost:27017/")
dbmongo = client["event_manager"]

class SocialMediaLink(BaseModel):
    link: str
    public: Optional[bool] = True



class PrenumeNume(BaseModel):
    value: str
    public: Optional[bool] = True



class ClientModel(BaseModel):
    id: str = Field(None, alias="_id")
    email: EmailStr
    prenume_nume: Optional[PrenumeNume] = None
    social_media_links: Optional[List[SocialMediaLink]] = []
    lista_bilete: List[str] = []


db = SqliteDatabase("event_manager.db")
db.connect()
db.create_tables([Utilizatori])
db.create_tables([Evenimente, Pachete, Bilete, Join_PE, Utilizatori], safe=True)

@router.post("", summary="Creeaza un client nou", dependencies=[Depends(security)])
def post_client(client: ClientModel, request: Request):
    if request.headers.get("content-type") != "application/json":
        raise HTTPException(status_code=415)
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    if rol != "admin":
        raise HTTPException(status_code=401)
    else:
        user = Utilizatori.get_or_none(Utilizatori.email == client.email)
        if not user:
            raise HTTPException(status_code=422, detail="Nu exista utilizator asociat cu acest email")
        collection = dbmongo["clients"]
        existing_client = collection.find_one({"_id": client.id})
        if existing_client:
            raise HTTPException(status_code=422)
        tickets=Bilete.select()
        for bilet in client.lista_bilete:
            if not any(b.COD == bilet for b in tickets):
                raise HTTPException(status_code=422, detail=f"Biletul cu codul '{bilet}' nu exista")
            else:
                bilet_obj = Bilete.get_or_none(Bilete.COD == bilet)
                event = Evenimente.get_or_none(Evenimente.ID == bilet_obj.EvenimentID)
                Evenimente.update(numarLocuri = event.numarLocuri - 1).where(Evenimente.ID == event.ID).execute()
                packet = Pachete.get_or_none(Pachete.ID == bilet_obj.PachetID)
                Pachete.update(numarLocuri = packet.numarLocuri - 1).where(Pachete.ID == packet.ID).execute()
        client_dict = client.dict(by_alias=True)
        collection.insert_one(client_dict)
        response = {
            "data": client_dict,
            "_links": {
                "self": {"href": "/api/event-manager/clients"},
                "parent": {"href": "/api/event-manager"}
            }
        }   
        return JSONResponse(status_code=201, content=response)



@router.get("/{id}", summary="Returneaza un client cu id specific")
def get_client(id: str, request: Request):
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    if rol != "admin":
        raise HTTPException(status_code=401)
    else:
        collection = dbmongo["clients"]
        client = collection.find_one({"_id": id})
        tickets=Bilete.select()
        events=[]
        for bilet in client.get("lista_bilete", []):
            bilet_events=Bilete.get_or_none(Bilete.COD==bilet)
            if bilet_events:
                eveniment=Evenimente.get_or_none(Evenimente.ID==bilet_events.EvenimentID)
                if eveniment and eveniment not in events:
                    events.append(eveniment)
        client["events"]= [e.__data__ for e in events]
        if user=="admin" and clients:
            response = {
                "data": clients,
                "_links": {
                    "self": {"href": "/api/event-manager/clients"},
                    "parent": {"href": "/api/event-manager"}
                }
            }
            return JSONResponse(status_code=200, content=response)
        elif clients:
            filtered_clients = []
            for client in clients:
                filtered = {}
                for k, v in client.items():
                    if isinstance(v, dict) and "public" in v:
                        if v["public"]:
                            filtered[k] = v["value"]
                    elif isinstance(v, list):
                        filtered_links = []
                        for link in v:
                            if isinstance(link, dict) and link.get("public", True):
                                filtered_links.append(link)
                            if filtered_links:
                                filtered[k] = filtered_links
                    else:
                        filtered[k] = v
                filtered_clients.append(filtered)
            response = {
                "data": filtered_clients,
                "_links": {
                    "self": {"href": "/api/event-manager/clients"},
                    "parent": {"href": "/api/event-manager"}
                }
            }
            return JSONResponse(status_code=200, content=response)
        else:
            raise HTTPException(status_code=404, detail="Clientul nu a fost gasit")



@router.get("", summary="Returneaza un client")
def get_client(request: Request, email: str = None, prenume_nume: str = None, social_link:str=None, page: int = None, items_per_page: int = 3):
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    if rol != "admin":
        raise HTTPException(status_code=401)
    else:
        collection = dbmongo["clients"]
        query = {}
        if prenume_nume:
            query["prenume_nume"] = {"$regex": f"^{prenume_nume}$", "$options": "i"}
        if email:
            query["email"] = email
        if social_link:
            query["social_media_links"] = social_link
        clients_cursor = collection.find(query)
        clients = list(clients_cursor)
        if page:
            start = (page - 1) * items_per_page
            end = start + items_per_page
            clients = clients[start:end]
        tickets=Bilete.select()
        events=[]
        for client in clients:
            for bilet in client.get("lista_bilete", []):
                bilet_events=Bilete.get_or_none(Bilete.COD==bilet)
                if bilet_events:
                    eveniment=Evenimente.get_or_none(Evenimente.ID==bilet_events.EvenimentID)
                    if eveniment and eveniment not in events:
                        events.append(eveniment)
            client["events"]= [e.__data__ for e in events]
            events=[]
        if clients:
            response = {
                "data": clients,
                "_links": {
                    "self": {"href": "/api/event-manager/clients"},
                    "parent": {"href": "/api/event-manager"}
                }
            }
            return JSONResponse(status_code=200, content=response)
        else:
            raise HTTPException(status_code=404, detail="Niciun client nu a fost gasit")



@router.put("", summary="Creaza sau inlocuieste un client existent", dependencies=[Depends(security)])
def put_client(client: ClientModel, request: Request):
    if request.headers.get("content-type") != "application/json":
        raise HTTPException(status_code=415)
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    if rol != "admin":
        raise HTTPException(status_code=401)
    else:
        user = Utilizatori.get_or_none(Utilizatori.email == client.email)
        if not user:
            raise HTTPException(status_code=422, detail="Nu exista utilizator asociat cu acest email")
        tickets=Bilete.select()
        for bilet in client.lista_bilete:
            if not any(b.COD == bilet for b in tickets):
                raise HTTPException(status_code=422, detail=f"Biletul cu codul '{bilet}' nu exista")
        events=[]
        all_events=Evenimente.select()
        for bilet in client.lista_bilete:
            bilet_obj=Bilete.get_or_none(Bilete.COD==bilet)
            if bilet_obj:
                eveniment=Evenimente.get_or_none(Evenimente.ID==bilet_obj.EvenimentID)
                if eveniment and eveniment not in events:
                    events.append(eveniment)
                packet = Pachete.get_or_none(Pachete.ID == bilet_obj.PachetID)
                Pachete.update(numarLocuri = packet.numarLocuri - 1).where(Pachete.ID == packet.ID).execute()
        for event in events:
            Evenimente.update(numarLocuri = event.numarLocuri - 1).where(Evenimente.ID == event.ID).execute()
        collection = dbmongo["clients"]
        existing_client = collection.find_one({"_id": client.id})
        client_dict = client.dict(by_alias=True)
        if existing_client:
            collection.replace_one({"_id": client.id}, client_dict)
            raise HTTPException(status_code=204)
        collection.insert_one(client_dict)
        response = {
            "data": client_dict,
            "_links": {
                "self": {"href": "/api/event-manager/clients"},
                "parent": {"href": "/api/event-manager"}
            }
        }
        return JSONResponse(status_code=201, content=response)



@router.delete("/{id}", summary="Sterge un client cu id specific", dependencies=[Depends(security)])
def delete_client(id: str, request: Request):
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    if rol != "admin":
        raise HTTPException(status_code=401)
    else:
        collection = dbmongo["clients"]
        existing_client = collection.find_one({"_id": id})
        if existing_client:
            collection.delete_one({"_id": id})
            response={
                "data": existing_client,
                "_links": {
                    "self": {"href": "/api/event-manager/clients"},
                    "parent": {"href": "/api/event-manager"}
                }
            }
            return JSONResponse(status_code=200, content=response)
        else:
            raise HTTPException(status_code=404, detail="Clientul nu a fost gasit")