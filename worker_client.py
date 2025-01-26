import grpc
import xray_pb2
import xray_pb2_grpc
from concurrent import futures
from add_client_in_xray_config import add_client

class XrayClientsServiceServicer(xray_pb2_grpc.XrayClientsServiceServicer):
    def InstallCertificate(self, request, context):
        cert = request.certificate
        server_id = request.server_id

        




    def AddClient(self, request, context):
        print(f"Добавляю нового клиента {request.name}")
        uuid, shortids = add_client(request.name)
        return xray_pb2.ClientIdentifierResponse(uuid = uuid, shortids = shortids)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    xray_pb2_grpc.add_XrayClientsServiceServicer_to_server(XrayClientsServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Server started on port 50051")
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()