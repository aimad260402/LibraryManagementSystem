from django.contrib import admin
# Register your models here.
from .models import Emprunt

@admin.register(Emprunt)
class EmpruntAdmin(admin.ModelAdmin):
    list_display = ['book_title', 'borrower_name', 'borrow_date', 'return_date', 'status']
    list_filter = ['status', 'borrow_date', 'return_date']
    search_fields = ['book_title', 'borrower_name', 'borrower_email']
    date_hierarchy = 'borrow_date'