from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import EntrepriseForm
from .models import Entreprise


# =============================================================================
# Partie 2 — Class-Based Views (routées)
# =============================================================================
class EntrepriseListView(ListView):
    model = Entreprise
    template_name = 'entreprises/liste.html'
    context_object_name = 'entreprises'

    def get_queryset(self):
        return Entreprise.objects.select_related('gerant').order_by('raison_sociale')


class EntrepriseDetailView(DetailView):
    model = Entreprise
    template_name = 'entreprises/detail.html'
    context_object_name = 'entreprise'

    def get_queryset(self):
        return Entreprise.objects.select_related('gerant')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vehicules'] = self.object.vehicules.order_by('immatriculation')
        context['expeditions'] = self.object.expeditions.order_by('-created_at')
        context['offres'] = (
            self.object.offre_set
            .select_related('expedition', 'vehicule')
            .order_by('-date_proposition')
        )
        return context


class EntrepriseCreateView(CreateView):
    model = Entreprise
    form_class = EntrepriseForm
    template_name = 'entreprises/form.html'

    def get_success_url(self):
        return reverse('entreprises:detail', kwargs={'pk': self.object.pk})


class EntrepriseUpdateView(UpdateView):
    model = Entreprise
    form_class = EntrepriseForm
    template_name = 'entreprises/form.html'
    context_object_name = 'entreprise'

    def get_success_url(self):
        return reverse('entreprises:detail', kwargs={'pk': self.object.pk})


class EntrepriseDeleteView(DeleteView):
    model = Entreprise
    template_name = 'entreprises/confirm_delete.html'
    context_object_name = 'entreprise'
    success_url = reverse_lazy('entreprises:liste')


# =============================================================================
# Partie 1 — Function-Based Views (référence, non routées)
# =============================================================================
def liste_entreprises(request):
    entreprises = (
        Entreprise.objects
        .select_related('gerant')
        .order_by('raison_sociale')
    )
    return render(request, 'entreprises/liste.html', {'entreprises': entreprises})


def detail_entreprise(request, pk):
    entreprise = get_object_or_404(
        Entreprise.objects.select_related('gerant'),
        pk=pk,
    )
    vehicules = entreprise.vehicules.order_by('immatriculation')
    expeditions = entreprise.expeditions.order_by('-created_at')
    offres = (
        entreprise.offre_set
        .select_related('expedition', 'vehicule')
        .order_by('-date_proposition')
    )
    return render(
        request,
        'entreprises/detail.html',
        {
            'entreprise': entreprise,
            'vehicules': vehicules,
            'expeditions': expeditions,
            'offres': offres,
        },
    )