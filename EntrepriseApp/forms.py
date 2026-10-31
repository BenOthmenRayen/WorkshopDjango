from django import forms
from django.db.models import Q

from .models import Entreprise


class EntrepriseForm(forms.ModelForm):
    class Meta:
        model = Entreprise
        fields = ['raison_sociale', 'matricule_fiscal', 'type_entreprise', 'adresse', 'gerant']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Gérants proposés : utilisateurs sans entreprise (+ le gérant actuel en modification)
        self.fields['gerant'].queryset = self.fields['gerant'].queryset.filter(
            Q(entreprise__isnull=True) | Q(pk=self.instance.gerant_id)
        )