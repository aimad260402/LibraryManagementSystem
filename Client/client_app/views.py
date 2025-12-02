# In Client/client_app/views.py

from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.urls import reverse
from .grpc_client import LibraryClient

# --- Authentication Views ---

def staff_login(request: HttpRequest):
    """Handles the display and processing of the librarian login form."""
    if request.session.get('staff_id'):
        # If already logged in, redirect to the dashboard
        return redirect('dashboard') 

    message = request.session.pop('login_message', None)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        client = LibraryClient()
        # Call the remote gRPC service
        auth_response = client.staff_login(username, password)

        if auth_response.success:
            # Store staff identification for session tracking
            request.session['staff_id'] = auth_response.user_id 
            request.session['username'] = username
            return redirect('dashboard')
        else:
            message = auth_response.message # Display the error message from the gRPC server
            
    return render(request, 'client_app/login.html', {'message': message})

def staff_logout(request: HttpRequest):
    """Logs the staff member out by clearing the session."""
    request.session.clear()
    request.session['login_message'] = "You have been logged out."
    return redirect('staff_login')


# --- Dashboard / Search View ---

def dashboard(request: HttpRequest):
    """The main librarian interface, featuring book search."""
    # Enforce authentication via session check
    staff_id = request.session.get('staff_id')
    if not staff_id:
        request.session['login_message'] = "Please log in to view the dashboard."
        return redirect('staff_login')
        
    query = request.GET.get('q', '') 
    book_results = []
    
    client = LibraryClient()
    
    # Fetch books based on query (or return all available books if query is empty)
    book_results = client.search_books(query)

    context = {
        'username': request.session.get('username'),
        'query': query,
        'book_results': book_results, # List of Protobuf Book objects
        'title': "Librarian Dashboard & Search"
    }
    
    return render(request, 'client_app/dashboard.html', context)