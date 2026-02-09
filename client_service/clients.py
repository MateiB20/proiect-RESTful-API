from fastapi import FastAPI, HTTPException, status, Response, Request, Depends, Header
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import os
import json
import jwt

from pymongo import MongoClient
from peewee import MySQLDatabase, Model, CharField, IntegerField, ForeignKeyField, CompositeKey, AutoField, IntegrityError

MYSQL_HOST = os.environ.get('MYSQL_HOST', 'mysql')
MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'password')
MYSQL_DB = os.environ.get('MYSQL_DB', 'event_manager')

MONGO_HOST = os.environ.get('MONGO_HOST', 'mongo')
MONGO_USER = os.environ.get('MONGO_INITDB_ROOT_USERNAME', 'root') 
MONGO_PASSWORD = os.environ.get('MONGO_INITDB_ROOT_PASSWORD', 'password')
db = MySQLDatabase(
    MYSQL_DB,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    host=MYSQL_HOST,
    port=3306
)

client_mongo = MongoClient(f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:27017/")
dbmongo = client_mongo["event_manager"]
collection = dbmongo["clients"]

class PeeweeBaseModel(Model):
    class Meta:
        database = db

class Evenimente(PeeweeBaseModel):
    ID = AutoField(primary_key=True)
    ID_OWNER = IntegerField()
    nume = CharField()
    locatie = CharField()
    descriere = CharField()
    numarLocuri = IntegerField()

class Pachete(PeeweeBaseModel):
    ID = AutoField(primary_key=True)
    ID_OWNER = IntegerField()
    nume = CharField()
    locatie = CharField()
    descriere = CharField()
    numarLocuri = IntegerField()

class Bilete(PeeweeBaseModel):
    COD = CharField(primary_key=True)
    PachetID = IntegerField()
    EvenimentID = IntegerField()

class Utilizatori(PeeweeBaseModel):
    ID = AutoField()
    email = CharField(max_length=255, unique=True)
    rol = CharField(max_length=50) 

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

SECRET_KEY = "secretul_tau_super_secret" 
ALGORITHM = "HS256"

def decode_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload 
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirat")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalid")

app = FastAPI(
    title="Client Manager API",
    description="Microserviciu RESTful pentru gestionarea clientilor (MongoDB si SQL)",
)
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
security = HTTPBearer()

@app.on_event("startup")
def startup():
    db.connect()
    db.create_tables([Evenimente, Pachete, Bilete, Utilizatori])

@app.on_event("shutdown")
def shutdown():
    if not db.is_closed():
        db.close()

@app.post("/api/event-manager/clients", summary="Creeaza un client nou", dependencies=[Depends(security)])
def post_client(client: ClientModel, request: Request):
    if request.headers.get("content-type") != "application/json":
        raise HTTPException(status_code=415)
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    user = Utilizatori.get_or_none(Utilizatori.email == client.email)
    if not user:
        raise HTTPException(status_code=422, detail="Nu exista utilizator asociat cu acest email")
    collection = dbmongo["clients"]
    existing_client = collection.find_one({"email": client.email})
    if existing_client:
        raise HTTPException(status_code=422)
    for cod_bilet in client.lista_bilete:
        bilet_obj = Bilete.get_or_none(Bilete.COD == cod_bilet)
        if not bilet_obj:
            raise HTTPException(status_code=422, detail=f"Biletul cu codul '{cod_bilet}' nu exista")
        Evenimente.update(numarLocuri = Evenimente.numarLocuri - 1).where(Evenimente.ID == bilet_obj.EvenimentID).execute()
        if bilet_obj.PachetID:
            Pachete.update(numarLocuri = Pachete.numarLocuri - 1).where(Pachete.ID == bilet_obj.PachetID).execute()
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



@app.get("/api/event-manager/clients/email", summary="Returneaza id-ul unui client cu email specific")
def get_client_id(email:str, request: Request):
    collection = dbmongo["clients"]
    client=collection.find_one({"email": email.strip()})
    if client:
        client_id_str = str(client["_id"])
        response = {
            "data": client_id_str,
            "_links": {
                "self": {"href": "/api/event-manager/clients"},
                "parent": {"href": "/api/event-manager"}
            }
        }
        return JSONResponse(status_code=200, content=response)
    else:
        raise HTTPException(status_code=404, detail="Clientul nu a fost gasit")



@app.get("/api/event-manager/clients/{id}", summary="Returneaza un client cu id specific")
def get_client(id: str, request: Request):
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    client=collection.find_one({"_id": id})
    if not client:
        raise HTTPException(status_code=404, detail="Clientul nu a fost gasit")
    response = {
        "data": client,
        "_links": {
            "self": {"href": "/api/event-manager/clients"},
            "parent": {"href": "/api/event-manager"}
        }
    }
    return JSONResponse(status_code=200, content=response)



@app.get("/api/event-manager/clients")
def get_clients(request: Request, email: str = None):
    auth = request.headers.get("authorization")
    if not auth: 
        raise HTTPException(status_code=401)
    token = auth.replace("Bearer ", "")
    payload = decode_jwt(token)
    collection = dbmongo["clients"]
    query = {"email": email} if email else {}
    clients = collection.find(query)
    clients = list(clients)  
    for c in clients:
        c["_id"] = str(c["_id"])  
        events_list = []
        for cod in c.get("lista_bilete", []):
            b = Bilete.get_or_none(Bilete.COD == cod)
            if b:
                e = Evenimente.get_or_none(Evenimente.ID == b.EvenimentID)
                if e: 
                    events_list.append(e.nume)
        c["events_names"] = events_list
    response = {
        "data": clients,
        "_links": {
            "self": {"href": "/api/event-manager/clients"},
            "parent": {"href": "/api/event-manager"}
        }
    }
    return JSONResponse(status_code=200, content=response)




@app.put("/api/event-manager/clients", summary="Creaza sau inlocuieste un client existent", dependencies=[Depends(security)])
def put_client(client: ClientModel, request: Request):
    if not request.headers.get("content-type", "").startswith("application/json"):
        raise HTTPException(status_code=415)
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    user = Utilizatori.get_or_none(Utilizatori.email == client.email)
    if not user:
        raise HTTPException(status_code=422, detail="Nu exista utilizator asociat cu acest email")
    bilete_objs = []
    for cod_bilet in client.lista_bilete:
        bilet_obj = Bilete.get_or_none(Bilete.COD == cod_bilet)
        if not bilet_obj:
            raise HTTPException(status_code=422, detail=f"Biletul cu codul '{cod_bilet}' nu exista")
        bilete_objs.append(bilet_obj)
    events = []
    packets = []
    for b in bilete_objs:
        if b.EvenimentID not in events:
            events.append(b.EvenimentID)
        if b.PachetID and b.PachetID not in packets:
            packets.append(b.PachetID)
    with db.atomic():
        for ev_id in events:
            Evenimente.update(
                numarLocuri=Evenimente.numarLocuri - 1
            ).where(Evenimente.ID == ev_id).execute()
        for p_id in packets:
            Pachete.update(
                numarLocuri=Pachete.numarLocuri - 1
            ).where(Pachete.ID == p_id).execute()
    collection = dbmongo["clients"]
    client_dict = client.dict(by_alias=True)
    existing_client = collection.find_one({"email": client.email})
    if existing_client:
        collection.replace_one({"email": client.email}, client_dict)
        return Response(status_code=204)
    collection.insert_one(client_dict)
    response = {
        "data": client_dict,
        "_links": {
            "self": {"href": "/api/event-manager/clients"},
            "parent": {"href": "/api/event-manager"}
        }
    }
    return JSONResponse(status_code=201, content=response)




@app.delete("/api/event-manager/clients/{id}", summary="Sterge un client cu id specific", dependencies=[Depends(security)])
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



@app.put("/api/event-manager/clients/{id}/tickets/{cod}", summary="Adauga la client biletele")
def add_ticket_to_client(id: str, cod:str, request: Request):
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    email= payload.get("email")
    collection = dbmongo["clients"]
    client=collection.find_one({"_id": id})
    if not client:
        raise HTTPException(status_code=404, detail="Clientul nu a fost gasit")
    print("Email din token:", email)
    print("Email din client:", client.get("email"))
    if email != client.get("email"):
        raise HTTPException(status_code=401)
    else:
        ticket_obj = Bilete.get_or_none(Bilete.COD == cod)
        if not ticket_obj:
            raise HTTPException(status_code=422, detail="Biletul nu exista")
        if ticket_obj.COD in client.get("lista_bilete", []):
            raise HTTPException(status_code=422, detail="Biletul este deja asociat cu acest client")
        client["lista_bilete"].append(ticket_obj.COD)
        collection.replace_one({"_id": id}, client)
        event = Evenimente.get_or_none(Evenimente.ID == ticket_obj.EvenimentID)
        if event:
            if event.numarLocuri <= 0:
                raise HTTPException(status_code=422, detail="Nu mai sunt locuri disponibile la acest eveniment")
            Evenimente.update(numarLocuri = event.numarLocuri - 1).where(Evenimente.ID == event.ID).execute()

        packet = Pachete.get_or_none(Pachete.ID == ticket_obj.PachetID)
        if packet:
            if packet.numarLocuri <= 0:
                raise HTTPException(status_code=422, detail="Nu mai sunt locuri disponibile în acest pachet")
            Pachete.update(numarLocuri = packet.numarLocuri - 1).where(Pachete.ID == packet.ID).execute()
        response = {
            "data": client,
            "_links": {
                "self": {"href": f"/api/event-manager/client/{id}/tickets"},
                "parent": {"href": f"/api/event-manager/clients/{id}"}
            }
        }
        return JSONResponse(status_code=200, content=response)