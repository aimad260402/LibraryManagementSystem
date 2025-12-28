from django.db import models
from django.utils import timezone
# Create your models here.

class Client(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20)
    date_inscription = models.DateTimeField(auto_now_add=True)
    emprunts_actifs = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.nom} {self.prenom}"
    
    class Meta:
        ordering = ['-date_inscription']
####Commendes####
class Emprunt(models.Model):
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('returned', 'Retourné'),
        ('overdue', 'En Retard'),
    ]
    
    book_title = models.CharField(max_length=200, verbose_name="Titre du livre")
    borrower_name = models.CharField(max_length=100, verbose_name="Nom de l'emprunteur")
    borrower_email = models.EmailField(verbose_name="Email de l'emprunteur")
    borrow_date = models.DateField(default=timezone.now, verbose_name="Date d'emprunt")
    return_date = models.DateField(verbose_name="Date de retour prévue")
    actual_return_date = models.DateField(null=True, blank=True, verbose_name="Date de retour réelle")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-borrow_date']
        verbose_name = "Emprunt"
        verbose_name_plural = "Emprunts"
    
    def __str__(self):
        return f"{self.book_title} - {self.borrower_name}"
    
    def is_overdue(self):
        """Vérifie si l'emprunt est en retard"""
        if self.status == 'active' and self.return_date < timezone.now().date():
            return True
        return False