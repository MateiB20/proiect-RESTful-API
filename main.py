from fastapi import FastAPI, HTTPException, status, Response, Request, Depends, Header
from fastapi.security import HTTPBearer
security = HTTPBearer()
import json
import os
from peewee import OperationalError, SqliteDatabase, MySQLDatabase, Model, CharField, IntegerField, ForeignKeyField, CompositeKey, AutoField
from fastapi.responses import JSONResponse
from enum import Enum
from jwt import ExpiredSignatureError, InvalidTokenError


from pymongo import MongoClient
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
import time


import grpc
from concurrent import futures
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
try:
    import IDM_pb2, IDM_pb2_grpc
except ImportError as e:
    print(f"Error importing gRPC stubs: {e}")
    print(f"Current directory appended to path: {current_dir}")
    raise


"""
db = MySQLDatabase(
    'event_manager',
    user='root',
    password='password',
    host='localhost',
    port=3306
)
channel = grpc.insecure_channel('localhost:50051')
client = MongoClient("mongodb://localhost:27017/")
dbmongo = client["event_manager"]
"""

MYSQL_HOST = os.environ.get('MYSQL_HOST', 'mysql') 
MONGO_HOST = os.environ.get('MONGO_HOST', 'mongo')
GRPC_HOST = os.environ.get('GRPC_HOST', 'idm_service') 
GRPC_PORT = os.environ.get('GRPC_PORT', '50051')

db = MySQLDatabase(
    'event_manager',
    user='root',
    password='password',
    host=MYSQL_HOST, 
    port=3306
)

#from clientsrouter.clients import router as clients_router
app = FastAPI(
    title="Event Manager API",
    description="Server RESTful pentru gestionarea evenimentelor",
)

#app.include_router(clients_router, prefix="/api/event-manager/clients")
"""
MAX_RETRIES = 10
RETRY_DELAY = 5

for attempt in range(MAX_RETRIES):
    try:
        db.connect()
        break  
    except OperationalError as e:
        if attempt < MAX_RETRIES - 1:
            db.close() 
            time.sleep(RETRY_DELAY)
        else:
            raise 
"""
channel = grpc.insecure_channel(f'{GRPC_HOST}:{GRPC_PORT}') 
stub = IDM_pb2_grpc.IDMServiceStub(channel)

client = MongoClient(f"mongodb://{MONGO_HOST}:27017/")
dbmongo = client["event_manager"]

blacklistcounters = {}
blacklisttimestamps= {}
blacklist = {}
token_blacklist = {}

stub = IDM_pb2_grpc.IDMServiceStub(channel)



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






import jwt
import secrets
from datetime import datetime, timedelta

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import uuid

SECRET_KEY = "secretul_tau_super_secret"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60
def create_jwt_token(user_id: int, email: str, role: str):
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "ID_OWNER": user_id,  
        "iss": "event_manager_api", 
        "jti": str(uuid.uuid4()),   
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token



def decode_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        jti = payload.get("jti")
        if jti in token_blacklist:
            raise HTTPException(
                status_code=401, 
                detail="Sesiune invalida"
            )
        return payload 
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401)






@app.on_event("startup")
def startup():
    MAX_RETRIES = 10
    RETRY_DELAY = 5
    for attempt in range(MAX_RETRIES):
        try:
            db.connect()
            db.create_tables([Evenimente, Pachete, Bilete, Join_PE, Utilizatori], safe=True)
            print("Successfully connected to MySQL and created tables.")
            break
        except OperationalError as e:
            if attempt < MAX_RETRIES - 1:
                print(f"MySQL connection failed. Retrying in {RETRY_DELAY} seconds... ({attempt+1}/{MAX_RETRIES})")
                if not db.is_closed():
                    db.close() 
                time.sleep(RETRY_DELAY)
            else:
                print(f"FATAL: Could not connect to database after {MAX_RETRIES} attempts: {e}")
                raise

@app.on_event("shutdown")
def shutdown():
    if not db.is_closed():
        db.close()
        print("MySQL connection closed.")



@app.get("/api/event-manager/openapi.json")
def get_openapi_json():
    return JSONResponse(app.openapi())






@app.get("/api/event-manager/events/{id}", summary="Returneaza un eveniment cu id specific")
def get_event(id: int):
    event = Evenimente.get_or_none(Evenimente.ID == id)
    if event:
        response = {
            "data": event.__data__,
            "_links": {
                "self": {"href": f"/api/event-manager/events/{id}"},
                "parent": {"href": "/api/event-manager/events"},
                "packets": {"href":f"/api/event-manager/events/{id}/event-packets"},
                "tickets":{"href":f"/api/event-manager/events/{id}/tickets"}
            }
        }
        return JSONResponse(status_code=200, content=response)
    else:
        raise HTTPException(status_code=404, detail="Evenimentul nu a fost gasit")



@app.get("/api/event-manager/events",  summary="Returneaza un eveniment")
def get_events(idowner:str=None, name: str = None, locatie: str = None, available_tickets: int = None, page: int = None, items_per_page: int = 3, type: str = None):
    query = Evenimente.select()
    if name:
        query = query.where(Evenimente.nume.contains(name))
    if locatie:
        query = query.where(Evenimente.locatie.contains(locatie))
    if available_tickets:
        query = query.where(Evenimente.numarLocuri >= available_tickets)
    if type:
        query = query.where(Evenimente.descriere.contains(type))
    events = [e.__data__ for e in query]
    if page:
        start = (page - 1) * items_per_page
        end = start + items_per_page
        events = events[start:end]
    if events:
        response = {
            "data": events,
            "_links": {
                "self": {"href": "/api/event-manager/events"},
                "parent": {"href": "/api/event-manager"},
                "packets": {"href":f"/api/event-manager/events/{id}/event-packets"},
                "tickets":{"href":f"/api/event-manager/events/{id}/tickets"}
            }
        }
        return JSONResponse(status_code=200, content=response)
    else:
        raise HTTPException(status_code=404, detail="Niciun eveniment nu a fost gasit")



@app.put("/api/event-manager/events", summary="Creaza sau inlocuieste un eveniment", dependencies=[Depends(security)])
def create_event(event: dict, request: Request):
    content_type = request.headers.get("content-type")
    if content_type != "application/json":
        raise HTTPException(status_code=415)
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    user = Utilizatori.get_or_none(Utilizatori.ID == event["ID_OWNER"])
    if not user or not user.rol == "owner-event":
        raise HTTPException(status_code=422, detail="Event Owner invalid")
    if rol != "owner-event":
        raise HTTPException(status_code=401)
    else:
        events = Evenimente.select()
        existing_event = Evenimente.get_or_none(Evenimente.ID == event["ID"])
        if existing_event:
            Evenimente.update(
                ID=event["ID"],
                ID_OWNER=event["ID_OWNER"],
                nume=event["nume"],
                locatie=event["locatie"],
                descriere=event["descriere"],
                numarLocuri=event["numarLocuri"]
            ).where(Evenimente.ID == event["ID"]).execute()
            raise HTTPException(status_code=204)
        Evenimente.create(
            ID=event["ID"],
            ID_OWNER=event["ID_OWNER"],
            nume=event["nume"],
            locatie=event["locatie"],
            descriere=event["descriere"],
            numarLocuri=event["numarLocuri"]
        )
        response = {
            "data": event,
            "_links": {
                "self": {"href": "/api/event-manager/events"},
                "parent": {"href": "/api/event-manager"},
                "packets": {"href":f"/api/event-manager/events/{id}/event-packets"},
                "tickets":{"href":f"/api/event-manager/events/{id}/tickets"}
            }
        }
        return JSONResponse(status_code=201, content=response)



@app.post("/api/event-manager/events", summary="Actualizeaza o resursa container cu un nou eveniment", dependencies=[Depends(security)])
def post_event(event: dict, request: Request):
    if request.headers.get("content-type") != "application/json":
        raise HTTPException(status_code=415)
    events = Evenimente.select()
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    user = Utilizatori.get_or_none(Utilizatori.ID == event["ID_OWNER"])
    if not user or not user.rol == "owner-event":
        raise HTTPException(status_code=422, detail="Event Owner invalid") 
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    email = payload.get("email")
    if rol != "owner-event" or email!= user.email:
        raise HTTPException(status_code=401)
    else:
        if any(e.nume == event["nume"] for e in events):
            raise HTTPException(status_code=422)
        Evenimente.create(
            ID_OWNER=event["ID_OWNER"],
            nume=event["nume"],
            locatie=event["locatie"],
            descriere=event["descriere"],
            numarLocuri=event["numarLocuri"]
        )
        response = {
            "data": event,
            "_links": {
                "self": {"href": "/api/event-manager/events"},
                "parent": {"href": "/api/event-manager"},\
            }
        }
        return JSONResponse(status_code=201, content=response)



@app.delete("/api/event-manager/events/{id}", summary="Sterge un eveniment cu id specific", dependencies=[Depends(security)])
def delete_event(id: int, request: Request):
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    email = payload.get("email")
    event=Evenimente.get_or_none(Evenimente.ID == id)
    user = Utilizatori.get_or_none(Utilizatori.ID == event.ID_OWNER)
    if rol != "owner-event" or user.email != email:
        raise HTTPException(status_code=401)
    else:
        event = Evenimente.get_or_none(Evenimente.ID == id)
        if event:
            eventtemp = event
            event.delete_instance()
            response={
                "data": eventtemp.__data__,
                "_links": {
                    "self": {"href": "/api/event-manager/events"},
                    "parent": {"href": "/api/event-manager"},
                    "packets": {"href":f"/api/event-manager/events/{id}/event-packets"},
                    "tickets":{"href":f"/api/event-manager/events/{id}/tickets"}
                }
            }
            return JSONResponse(status_code=200, content=response)
        else:
            raise HTTPException(status_code=404, detail="Evenimentul nu a fost gasit")








@app.get("/api/event-manager/event-packets", summary="Returneaza un pachet de evenimente")
def get_packets(name: str = None, available_tickets:str=None, locatie: str = None, page: int = None, items_per_page: int = 3, type: str = None):
    query = Pachete.select()
    if name:
        query = query.where(Pachete.nume.contains(name))
    if locatie:
        query = query.where(Pachete.locatie.contains(locatie))
    if available_tickets:
        query = query.where(Pachete.numarLocuri >= available_tickets)
    if type:
        query = query.where(Pachete.descriere.contains(type))
    packets = [p.__data__ for p in query]
    if page:
        start = (page - 1) * items_per_page
        end = start + items_per_page
        packets = packets[start:end]
    if packets:
        response = {
            "data": packets,
            "_links": {
                "self": {"href": "/api/event-manager/event-packets"},
                "parent": {"href": "/api/event-manager"},
                "event": {"href":"/api/event-manager/event-packets/{id}/events"},
                "tickets":{"href":f"/api/event-manager/events/{id}/tickets"}
            }
        }
        return JSONResponse(status_code=200, content=response)
    else:
        raise HTTPException(status_code=404, detail="Niciun pachet de evenimente nu a fost gasit")



@app.get("/api/event-manager/event-packets/{id}", summary="Returneaza un pachet de evenimente cu id specific")
def get_packet(id: int):
    packet = Pachete.get_or_none(Pachete.ID == id)
    if packet:
        response = {
            "data": packet.__data__,
            "_links": {
                "self": {"href": f"/api/event-manager/event-packets/{id}"},
                "parent": {"href": "/api/event-manager"},
                "event": {"href":f"/api/event-manager/event-packets/{id}/events"},
                "tickets":{"href":f"/api/event-manager/event-packets/{id}/tickets"}
            }
        }
        return JSONResponse(status_code=200, content=response)
    else:
        raise HTTPException(status_code=404, detail="Pachetul nu a fost gasit")



@app.put("/api/event-manager/event-packets", summary="Creaza sau inlocuieste un pachet de evenimente", dependencies=[Depends(security)])
def create_packet(packet: dict, request: Request):
    content_type = request.headers.get("content-type")
    if content_type != "application/json":
        raise HTTPException(status_code=415)
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    user = Utilizatori.get_or_none(Utilizatori.ID == packet["ID_OWNER"])
    if not user or not user.rol == "owner-event":
        raise HTTPException(status_code=422, detail="Event Owner invalid")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    email = payload.get("email")
    if rol != "owner-event" or email!= user.email:
        raise HTTPException(status_code=401)
    else:
        pachete = Pachete.select()
        existing_packet = Pachete.get_or_none(Pachete.ID == packet["ID"])
        if existing_packet:
            Pachete.update(
                ID=packet["ID"],
                ID_OWNER=packet["ID_OWNER"],
                nume=packet["nume"],
                locatie=packet["locatie"],
                descriere=packet["descriere"],
                numarLocuri=packet["numarLocuri"]
            ).where(Pachete.ID == packet["ID"]).execute()
            raise HTTPException(status_code=204)
        Pachete.create(
            ID=packet["ID"],
            ID_OWNER=packet["ID_OWNER"],
            nume=packet["nume"],
            locatie=packet["locatie"],
            descriere=packet["descriere"],
            numarLocuri=packet["numarLocuri"]
        )
        response = {
            "data": packet,
            "_links": {
                "self": {"href": "/api/event-manager/event-packets"},
                "parent": {"href": "/api/event-manager"},
                "event": {"href": f"/api/event-manager/event-packets/{packet['ID']}/events"},
                "tickets":{"href":f"/api/event-manager/event-packets/{packet['ID']}/tickets"}
            }
        }
        return JSONResponse(status_code=201, content=response)



@app.post("/api/event-manager/event-packets", summary="Actualizeaza o resursa container cu un nou pachet de evenimente", dependencies=[Depends(security)])
def post_packet(packet: dict, request: Request):
    if request.headers.get("content-type") != "application/json":
        raise HTTPException(status_code=415)
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    user = Utilizatori.get_or_none(Utilizatori.ID == packet.get("ID_OWNER"))
    if not user or not user.rol == "owner-event":
        raise HTTPException(status_code=422, detail="Event Owner invalid")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    email = payload.get("email")
    if rol != "owner-event" or email!= user.email:
        raise HTTPException(status_code=401)
    else:
        pachete = Pachete.select()
        if any(p.nume == packet["nume"] for p in pachete):
            raise HTTPException(status_code=422)
        Pachete.create(
            ID_OWNER=packet["ID_OWNER"],
            nume=packet["nume"],
            locatie=packet["locatie"],
            descriere=packet["descriere"],
            numarLocuri=packet["numarLocuri"]
        )
        response = {
            "data": packet,
            "_links": {
                "self": {"href": "/api/event-manager/event-packets"},
                "parent": {"href": "/api/event-manager"},
                "event": {"href":f"/api/event-manager/event-packets/{id}/events"},
                "tickets":{"href":f"/api/event-manager/event-packets/{id}/tickets"}
            }
        }
        return JSONResponse(status_code=201, content=response)



@app.delete("/api/event-manager/event-packets/{id}", summary="Sterge un pachet de evenimente cu id specific", dependencies=[Depends(security)])
def delete_packet(id: int, request:Request):
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    email = payload.get("email")
    packet= Pachete.get_or_none(Pachete.ID == id)
    user = Utilizatori.get_or_none(Utilizatori.ID == packet.ID_OWNER)
    if rol != "owner-event" or user.email != email:
        raise HTTPException(status_code=401)
    else:
        packet = Pachete.get_or_none(Pachete.ID == id)
        if packet:
            packettemp = packet
            packet.delete_instance()
            response={
                "data": packettemp.__data__,
                "_links": {
                    "self": {"href": "/api/event-manager/event-packets"},
                    "parent": {"href": "/api/event-manager"},
                    "event": {"href":f"/api/event-manager/event-packets/{id}/events"},
                    "tickets":{"href":f"/api/event-manager/event-packets/{id}/tickets"}
                }
            }
            return JSONResponse(status_code=200, content=response)
        else:
            raise HTTPException(status_code=404, detail="Pachetul nu a fost gasit")






@app.get("/api/event-manager/tickets", summary="Returneaza un bilet")
def get_events(request:Request, idowner:str=None, name: str = None, pachetid:int=None, evenimentid:int=None, page: int = None, items_per_page: int = 3):
    query = Bilete.select()
    if pachetid:
        query = query.where(Bilete.PachetID==pachetid)
    if evenimentid:
        query = query.where(Bilete.EvenimentID==evenimentid)
    tickets = [t.__data__ for t in query]
    if page:
        start = (page - 1) * items_per_page
        end = start + items_per_page
        tickets = tickets[start:end]
    if tickets:
        response = {
            "data": tickets,
            "_links": {
                "self": {"href": "/api/event-manager/tickets"},
                "parent": {"href": "/api/event-manager"}
            }
        }
        return JSONResponse(status_code=200, content=response)
    else:
        raise HTTPException(status_code=404, detail="Niciun eveniment nu a fost gasit")



@app.get("/api/event-manager/tickets/{cod}", summary="Returneaza un bilet cu cod specific")
def get_ticket(cod: str):
    ticket = Bilete.get_or_none(Bilete.COD == cod)
    if ticket:
        event = Evenimente.get_or_none(Evenimente.ID == ticket.EvenimentID)
        pachet = Pachete.get_or_none(Pachete.ID == ticket.PachetID)
        links = {
            "self": {"href": f"/api/event-manager/tickets/{cod}"},
            "parent": {"href": "/api/event-manager/tickets"}
        }
        if event and pachet:
            if event.numarLocuri > 0 and pachet.numarLocuri > 0:
                links["buy"] = {
                    "href": f"/api/event-manager/client/ID_CLIENT_AICI/tickets"
                }
        response = {
            "data": ticket.__data__,
            "_links": links
        }
        return JSONResponse(status_code=200, content=response)
    else:
        raise HTTPException(status_code=404, detail="Biletul nu a fost gasit")





@app.put("/api/event-manager/tickets", summary="Creaza sau inlocuieste un bilet", dependencies=[Depends(security)])
def create_ticket(ticket: dict, request: Request): 
    pachet= Pachete.get_or_none(Pachete.ID == ticket["PachetID"])
    event= Evenimente.get_or_none(Evenimente.ID == ticket["EvenimentID"])
    if not event:
        raise HTTPException(status_code=422, detail="Evenimentul asociat biletului nu exista")
    if not pachet:
        raise HTTPException(status_code=422, detail="Pachetul asociat biletului nu exista")
    user = Utilizatori.get_or_none(Utilizatori.ID == pachet.ID_OWNER)
    user2 = Utilizatori.get_or_none(Utilizatori.ID == event.ID_OWNER)
    if user.ID != user2.ID:
        raise HTTPException(status_code=422, detail="Proprietarii pachetului si evenimentului nu coincid")
    if not user or not user.rol == "owner-event":
        raise HTTPException(status_code=422, detail="Event Owner invalid")
    content_type = request.headers.get("content-type")
    if content_type != "application/json":
        raise HTTPException(status_code=415)
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    if rol != "owner-event" or user.email != payload.get("email"):
        raise HTTPException(status_code=401)
    else:
        existing_ticket = Bilete.get_or_none(Bilete.COD == ticket["COD"])
        if existing_ticket:
            Bilete.update(
                COD=ticket["COD"],
                PachetID=ticket["PachetID"],
                EvenimentID=ticket["EvenimentID"]
            ).where(Bilete.COD == ticket["COD"]).execute()
            raise HTTPException(status_code=204)
        Bilete.create(
            COD=ticket["COD"],
            PachetID=ticket["PachetID"],
            EvenimentID=ticket["EvenimentID"]
        )
        response = {
            "data": ticket,
            "_links": {
                "self": {"href": "/api/event-manager/tickets"},
                "parent": {"href": "/api/event-manager"}
            }
        }
        return JSONResponse(status_code=201, content=response)



@app.post("/api/event-manager/tickets", dependencies=[Depends(security)])
def post_ticket(ticket: dict, request: Request):
    pachet= Pachete.get_or_none(Pachete.ID == ticket["PachetID"])
    event= Evenimente.get_or_none(Evenimente.ID == ticket["EvenimentID"])
    if not event:
        raise HTTPException(status_code=422, detail="Evenimentul asociat biletului nu exista")
    if not pachet:
        raise HTTPException(status_code=422, detail="Pachetul asociat biletului nu exista")
    user = Utilizatori.get_or_none(Utilizatori.ID == pachet.ID_OWNER)
    user2 = Utilizatori.get_or_none(Utilizatori.ID == event.ID_OWNER)
    if user.ID != user2.ID:
        raise HTTPException(status_code=422, detail="Proprietarii pachetului si evenimentului nu coincid")
    if not user or not user.rol == "owner-event":
        raise HTTPException(status_code=422, detail="Event Owner invalid")
    if request.headers.get("content-type") != "application/json":
        raise HTTPException(status_code=415)
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    if rol != "owner-event" or user.email != payload.get("email"):
        raise HTTPException(status_code=401)
    else:
        Bilete.create(
            COD=ticket["COD"],
            PachetID=ticket["PachetID"],
            EvenimentID=ticket["EvenimentID"]
        )
        response = {
            "data": ticket,
            "_links": {
                "self": {"href": "/api/event-manager/tickets"},
                "parent": {"href": "/api/event-manager"}
            }
        }
        return JSONResponse(status_code=201, content=response)



@app.delete("/api/event-manager/tickets/{cod}", dependencies=[Depends(security)])
def delete_ticket(cod: str, request: Request):
    ticket = Bilete.get_or_none(Bilete.COD == cod)
    if not ticket:
        raise HTTPException(status_code=404, detail="Biletul nu a fost gasit")
    pachet = Pachete.get_or_none(Pachete.ID == ticket.PachetID)
    if not pachet:
        raise HTTPException(status_code=422, detail="Pachetul asociat biletului nu exista")
    user = Utilizatori.get_or_none(Utilizatori.ID == pachet.ID_OWNER)
    if not user or not user.rol == "owner-event":
        raise HTTPException(status_code=422, detail="Event Owner invalid")
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    if rol != "owner-event":
        raise HTTPException(status_code=401)
    else:
        ticket = Bilete.get_or_none(Bilete.COD == cod)
        if ticket:
            tickettemp = ticket
            ticket.delete_instance()
            response={
                "data": tickettemp.__data__,
                "_links": {
                    "self": {"href": "/api/event-manager/tickets"},
                    "parent": {"href": "/api/event-manager"}
                }
            }
            return JSONResponse(status_code=200, content=response)
        else:
            raise HTTPException(status_code=404, detail="Biletul nu a fost gasit")






@app.get("/api/event-manager/join-pe", summary="Returnează un join pachet-eveniment")
def get_join_pe(pachetid:int=None, evenimentid:int=None, available_tickets: int = None,  page: int = None, items_per_page: int = 3, type: str = None):
    joins = [j.__data__ for j in Join_PE.select()]
    query = Join_PE.select()
    if evenimentid:
        query = query.where(Join_PE.EvenimentID==evenimentid)
    if pachetid:
        query = query.where(Join_PE.PachetID==pachetid )
    if available_tickets:
        query = query.where(Join_PE.numarLocuri >= available_tickets)
    joins = [j.__data__ for j in query]
    if page:
        start = (page - 1) * items_per_page
        end = start + items_per_page
        joins = joins[start:end]
    if joins:
        response = {
            "data": joins,
            "_links": {
                "self": {"href": "/api/event-manager/join-pe"},
                "parent": {"href": "/api/event-manager"}
            }
        }
        return JSONResponse(status_code=200, content=response)
    else:
        raise HTTPException(status_code=404, detail="Niciun join nu a fost gasit")



@app.get("/api/event-manager/join-pe/{id}", summary="Returnează un join pachet-eveniment cu id specific")
def get_event(id: int):
    join = Join_PE.get_or_none(Join_PE.id == id)
    if join:
        response = {
            "data": join.__data__,
            "_links": {
                "self": {"href": f"/api/event-manager/join-pe/{id}"},
                "parent": {"href": "/api/event-manager/join-pe"}
            }
        }
        return JSONResponse(status_code=200, content=response)
    else:
        raise HTTPException(status_code=404, detail="Join nu a fost gasit")



@app.put("/api/event-manager/event/{eid}/event-packets/{pid}", summary="Creaza sau inlocuieste un join pachet-eveniment")
def create_join_pe(eid:str, pid:str, request: Request):
    if not pid or not eid:
        raise HTTPException(status_code=422)
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    event= Evenimente.get_or_none(Evenimente.ID == eid)
    packet= Pachete.get_or_none(Pachete.ID == pid)
    if not event or not packet or not event.ID_OWNER == packet.ID_OWNER:
        raise HTTPException(status_code=422, detail="Evenimentul sau pachetul nu exista sau nu au acelasi owner")
    user = Utilizatori.get_or_none(Utilizatori.email == payload.get("email"))
    if not user or not user.rol == "owner-event":
        raise HTTPException(status_code=422, detail="Event Owner invalid")
    if rol != "owner-event":
        raise HTTPException(status_code=401)
    else:
        query = Evenimente.select()
        query = query.where(Evenimente.ID==eid)
        query2= Pachete.select()
        query2 = query2.where(Pachete.ID==pid)
        event= query.first()
        packet= query2.first()
        if not event or not packet:
            raise HTTPException(status_code=422, detail="Evenimentul sau pachetul nu exista")
        if event.numarLocuri < packet.numarLocuri:
            Pachete.update(numarLocuri=event.numarLocuri).where(Pachete.ID == packet.ID).execute()
        join=Join_PE.create(
            PachetID=pid,
            EvenimentID=eid,
        )
        response = {
            "data": join.__data__,
            "_links": {
                "self": {"href": "/api/event-manager/event/{eid}/pachet/{pid}"},
                "parent": {"href": "/api/event-manager/event"}
            }
        }
        return JSONResponse(status_code=201, content=response)
    
    
    
@app.post("/api/event-manager/event/{eid}/event-packets/{pid}", summary="Actualizeaza o resursa container cu un nou join pachet-eveniment")
def post_join_pe(eid:str, pid:str,request: Request):
    if not pid or not eid:
        raise HTTPException(status_code=422)
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    event= Evenimente.get_or_none(Evenimente.ID == eid)
    packet= Pachete.get_or_none(Pachete.ID == pid)
    if not event or not packet or not event.ID_OWNER == packet.ID_OWNER:
        raise HTTPException(status_code=422, detail="Evenimentul sau pachetul nu exista sau nu au acelasi owner")
    user = Utilizatori.get_or_none(Utilizatori.email == payload.get("email"))
    if not user or not user.rol == "owner-event":
        raise HTTPException(status_code=422, detail="Event Owner invalid")
    if rol != "owner-event" or user.email != payload.get("email"):
        raise HTTPException(status_code=401)
    else:
        query = Evenimente.select()
        query = query.where(Evenimente.ID==eid)
        query2= Pachete.select()
        query2 = query2.where(Pachete.ID==pid)
        event= query.first()
        packet= query2.first()
        if not event or not packet:
            raise HTTPException(status_code=422, detail="Evenimentul sau pachetul nu exista")
        if event.numarLocuri < packet.numarLocuri:
            Pachete.update(numarLocuri=event.numarLocuri).where(Pachete.ID == packet.ID).execute()
        join=Join_PE.create(
            PachetID=pid,
            EvenimentID=eid,
        )
        response = {
            "data": join.__data__,
            "_links": {
                "self": {"href": "/api/event-manager/event/{eid}/pachet/{pid}"},
                "parent": {"href": "/api/event-manager/event"}
            }
        }
        return JSONResponse(status_code=201, content=response)



"""
@app.delete("/api/event-manager/join-pe/{id}", summary="Sterge un join pachet-eveniment cu id specific")
def delete_event(id: int, request: Request):
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    if rol != "owner-event":
        raise HTTPException(status_code=401)
    else:
        join = Join_PE.get_or_none(Join_PE.id == id)
        if join:
            jointemp = join
            join.delete_instance()
            response={
                "data": jointemp.__data__,
                "_links": {
                    "self": {"href": "/api/event-manager/join-pe"},
                    "parent": {"href": "/api/event-manager"}
                }
            }
            return JSONResponse(status_code=200, content=response)
        else:
            raise HTTPException(status_code=404, detail="Join nu a fost gasit")
"""





@app.get("/api/event-manager/events/{id}/event-packets", summary="Returneaza pachetele de evenimente cu un eveniment")
def get_packet_events(id: int):
    if event:
        query = Join_PE.select().where(Join_PE.EvenimentID == id)
        events = [Pachete.get_or_none(Pachete.ID == e.PachetID).__data__ for e in query]
        response = {
            "data": event.__data__,
            "_links": {
                "self": {"href": f"/api/event-manager/events/{id}/event-packets"},
                "parent": {"href": f"/api/event-manager/events/{id}"}
            },
            "events": events
        }
        return JSONResponse(status_code=200, content=response)
    raise HTTPException(status_code=404, detail="Pachetul nu a fost gasit")






@app.get("/api/event-manager/event-packets/{id}/events", summary="Returneaza evenimentele dintr-un pachet de evenimente")
def get_packet_events(id: int):
    packet = Pachete.get_or_none(Pachete.ID == id)
    if packet:
        query = Join_PE.select().where(Join_PE.PachetID == id)
        events = [Evenimente.get_or_none(Evenimente.ID == e.EvenimentID).__data__ for e in query]
        response = {
            "data": packet.__data__,
            "_links": {
                "self": {"href": f"/api/event-manager/event-packets/{id}/events"},
                "parent": {"href": f"/api/event-manager/event-packets/{id}"}
            },
            "events": events
        }
        return JSONResponse(status_code=200, content=response)
    raise HTTPException(status_code=404, detail="Evenimentul nu a fost gasit")






@app.get("/api/event-manager/events/{id}/tickets/{cod}", summary="Returneaza un bilet la un eveniment")
def get_event_ticket(id: int, cod: str):
    ticket = Bilete.get_or_none((Bilete.EvenimentID == id) & (Bilete.COD == cod))
    if ticket:
        response = {
            "data": ticket.__data__,
            "_links": {
                "self": {"href": f"/api/event-manager/events/{id}/tickets/{cod}"},
                "parent": {"href": f"/api/event-manager/events/{id}/tickets"}
            }
        }
        return JSONResponse(status_code=200, content=response)
    raise HTTPException(status_code=404, detail="Biletul nu a fost gasit")






@app.get("/api/event-manager/event-packets/{id}/tickets/{cod}", summary="Returneaza un bilet dintr-un pachet de evenimente")
def get_packet_ticket(id: int, cod: str):
    ticket = Bilete.get_or_none((Bilete.PachetID == id) & (Bilete.COD == cod))
    if ticket:
        response = {
            "data": ticket.__data__,
            "_links": {
                "self": {"href": f"/api/event-manager/event-packets/{id}/tickets/{cod}"},
                "parent": {"href": f"/api/event-manager/event-packets/{id}/tickets"}
            }
        }
        return JSONResponse(status_code=200, content=response)
    raise HTTPException(status_code=404, detail="Biletul nu a fost gasit")






"""
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



@app.get("/api/event-manager/clients/{id}", summary="Returneaza un client cu id specific")
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



@app.get("/api/event-manager/clients", summary="Returneaza un client")
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



@app.put("/api/event-manager/clients", summary="Creaza sau inlocuieste un client existent", dependencies=[Depends(security)])
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

@app.put("/api/event-manager/client/{id}/tickets", summary="Returneaza biletele")
def add_ticket_to_client(id: str, ticket: dict, request: Request):
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
    if rol != "client" or email != client["email"]:
        raise HTTPException(status_code=401)
    else:
        ticket_obj = Bilete.get_or_none(Bilete.COD == ticket["COD"])
        if not ticket_obj:
            raise HTTPException(status_code=422, detail="Biletul nu exista")
        if ticket["COD"] in client.get("lista_bilete", []):
            raise HTTPException(status_code=422, detail="Biletul este deja asociat cu acest client")
        client["lista_bilete"].append(ticket["COD"])
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
"""





@app.get("/api/event-manager/users", summary="Returneaza un utilizator")
def get_users(request: Request):
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    if rol == "admin":
        query = Utilizatori.select()
        users = [u.__data__ for u in query]
        response = {
            "data": users,
            "_links": {
                "self": {"href": "/api/event-manager/users"},
                "parent": {"href": "/api/event-manager"}
            }
        }
        return JSONResponse(status_code=200, content=response)
    else:
        payload = decode_jwt(token)
        user_email = payload.get("email")
        if not user_email:
            raise HTTPException(status_code=401, detail="/api/event-manager/login")
        query = Utilizatori.select().where(Utilizatori.email == user_email)
        users = [u.__data__ for u in query]
        if users:
            response = {
                "data": users,
                "_links": {
                    "self": {"href": "/api/event-manager/users"},
                    "parent": {"href": "/api/event-manager"}
                }
            }
            return JSONResponse(status_code=200, content=response)
        else:
            raise HTTPException(status_code=404, detail="Utilizatorul nu exista")



@app.post("/api/event-manager/register", summary="Creeaza un utilizator nou")
def post_user(user: dict, request: Request):
    if request.headers.get("content-type") != "application/json":
        raise HTTPException(status_code=415)
    rol=user["rol"]
    if rol!="admin" and rol!="owner-event" and rol!="client":
        raise HTTPException(status_code=422, detail="Rol invalid")
    existing_user = Utilizatori.get_or_none(Utilizatori.email == user["email"])
    if existing_user:
        raise HTTPException(status_code=422, detail="Utilizator cu email-ul dat exista deja")
    else:
        Utilizatori.create(
            email=user["email"],
            parola=user["parola"],
            rol=user["rol"]
        )
        grpc_request = IDM_pb2.LoginRequest(
            email=user["email"],
            parola=user["parola"],
            rol=user["rol"]
        )
        response1 = stub.Login(grpc_request)
        response = {
            "data": user,
            "_links": {
                "self": {"href": "/api/event-manager/register"},
                "parent": {"href": "/api/event-manager"}
            },
            "token": response1.token
        }
        return JSONResponse(status_code=201, content=response)



@app.delete("/api/event-manager/users/{id}", summary="Sterge un utilizator cu id specific")
def delete_event(id: int, request: Request):
    if request.headers.get("authorization") is None:
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="/api/event-manager/login")
    token = auth.replace("Bearer ", "").strip()
    payload = decode_jwt(token)
    rol = payload.get("rol")
    if rol != "admin":
        raise HTTPException(status_code=401)
    user = Utilizatori.get_or_none(Utilizatori.ID == id)
    if user:
        usertemp = user
        user.delete_instance()
        response={
            "data": usertemp.__data__,
            "_links": {
                "self": {"href": "/api/event-manager/users"},
                "parent": {"href": "/api/event-manager"},
            }
        }
        return JSONResponse(status_code=200, content=response)
    else:
        raise HTTPException(status_code=404, detail="Utilizatorul nu a fost gasit")



@app.post("/api/event-manager/login", summary="Autentifica un utilizator")
def post_user(user: dict, request: Request):
    if request.headers.get("content-type") != "application/json":
        raise HTTPException(status_code=415)
    existing_user = Utilizatori.get_or_none((Utilizatori.email == user["email"]) & (Utilizatori.parola == user["parola"]))
    existing_user_email= Utilizatori.get_or_none(Utilizatori.email == user["email"])
    if existing_user:
        grpc_request = IDM_pb2.LoginRequest(
            email=user["email"],
            parola=user["parola"],
            rol=user["rol"]
        )
        response1 = stub.Login(grpc_request)
        response = {
            "data": user,
            "_links": {
                "self": {"href": "/api/event-manager/login"},
                "parent": {"href": "/api/event-manager"}
            },
            "token": response1.token
        }
        return JSONResponse(status_code=200, content=response)
    if existing_user_email:
        if existing_user_email.email in blacklisttimestamps:
            now=time.time()
            if now - blacklisttimestamps[existing_user_email.email] >= 60:
                blacklistcounters[existing_user_email.email] = 0  
                del blacklisttimestamps[existing_user_email.email]
        if not blacklistcounters.get(existing_user_email.email):
            blacklistcounters[existing_user_email.email]=1
        elif blacklistcounters[existing_user_email.email]<5:
            blacklistcounters[existing_user_email.email]+=1
        if blacklistcounters[existing_user_email.email]>=5:
            blacklisttimestamps[existing_user_email.email]=time.time()
            raise HTTPException(status_code=403, detail="Cont blocat din cauza tentativelor multiple de autentificare esuate")
    raise HTTPException(status_code=401, detail="Email sau parola incorecta")



@app.post("/api/event-manager/logout")
async def logout(user:dict, request: Request):
    auth = request.headers.get("authorization")
    token = auth.replace("Bearer ", "").strip()
    payload = jwt.decode(token)
    jti = payload.get("jti")
    existing_user_email= Utilizatori.get_or_none(Utilizatori.email == user["email"])
    token_blacklist[jti] = True 
    return JSONResponse(status_code=200)


