
from decimal import Decimal

from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone


#Ce sont des imports entre applications. Chaque application Django a ses propres modèles, 
# et on importe ceux dont on a besoin pour créer des relations. C’est ainsi que le projet est découpé en modules (une application par domaine métier).
from EntrepriseApp.models import Entreprise
from ExpeditionApp.models import Expedition
from VehiculesApp.models import Vehicule


#un dictionnaire dont la clé est le type de véhicule et la valeur un tuple (poids_min, poids_max) en kg.
PLAGES_POIDS_PAR_TYPE_VEHICULE = {
    'camionnette': (Decimal(0), Decimal(1500)),
    'fourgon': (Decimal(1500), Decimal(3500)),
    'camion_porteur': (Decimal(3500), Decimal(19000)),
    'semi_remorque': (Decimal(19000), Decimal(26000)),
}
class Offre(models.Model):
    STATUT_CHOICES = [#constante declaree en majuscule 
        ('proposee', 'Proposee'),
        ('acceptee', 'Acceptee'),
        ('refusee', 'Refusee'),
        ('retiree', 'Retiree'),
    ]

    prix = models.DecimalField(
        decimal_places=2,# nombre décimal exact (NUMERIC en SQL), idéal pour l’argent.
        max_digits=10,
        validators=[MinValueValidator(1, message='Le prix doit être supérieur à 1')],
    )
    delai_jours = models.PositiveIntegerField(
        validators=[MinValueValidator(1, message='Une valeur supérieure ou égale à 1 est requise')]
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='proposee')
    date_proposition = models.DateField(auto_now_add=True)
#DateField : date seule (2026-10-24), alors que DateTimeField contient date et heure.
#Remarque : ce champ fait doublon avec created_at, qui contient déjà cette information.
#Ce n’est pas une erreur, mais l’un des deux suffit.
    expedition = models.ForeignKey(Expedition, on_delete=models.CASCADE)
    transporteur = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    vehicule = models.ForeignKey(Vehicule, on_delete=models.CASCADE)

#ForeignKey est la relation plusieurs — 1 (many-to-one). C’est la différence avec le OneToOneField déjà vu :
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Offre de {self.transporteur.raison_sociale} sur {self.expedition.reference}"

    def clean(self):
        super().clean()

        if self.transporteur_id and self.transporteur.type_entreprise != 'transporteur':
            raise ValidationError({
                'transporteur': "Une offre ne peut être créée que par une entreprise de type transporteur."
            })

        if self.vehicule_id and self.transporteur_id and self.vehicule.entreprise_id != self.transporteur_id:
            raise ValidationError({
                'vehicule': "Le véhicule doit appartenir à l'entreprise transporteur de l'offre."
            })

        if self.pk is None and self.expedition_id and self.expedition.statut != 'publiee':
            raise ValidationError({
                'expedition': "Cette expédition ne peut plus recevoir de nouvelles offres (statut différent de 'publiée')."
            })

        if self.statut == 'proposee' and self.transporteur_id and self.expedition_id:
            duplicate_exists = Offre.objects.filter(
                transporteur_id=self.transporteur_id,
                expedition_id=self.expedition_id,
                statut='proposee',
            ).exclude(pk=self.pk).exists()
            if duplicate_exists:
                raise ValidationError({
                    'statut': "Cette entreprise a déjà une offre 'proposee' active sur cette expédition."
                })

        if self.pk is None and self.vehicule_id and not self.vehicule.disponibilite:
            raise ValidationError({
                'vehicule': "Ce véhicule n'est pas disponible et ne peut pas être proposé sur une nouvelle offre."
            })

        if self.vehicule_id and self.expedition_id:
            plage = PLAGES_POIDS_PAR_TYPE_VEHICULE.get(self.vehicule.type_vehicule)
            poids_kg = self.expedition.poid_kg
            if plage and not (plage[0] < poids_kg <= plage[1]):
                raise ValidationError({
                    'vehicule': (
                        f"Le type de véhicule '{self.vehicule.type_vehicule}' n'est pas adapté "
                        f"au poids de l'expédition ({poids_kg} kg)."
                    )
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        previous_statut = None
        if self.pk:
            previous_statut = Offre.objects.filter(pk=self.pk).values_list('statut', flat=True).first()

        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.statut == 'acceptee' and previous_statut != 'acceptee':
                self._appliquer_cascade_acceptation()


#Cette méthode est appelée uniquement lorsque le statut de l’offre passe à "acceptee".
#Cette méthode applique les conséquences métier de l'acceptation d'une offre.
    def _appliquer_cascade_acceptation(self):
        expedition_model = apps.get_model('ExpeditionApp', 'Expedition')
        expedition_model.objects.filter(pk=self.expedition_id).update(statut='attribue')

        Offre.objects.filter(
            expedition_id=self.expedition_id,
            statut='proposee',
        ).exclude(pk=self.pk).update(statut='refusee', updated_at=timezone.now())
   
#Ce code vérifie la validité d’une offre avec clean() (transporteur, véhicule, poids, doublons et statut de l’expédition), puis save() valide et enregistre l’offre.
#Si l’offre devient acceptée, _appliquer_cascade_acceptation() attribue l’expédition au transporteur et refuse automatiquement les autres offres encore proposées pour cette expédition.
    