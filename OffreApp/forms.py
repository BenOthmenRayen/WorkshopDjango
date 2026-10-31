from django import forms

from .models import Offre


class OffreForm(forms.ModelForm):
    """Création : statut et transporteur ne sont jamais exposés."""
    class Meta:
        model = Offre
        fields = ['expedition', 'vehicule', 'prix', 'delai_jours']


class OffreModificationForm(forms.ModelForm):
    """Modification : l'expédition visée ne change plus."""
    class Meta:
        model = Offre
        fields = ['vehicule', 'prix', 'delai_jours']