# In Client/client_app/views.py

from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.urls import reverse
from .grpc_client import LibraryClient

# ----------------------------------------------------
# A. Authentication Views (No Change)
# ----------------------------------------------------

def staff_login(request: HttpRequest):
    # ... (Implementation remains the same) ...
    if request.session.get('staff_id'):
        return redirect('dashboard') 

    message = request.session.pop('login_message', None)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        client = LibraryClient()
        auth_response = client.staff_login(username, password)

        if auth_response.success:
            # Storing the ID and username after successful auth
            request.session['staff_id'] = auth_response.user_id 
            request.session['username'] = username
            return redirect('dashboard')
        else:
            message = auth_response.message
            
    return render(request, 'client_app/login.html', {'message': message})

def staff_logout(request: HttpRequest):
    # ... (Implementation remains the same) ...
    request.session.clear()
    request.session['login_message'] = "You have been logged out."
    return redirect('staff_login')


# ----------------------------------------------------
# B. Core Management Views (No Change)
# ----------------------------------------------------

def dashboard(request: HttpRequest):
    # ... (Implementation remains the same) ...
    staff_id = request.session.get('staff_id')
    if not staff_id:
        request.session['login_message'] = "Please log in to view the dashboard."
        return redirect('staff_login')
        
    query = request.GET.get('q', '') 
    client = LibraryClient()
    book_results = client.search_books(query)

    context = {
        'username': request.session.get('username'),
        'query': query,
        'book_results': book_results,
        'title': "Librarian Dashboard & Search"
    }
    return render(request, 'client_app/dashboard.html', context)

def add_book(request: HttpRequest):
    # ... (Implementation remains the same) ...
    staff_id = request.session.get('staff_id')
    
    if not staff_id:
        request.session['login_message'] = "Authentication required."
        return redirect('staff_login')

    context = {
        'username': request.session.get('username'),
        'title': "Add New Book"
    }
    
    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        isbn = request.POST.get('isbn')
        is_available = request.POST.get('is_available') == 'on' 

        client = LibraryClient()
        response = client.create_book(title, author, isbn, is_available)
        
        context['success'] = response.success
        context['message'] = response.message
        
        if response.success:
            context['message'] += f" (New ID: {response.entity_id})"
            
    return render(request, 'client_app/add_book.html', context)

# ----------------------------------------------------
# C. Staff Profile Management (Cleaned)
# ----------------------------------------------------

def staff_profile(request: HttpRequest):
    """
    Handles staff profile viewing and updates using the UpdateStaffProfile RPC.
    """
    staff_id = request.session.get('staff_id')
    
    # 💡 CLEANUP 1: Moved debug line inside the POST block, or rely on server debug.
    
    if not staff_id:
        request.session['login_message'] = "Authentication required."
        return redirect('staff_login')
    
    # Initialize context with current session data
    context = {
        'username': request.session.get('username'),
        'email': request.session.get('email', 'Update your email address'), 
        'staff_id': staff_id,
        'title': "Librarian Profile"
    }
    
    if request.method == 'POST':
        
        # 💡 CLEANUP 2: Use .get(key, default) for robustness against missing form data
        new_username = request.POST.get('new_username', context['username']) # Default to current session username
        new_email = request.POST.get('new_email', context['email'])
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        
        # 2. Basic Validation: Must supply current password
        if not current_password:
            context['error_message'] = "Security Check: You must enter your current password to save any changes."
            # Render context with new_username/new_email retained from POST data
            context['username'] = new_username 
            context['email'] = new_email
            return render(request, 'client_app/staff_profile.html', context)

        # 3. Call gRPC RPC
        client = LibraryClient()
        response = client.update_staff_profile(
            staff_id=staff_id,
            new_username=new_username,
            new_email=new_email,
            current_password=current_password,
            new_password=new_password
        )

        # 4. Process gRPC Response (StatusResponse)
        if response.success:
            context['success_message'] = response.message
            
            # Update local session state on success
            request.session['username'] = new_username
            if new_email:
                request.session['email'] = new_email

            # Force re-login if password was changed for security
            if new_password:
                request.session.clear()
                request.session['login_message'] = "Password changed successfully. Please log in again."
                return redirect('staff_login')

        else:
            # Display the error message from the gRPC client/server
            context['error_message'] = response.message
            # Re-set context values for re-rendering (Keep user input)
            context['username'] = new_username 
            context['email'] = new_email 


    # Re-render the page with success/error messages
    return render(request, 'client_app/staff_profile.html', context)