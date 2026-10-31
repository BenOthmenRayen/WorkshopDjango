from django import forms

from .models import Expedition


class ExpeditionForm(forms.ModelForm):
    class Meta:
        model = Expedition
        # Liste explicite : reference (générée), statut (géré par le métier)
        # et entreprise (fixée côté serveur) ne sont jamais exposés
        fields = ['ville_depart', 'ville_arrive', 'date_souhaitée', 'poid_kg', 'description']
        widgets = {
            'date_souhaitée': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M',
            ),
        }