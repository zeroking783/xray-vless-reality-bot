import grpc
from app import app

from ..proto import xray_pb2
from ..proto import xray_pb2_grpc
import utils


def send_grpc_request(server_id, ip, method, **kwargs):
    if not check_tls(server_id, ip):
        sys.exit(f"Не удалось проверить сертификат или не удалось создать его")
    
    with open(f"servers_certificates/{ip}.crt", "r") as f:
        certificate = f.read()
    with open(f"servers_certificates/{ip}.key", "r") as f:
        private_key = f.read()
    
    credentials = grpc.ssl_channel_credentials(
        certificate_chain=certificate.encode(),
        private_key=private_key.encode()
    )

    with grpc.secure_channel(f"{ip}:50051", credentials) as channel:
        stub = xray_pb2_grpc.XrayClientsServiceStub(channel)

        if method == "AddClient":
            response = stub.AddClient(xray_pb2.ClientIdRequest(name=kwargs["client_id"]))
            print(f"Received response: UUID={response.uuid}, Short ID={response.shortids}")
        if method == "DeleteClient":
            response = stub.DeleteClient(xray_pb2.ClientIdRequest(name=kwargs["delete_client"]))
