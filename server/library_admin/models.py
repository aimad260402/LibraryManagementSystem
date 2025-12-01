from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=200, help_text="Title of the book.")
    author = models.CharField(max_length=100)
    isbn = models.CharField(max_length=13, unique=True, help_text="13-Digit ISBN.")
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} by {self.author}"
    
class LibraryUser(models.Model):
    # Links to the built-in Django User model for authentication if needed for a separate login.
    # For now, it simply uses the existing primary User table for ID/name storage.
    user = models.OneToOneField(User, on_delete=models.CASCADE) 
    
    # Custom, permanent ID for the patron (will be used as the gRPC identifier/token)
    member_id = models.CharField(max_length=20, unique=True, verbose_name="Library Member ID")
    max_loans = models.IntegerField(default=5)

    def __str__(self):
        return f"Patron: {self.user.username} ({self.member_id})"
    
