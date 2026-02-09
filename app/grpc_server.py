import grpc
from concurrent import futures
import time
import IDM_pb2
import IDM_pb2_grpc
import datetime
import jwt

SECRET_KEY = "secretul_tau_super_secret"

class IDMServiceServicer(IDM_pb2_grpc.IDMServiceServicer):
    def Login(self, request, context):
        email = request.email
        rol = request.rol
        parola = request.parola
        payload = {
            "email": email,
            "rol":rol,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token_str = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        if isinstance(token_str, bytes):
            token_str = token_str.decode("utf-8")
            return IDM_pb2.LoginResponse(
                success=True,
                token=token_str,
                error=""
            )
        return IDM_pb2.LoginResponse(
            success=True,
            token=token_str,
            error=""
        )
    def Register(self, request, context):
        email = request.email
        rol = request.rol
        parola = request.parola
        payload = {
            "email": email,
            "rol":rol,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token_str = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        if isinstance(token_str, bytes):
            token_str = token_str.decode("utf-8")
            return IDM_pb2.LoginResponse(
                success=True,
                token=token_str,
                error=""
            )
        return IDM_pb2.LoginResponse(
            success=True,
            token=token_str,
            error=""
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    IDM_pb2_grpc.add_IDMServiceServicer_to_server(IDMServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC server pornit pe 127.0.0.1:50051")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == "__main__":
    serve()
