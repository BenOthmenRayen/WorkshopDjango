from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from EntrepriseApp.models import Entreprise

from .forms import ExpeditionForm
from .models import Expedition


# =============================================================================
# Partie 2 — Class-Based Views (routées)
# =============================================================================
class ExpeditionListView(ListView):
    model = Expedition
    template_name = 'expeditions/liste.html'
    context_object_name = 'expeditions'

    def get_queryset(self):
        return (
            Expedition.objects
            .filter(statut='publiee')
            .select_related('entreprise')
            .order_by('-created_at')
        )


class ExpeditionDetailView(DetailView):
    model = Expedition
    template_name = 'expeditions/detail.html'
    context_object_name = 'expedition'
    slug_field = 'reference'
    slug_url_kwarg = 'reference'

    def get_queryset(self):
        return Expedition.objects.select_related('entreprise')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['offres'] = (
            self.object.offre_set
            .select_related('transporteur', 'vehicule')
            .order_by('-date_proposition')
        )
        return context


class ExpeditionCreateView(CreateView):
    model = Expedition
    form_class = ExpeditionForm
    template_name = 'expeditions/form.html'

    def get_entreprise_courante(self):
        # Pas d'authentification : le chargeur est passé dans l'URL
        return get_object_or_404(
            Entreprise, pk=self.kwargs['entreprise_id'], type_entreprise='chargeur'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entreprise'] = self.get_entreprise_courante()
        return context

    def form_valid(self, form):
        # entreprise : fixée côté serveur, jamais fournie par le formulaire
        # statut : jamais exposé, toujours la valeur par défaut du modèle
        form.instance.entreprise = self.get_entreprise_courante()
        try:
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e.messages)
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('expeditions:detail', kwargs={'reference': self.object.reference})


class ExpeditionUpdateView(UpdateView):
    model = Expedition
    form_class = ExpeditionForm
    template_name = 'expeditions/form.html'
    context_object_name = 'expedition'
    slug_field = 'reference'
    slug_url_kwarg = 'reference'

    def get_queryset(self):
        # Une expédition n'est modifiable que tant qu'elle est publiée
        return Expedition.objects.filter(statut='publiee').select_related('entreprise')

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ValidationError as e:
            form.add_error(None, e.messages)
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse('expeditions:detail', kwargs={'reference': self.object.reference})


class ExpeditionDeleteView(DeleteView):
    model = Expedition
    template_name = 'expeditions/confirm_delete.html'
    context_object_name = 'expedition'
    slug_field = 'reference'
    slug_url_kwarg = 'reference'
    success_url = reverse_lazy('expeditions:liste')


# =============================================================================
# Partie 1 — Function-Based Views (référence, non routées)
# =============================================================================
def liste_expeditions(request):
    expeditions = (
        Expedition.objects
        .filter(statut='publiee')
        .select_related('entreprise')
        .order_by('-created_at')
    )
    return render(request, 'expeditions/liste.html', {'expeditions': expeditions})


def detail_expedition(request, reference):
    expedition = get_object_or_404(
        Expedition.objects.select_related('entreprise'),
        reference=reference,
    )
    offres = (
        expedition.offre_set
        .select_related('transporteur', 'vehicule')
        .order_by('-date_proposition')
    )
    return render(
        request,
        'expeditions/detail.html',
        {'expedition': expedition, 'offres': offres},
    )


@require_POST
def supprimer_expedition(request, reference):
    expedition = get_object_or_404(Expedition, reference=reference)
    expedition.delete()
    return redirect('expeditions:liste')