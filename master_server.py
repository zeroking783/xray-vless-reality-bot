import grpc
import xray_pb2
import xray_pb2_grpc

def send_request():
    # Создание канала для подключения к серверу
    with grpc.insecure_channel('138.124.31.142:50051') as channel:
        stub = xray_pb2_grpc.XrayClientsServiceStub(channel)  # Используем сгенерированный клиент
        # Отправка запроса AddClient
        response = stub.AddClient(xray_pb2.ClientIdRequest(name="bakvivas"))
        print(f"Received response: UUID={response.uuid}, Short ID={response.shortids}")

if __name__ == '__main__':
    send_request()