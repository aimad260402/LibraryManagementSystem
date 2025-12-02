import grpc
from concurrent import futures
import os
import django
import sys # Import sys for path modification
from django.contrib.auth import authenticate 
from django.db.models import Q 
from django.db.utils import OperationalError
from django.db import IntegrityError

# ----------------------------------------------------
# 1. ROBUST DJANGO ENVIRONMENT SETUP (Path Fix)
# ----------------------------------------------------

# 🚨 FIX: Add the directory containing the settings module to the search path.
# os.path.dirname(os.path.abspath(__file__)) points directly to C:\...\server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) 

# Set the environment variable pointing to your settings file.
# NOTE: Using 'library_server.settings' based on your folder structure.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_server.settings') 

# Initialize Django environment
try:
    print("Attempting Django setup...")
    django.setup() 
    print("Django setup successful.")
except Exception as e:
    print(f"FATAL: Django setup failed. Details: {e}") 
    sys.exit(1)

# ----------------------------------------------------
# 2. Model and Generated Code Imports
# ----------------------------------------------------
# These imports rely on Django setup having completed successfully
from library_admin.models import LibraryUser, Book 

# Import generated protobuf code (must be locally available)
import library_pb2
import library_pb2_grpc


# ----------------------------------------------------
# 3. The gRPC Servicer Implementation
# ----------------------------------------------------

class LibraryServicer(library_pb2_grpc.LibraryServiceServicer):
    
    # A. Authentication (Staff/Librarian Login - RPC: Unary)
    def UserLogin(self, request, context):
        """Authenticates a staff member for the Client application."""
        user = authenticate(
            username=request.username,
            password=request.password
        )
        
        response = library_pb2.LoginResponse()

        if user is not None and user.is_active:
            # Check for staff privileges (Librarian)
            if user.is_staff or user.is_superuser:
                response.success = True
                response.user_id = str(user.id) # Django User ID for session tracking
                response.message = f"Staff login successful: {user.username}"
            else:
                response.success = False
                response.message = "Access Denied: Account lacks staff privileges."
        else:
            response.success = False
            response.user_id = ""
            response.message = "Invalid username or account is inactive."
            
        return response
    
    # B. Inventory Management (Book Creation - RPC: Unary)
    def CreateBook(self, request, context):
        """Creates a new Book record in the database using Django ORM."""
        response = library_pb2.StatusResponse()
        
        try:
            new_book = Book.objects.create(
                title=request.title,
                author=request.author,
                isbn=request.isbn,
                is_available=request.is_available
            )
            response.success = True
            response.message = f"Book '{request.title}' successfully created."
            response.entity_id = new_book.id
            
        except IntegrityError:
            response.success = False
            response.message = f"Failed to create book: ISBN '{request.isbn}' already exists."
            context.set_code(grpc.StatusCode.ALREADY_EXISTS)
            context.set_details(response.message)
            
        except Exception as e:
            response.success = False
            response.message = f"An unexpected database error occurred: {e}"
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(response.message)
            
        return response
        
    # C. Inventory Lookup (Book Search - RPC: Server Stream)
    def SearchBooks(self, request, context):
        """Searches books and streams results back to the client."""
        query = request.query
        
        books = Book.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        ).order_by('title')
        
        # Yield each Django model object as a Protobuf message
        for book in books:
            yield library_pb2.Book(
                id=book.id,
                title=book.title,
                author=book.author,
                isbn=book.isbn,
                is_available=book.is_available
            )
    
    # NOTE: Other RPC methods for Loan, Update, Delete would go here.


# ----------------------------------------------------
# 4. Server Initialization
# ----------------------------------------------------

def serve():
    """Starts the gRPC server on the designated port 50051."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    library_pb2_grpc.add_LibraryServiceServicer_to_server(
        LibraryServicer(), server)
    
    # 🚨 PORT CONFIGURATION: Listening on port 50051
    server.add_insecure_port('[::]:50051') 
    server.start()
    print("gRPC Library Server started on port 50051.")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)
        print("\nServer shut down gracefully.")


if __name__ == '__main__':
    # Initial check to catch common database errors before starting the server
    try:
        # This checks the DB connection before starting the server thread pool
        Book.objects.exists()
        serve()
    except OperationalError as e:
        print("\n--- FATAL ERROR: DATABASE CONNECTION FAILED ---")
        print("Please ensure your MySQL server is running and accessible.")
    except Exception as e:
        print(f"An unexpected error occurred during startup: {e}")