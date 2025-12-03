import grpc
from concurrent import futures
import os
import django
import sys
from django.contrib.auth import authenticate 
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Q 
from django.db.utils import OperationalError
from django.db import IntegrityError
from django.db import transaction

# ----------------------------------------------------
# 1. ROBUST DJANGO ENVIRONMENT SETUP 
# ----------------------------------------------------

# Set up Django environment and initialize
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_server.settings') 

try:
    django.setup() 
except Exception as e:
    print(f"FATAL: Django setup failed. Details: {e}") 
    sys.exit(1)

# ----------------------------------------------------
# 2. Model and Generated Code Imports
# ----------------------------------------------------
from django.contrib.auth.models import User # <-- CORRECT: Import the built-in User model
from library_admin.models import Book # Keep Book for inventory management
# NOTE: We no longer import LibraryUser here, as it's not used in this file's logic

# Import generated protobuf code 
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
        # ... (UserLogin logic remains the same, it correctly uses authenticate) ...
        response = library_pb2.LoginResponse()

        if user is not None and user.is_active:
            if user.is_staff or user.is_superuser:
                response.success = True
                response.user_id = str(user.id) 
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
        """Creates a new Book record."""
        # ... (CreateBook logic remains the same) ...
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
        # ... (SearchBooks logic remains the same) ...
        query = request.query
        
        books = Book.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        ).order_by('title')
        
        for book in books:
            yield library_pb2.Book(
                id=book.id,
                title=book.title,
                author=book.author,
                isbn=book.isbn,
                is_available=book.is_available
            )

    # D. Staff Profile Update
    def UpdateStaffProfile(self, request, context):
        """Updates a staff member's profile (username, email, password)."""
        response = library_pb2.StatusResponse()

        try:
            # 1. CRITICAL FIX: Look up the user in the built-in User model (auth_user table)
            staff_id_int = int(request.staff_id) 
            user = User.objects.get(id=staff_id_int) # <-- FIX: Changed from LibraryUser to User
            
            # 2. SECURITY CHECK: Verify Current Password
            if not check_password(request.current_password, user.password):
                context.set_code(grpc.StatusCode.UNAUTHENTICATED)
                context.set_details("Security Check Failed: Current password is incorrect.")
                return library_pb2.StatusResponse(success=False, message="Invalid current password.")
            
            # 3. Update Profile Fields (within a transaction for atomicity)
            with transaction.atomic():
                
                # Update Username (if provided and changed)
                if request.new_username and request.new_username != user.username:
                    # FIX: Change uniqueness check to use the built-in User model
                    if User.objects.filter(username=request.new_username).exclude(id=user.id).exists():
                        context.set_code(grpc.StatusCode.ALREADY_EXISTS)
                        context.set_details("Username already taken.")
                        return library_pb2.StatusResponse(success=False, message="Username already taken.")
                    user.username = request.new_username
                    
                # Update Email
                if request.new_email:
                    user.email = request.new_email

                # Update Password (if new_password is provided)
                if request.new_password:
                    user.password = make_password(request.new_password)
                
                user.save()

            response.success = True
            response.message = "Profile updated successfully."
            response.entity_id = user.id

        except User.DoesNotExist: # <-- FIX: Changed exception to User.DoesNotExist
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Staff member not found.")
            response.success = False
            response.message = "Staff member not found."
        
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"An unexpected server error occurred: {e}")
            response.success = False
            response.message = "Failed to update profile due to a server error."

        return response


# ----------------------------------------------------
# 4. Server Initialization (Serve function remains the same)
# ----------------------------------------------------

def serve():
    """Starts the gRPC server on the designated port 50051."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    library_pb2_grpc.add_LibraryServiceServicer_to_server(
        LibraryServicer(), server)
    
    server.add_insecure_port('[::]:50051') 
    server.start()
    print("gRPC Library Server started on port 50051.")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)
        print("\nServer shut down gracefully.")


if __name__ == '__main__':
    try:
        Book.objects.exists()
        serve()
    except OperationalError as e:
        print("\n--- FATAL ERROR: DATABASE CONNECTION FAILED ---")
        print("Please ensure your MySQL server is running and accessible.")
    except Exception as e:
        print(f"An unexpected error occurred during startup: {e}")