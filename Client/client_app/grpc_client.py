# In Client/client_app/grpc_client.py

import grpc
# Import generated stubs and messages from the Client's local environment
# The import path must start from the directory where Python looks for packages
from Client import library_pb2
from Client import library_pb2_grpc

# NOTE: This address MUST match the running gRPC server address (server/grpc_handler.py)
SERVER_ADDRESS = 'localhost:50051' 

class LibraryClient:
    """
    Client-side wrapper to manage remote calls (RPCs) to the gRPC Server.
    """
    def __init__(self):
        self.channel = grpc.insecure_channel(SERVER_ADDRESS)
        self.stub = library_pb2_grpc.LibraryServiceStub(self.channel)

    def staff_login(self, username, password):
        """Calls the remote UserLogin RPC for staff authentication."""
        request = library_pb2.LoginRequest(username=username, password=password)
        try:
            # Send the request and receive the LoginResponse
            response = self.stub.UserLogin(request)
            return response
        except grpc.RpcError as e:
            print(f"Error calling UserLogin RPC: {e.details()}")
            return library_pb2.LoginResponse(
                success=False, 
                message=f"Connection error to gRPC server: {e.details()}"
            )

    def search_books(self, query):
        """Calls the remote SearchBooks RPC to retrieve a stream of books."""
        request = library_pb2.SearchRequest(query=query)
        
        try:
            # Call the remote RPC and receive the iterable stream of results
            return list(self.stub.SearchBooks(request))
        except grpc.RpcError as e:
            print(f"Error calling SearchBooks RPC: {e.details()}")
            return [] # Return an empty list on failure