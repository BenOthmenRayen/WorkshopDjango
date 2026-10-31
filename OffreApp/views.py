from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from EntrepriseApp.models import Entreprise
from ExpeditionApp.models import Expedition
from VehiculesApp.models import Vehicule

from .forms import OffreForm, OffreModificationForm
from .models import Offre


# =============================================================================
# Partie 2 — Class-Based Views (routées)
# =============================================================================
class OffreListView(ListView):
    model = Offre
    template_name = 'offres/liste.html'
    context_object_name = 'offres'

    def get_queryset(self):
        return (
            Offre.objects
            .select_related('expedition', 'transporteur', 'vehicule')
            .order_by('-created_at')
        )


class OffreDetailView(DetailView):
    model = Offre
    template_name = 'offres/detail.html'
    context_object_name = 'offre'

    def get_queryset(self):
        return Offre.objects.select_related('expedition', 'transporteur', 'vehicule')


class OffreCreateView(CreateView):
    model = Offre
    form_class = OffreForm
    template_name = 'offres/form.html'

    def get_entreprise_courante(self):
        # Pas d'authentification : le transporteur est passé dans l'URL
        return get_object_or_404(
            Entreprise, pk=self.kwargs['entreprise_id'], type_entreprise='transporteur'
        )

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Seulement les expéditions encore ouvertes aux offres
        form.fields['expedition'].queryset = Expedition.objects.filter(statut='publiee')
        # Seulement les véhicules disponibles du transporteur courant
        form.fields['vehicule'].queryset = Vehicule.objects.filter(
            entreprise=self.get_entreprise_courante(), disponibilite=True
        )
        return form

    def get_initial(self):
        # Préremplissage : ?expedition=12
        initial = super().get_initial()
        expedition_id = self.request.GET.get('expedition')
        if expedition_id:
            initial['expedition'] = expedition_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entreprise'] = self.get_entreprise_courante()
        return context

    def form_valid(self, form):
        # transporteur : fixé côté serveur, jamais fourni par le client
        # statut : jamais exposé, toujours 'proposee' (valeur par défaut du modèle)
        form.instance.transporteur = self.get_entreprise_courante()
        try:
            return super().form_valid(form)
        except ValidationError as e:
            # Une règle métier peut porter sur un champ absent du formulaire
            form.add_error(None, e.messages)
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('expeditions:detail', kwargs={'reference': self.object.expedition.reference})


class OffreUpdateView(UpdateView):
    model = Offre
    form_class = OffreModificationForm
    template_name = 'offres/form.html'
    context_object_name = 'offre'

    def get_queryset(self):
        # Une offre ne se modifie que tant qu'elle est proposée
        return Offre.objects.filter(statut='proposee').select_related('expedition', 'transporteur')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Véhicules du même transporteur : disponibles, ou celui déjà choisi
        form.fields['vehicule'].queryset = Vehicule.objects.filter(
            Q(disponibilite=True) | Q(pk=self.object.vehicule_id),
            entreprise_id=self.object.transporteur_id,
        )
        return form

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e.messages)
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('offres:detail', kwargs={'pk': self.object.pk})


class OffreDeleteView(DeleteView):
    model = Offre
    template_name = 'offres/confirm_delete.html'
    context_object_name = 'offre'
    success_url = reverse_lazy('offres:liste')

    def get_queryset(self):
        # Une offre acceptée ou refusée fait partie de l'historique : non supprimable
        return Offre.objects.filter(statut='proposee')


# =============================================================================
# Partie 1 — Function-Based Views (référence, non routées)
# =============================================================================
def liste_offres(request):
    offres = (
        Offre.objects
        .select_related('expedition', 'transporteur', 'vehicule')
        .order_by('-created_at')
    )
    return render(request, 'offres/liste.html', {'offres': offres})


def detail_offre(request, pk):
    offre = get_object_or_404(
        Offre.objects.select_related('expedition', 'transporteur', 'vehicule'),
        pk=pk,
    )
    return render(request, 'offres/detail.html', {'offre': offre})


@require_POST
def supprimer_offre(request, pk):
    offre = get_object_or_404(Offre, pk=pk)
    offre.delete()
    return redirect('offres:liste')