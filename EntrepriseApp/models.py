from django.utils import timezone
# il sert à récupérer l’année en cours pour générer l’identifiant (26user00).
from django.db import models
#models.Model : la classe mère de tout modèle ;les types de champs : CharField, EmailField, DateTimeField, OneToOneField...
from django.contrib.auth.models import AbstractUser
#AbstractUser est le modèle utilisateur complet de Django,Il apporte déjà ces champs
from django.core.validators import MinLengthValidator, RegexValidator
#Ce sont des validateurs prêts à l’emploi
from django.core.exceptions import ValidationError
#C’est l’exception que lève un validateur quand une valeur est invalide

#Le validateur personnalisé validate_email
def validate_email(value):
    if not value:
        raise ValidationError("L'email ne peut pas être vide")
    if not value.endswith('@gmail.com'):
        raise ValidationError("Format d'email invalide, doit se terminer par @gmail.com")
    def save(self, *args, **kwargs):#une methode de save na de sens dans une classe 
            self.full_clean()
            super().save(*args, **kwargs)


# il construit un RegexValidator avec la regex et le message donnés(une expression régulière)
def regexValidator(regex,message):
    return RegexValidator(regex=regex,message=message)


#un modèle utilisateur personnalisé
# Héritage : récupère username, password haché, first_name, last_name, is_staff…
class Utilisateur(AbstractUser):
    user_id=models.CharField(max_length=100,primary_key=True,editable=False)#CharField : colonne texte (VARCHAR).
    email=models.EmailField(unique=True,validators=[validate_email])
    telephone=models.CharField(max_length=15,blank=True,null=True)
    roles=models.CharField(max_length=12,choices=[('chargeur','chargeur'),('transporteur','Transporteur '),(' admin',' administrateur')],default='chargeur')# menu deroulant 
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)


    #	Calcule 26user00, 26user01…
    @classmethod
    def _generate_user_id(cls):
        annee = timezone.now().strftime('%y')#strftime('%y') formate la date sur 2 chiffres : 2026 donne "26".
        prefixe = f"{annee}user"#Cette f-string construit "26user"

        dernier = (
            cls.objects
            .filter(user_id__startswith=prefixe)
            .order_by('-user_id')#le - signifie tri décroissant
            .first()# renvoie le premier résultat
        )
        compteur = int(dernier.user_id[-2:]) + 1 if dernier else 0

        if compteur > 99:
            raise ValueError(
                f"Limite de 100 utilisateurs atteinte pour l'année 20{annee}."
            )

        return f"{prefixe}{compteur:02d}"


#Génère l’id → full_clean() → super().save()
    def save(self, *args, **kwargs):
                if not self.user_id:self.user_id=self._generate_user_id()
                self.full_clean()#force la validation complète :
                #Django n’exécute PAS les validateurs lors d’un save()
                super().save(*args, **kwargs)
                #On appelle le save() d’origine (celui de la classe parente), 
                # qui exécute réellement l’INSERT ou l’UPDATE SQL
    

#Hérite de models.Model, la classe de base de tout modèle. 
# Ici pas besoin d’AbstractUser, car une entreprise ne se connecte pas.

class Entreprise(models.Model):
#On n’utilise pas AbstractUser ici, car une entreprise ne se connecte pas
    raison_sociale=models.CharField(max_length=100)
    #C’est le nom officiel de la société. Le champ est obligatoire,
    #  car blank=False est la valeur par défaut.
    matricule_fiscal=models.CharField(max_length=17,unique=True, validators=[regexValidator(regex='\d{7}[/ -]?[A-Za-z][/ -]?[ABDNPEabdnpe][/ -]?[MPCNEmpcne][/ -]?\d{3}$',message='invalide format')])
    #Ce champ contient le matricule fiscal tunisien, qui doit être unique pour chaque entreprise.
    type_entreprise=models.CharField(max_length=12,choices=[('chargeur','chargeur'),('transporteur','Transporteur ')],default='chargeur')
    adresse=models.CharField(validators=[MinLengthValidator(20,"L'adresse doit contenir au moins 20 caractères")])
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    #la relation 1—1
    #une ForeignKey avec unique=True : un utilisateur gère au plus une entreprise, et une entreprise a un seul gérant.
    gerant=models.OneToOneField(Utilisateur,on_delete=models.CASCADE,related_name='entreprise')












