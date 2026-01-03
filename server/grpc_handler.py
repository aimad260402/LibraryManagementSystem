# ----------------------------------------------------
# 1. ROBUST DJANGO ENVIRONMENT SETUP 
# ----------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))) 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_server.settings') 

try:
    print("Attempting Django setup...") 
    django.setup() 
    print("Django setup successful.")
except Exception as e:
    print(f"FATAL: Django setup failed. Details: {e}") 
    sys.exit(1)
    
# ----------------------------------------------------
# 2. Generated Code Imports
# ----------------------------------------------------
from django.contrib.auth.models import User
from library_admin.models import Book, Loan, Member 

import library_pb2
import library_pb2_grpc