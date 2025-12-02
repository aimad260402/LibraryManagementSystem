# In Client/client_app/grpc_client.py

import grpc
import sys
import os

# ----------------------------------------------------
# 1. PYTHON PATH FIX (CRITICAL for Django Client)
# ----------------------------------------------------

# Get the directory where THIS SCRIPT (grpc_client.py) is located (e.g., .../client_app)
current_app_dir = os.path.dirname(os.path.abspath(__file__))

# Move up one directory to the package root (C:\...\LibraryManagementSystem\Client)
# This is where the generated library_pb2.py file lives.
project_root_client = os.path.abspath(os.path.join(current_app_dir, '..'))

# Add the client root directory to the search path
sys.path.insert(0, project_root_client)

# ----------------------------------------------------
# 2. GENERATED CODE IMPORTS
# ----------------------------------------------------

# These imports will now succeed because the directory containing them 
# (the 'Client' folder) is in sys.path.
import library_pb2
import library_pb2_grpc

# NOTE: This address MUST match the running gRPC server address (server/grpc_handler.py)
SERVER_ADDRESS = 'localhost:50051' 

class LibraryClient:
    """
    Client-side wrapper to manage remote calls (RPCs) to the gRPC Server.
    """
    def __init__(self):
        self.channel = grpc.insecure_channel(SERVER_ADDRESS)
        self.stub = library_pb2_grpc.LibraryServiceStub(self.channel)

    # ----------------------------------------------------
    # A. Authentication (Librarian Login)
    # ----------------------------------------------------
    def staff_login(self, username, password):
        """Calls the remote UserLogin RPC for staff authentication."""
        request = library_pb2.LoginRequest(username=username, password=password)
        try:
            response = self.stub.UserLogin(request)
            return response
        except grpc.RpcError as e:
            # Error calling RPC (Server offline or connection refused)
            print(f"Error calling UserLogin RPC: {e.details()}")
            return library_pb2.LoginResponse(
                success=False, 
                message=f"Connection error to gRPC server: {e.details()}"
            )

    # ----------------------------------------------------
    # B. Inventory Lookup (Search)
    # ----------------------------------------------------
    def search_books(self, query):
        """Calls the remote SearchBooks RPC to retrieve a stream of books."""
        request = library_pb2.SearchRequest(query=query)
        
        try:
            # Call the remote RPC and receive the iterable stream of results
            return list(self.stub.SearchBooks(request))
        except grpc.RpcError as e:
            print(f"Error calling SearchBooks RPC: {e.details()}")
            return [] 
            
    # ----------------------------------------------------
    # C. Inventory Management (Create Book)
    # ----------------------------------------------------
    def create_book(self, title, author, isbn, is_available):
        """Calls the remote CreateBook RPC on the server to add a new book."""
        book_request = library_pb2.Book(
            title=title,
            author=author,
            isbn=isbn,
            is_available=is_available 
        )
        
        try:
            response = self.stub.CreateBook(book_request)
            return response
        except grpc.RpcError as e:
            details = e.details()
            return library_pb2.StatusResponse(
                success=False, 
                message=f"RPC Error: {details}"
            )