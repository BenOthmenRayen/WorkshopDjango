from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q

from .models import Entreprise, Utilisateur


# Aide affichée sous les champs qui bloquent le plus souvent la création d'une entreprise
MATRICULE_AIDE = (
    "Format tunisien : 7 chiffres + lettre de contrôle + code TVA (A, B, D, N, P ou E) "
    "+ catégorie (M, P, C, N ou E) + 3 chiffres d'établissement. "
    "Exemples valides : 1234567/A/A/M/000, 1234567AAM000 ou 1234567-A-A-M-000."
)
ADRESSE_AIDE = "Au moins 20 caractères (rue, ville, code postal)."

ENTREPRISE_WIDGETS = {
    'matricule_fiscal': forms.TextInput(attrs={'placeholder': '1234567/A/A/M/000'}),
    'adresse': forms.TextInput(attrs={'placeholder': '22 rue des Dahlias, Ezzouhour 2052 Tunis'}),
}
ENTREPRISE_HELP = {
    'matricule_fiscal': MATRICULE_AIDE,
    'adresse': ADRESSE_AIDE,
}


class MatriculeMixin:
    """Nettoie le matricule avant la validation du modèle : espaces retirés, lettres en majuscules."""
    def clean_matricule_fiscal(self):
        matricule = self.cleaned_data['matricule_fiscal'].strip().upper()
        return ' '.join(matricule.split())


class InscriptionForm(UserCreationForm):
    """Formulaire d'inscription basé sur UserCreationForm.

    password1 / password2 (double saisie, vérification, hachage) sont ajoutés
    automatiquement par UserCreationForm.
    roles, is_staff et is_superuser ne sont JAMAIS exposés : sinon un visiteur
    pourrait se donner lui-même des droits (mass assignment).
    """
    class Meta(UserCreationForm.Meta):
        model = Utilisateur
        fields = ('username', 'email', 'telephone')


class EntrepriseForm(MatriculeMixin, forms.ModelForm):
    """Modification d'une entreprise (le gérant reste modifiable)."""
    class Meta:
        model = Entreprise
        fields = ['raison_sociale', 'matricule_fiscal', 'type_entreprise', 'adresse', 'gerant']
        widgets = ENTREPRISE_WIDGETS
        help_texts = ENTREPRISE_HELP

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Gérants proposés : utilisateurs sans entreprise (+ le gérant actuel en modification)
        self.fields['gerant'].queryset = self.fields['gerant'].queryset.filter(
            Q(entreprise__isnull=True) | Q(pk=self.instance.gerant_id)
        )


class EntrepriseCreationForm(MatriculeMixin, forms.ModelForm):
    """Création de l'entreprise après l'inscription.

    Le champ gerant n'est pas exposé : il est fixé côté serveur à request.user.
    """
    class Meta:
        model = Entreprise
        fields = ['raison_sociale', 'matricule_fiscal', 'type_entreprise', 'adresse']
        widgets = ENTREPRISE_WIDGETS
        help_texts = ENTREPRISE_HELP