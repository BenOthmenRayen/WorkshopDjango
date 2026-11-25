from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import EntrepriseCreationForm, EntrepriseForm, InscriptionForm
from .models import Entreprise


# =============================================================================
# Authentification — Inscription
# =============================================================================
class InscriptionView(CreateView):
    form_class = InscriptionForm
    template_name = 'registration/inscription.html'
    success_url = reverse_lazy('entreprises:ajouter')  # étape 2 : créer son entreprise

    def form_valid(self, form):
        response = super().form_valid(form)   # crée l'utilisateur (self.object)
        login(self.request, self.object)      # ouvre directement sa session
        return response


# =============================================================================
# Partie 2 — Class-Based Views (routées)
# =============================================================================
class EntrepriseListView(LoginRequiredMixin, ListView):
    model = Entreprise
    template_name = 'entreprises/liste.html'
    context_object_name = 'entreprises'

    def get_queryset(self):
        return Entreprise.objects.select_related('gerant').order_by('raison_sociale')


class EntrepriseDetailView(LoginRequiredMixin, DetailView):
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


class EntrepriseCreateView(LoginRequiredMixin, CreateView):
    model = Entreprise
    form_class = EntrepriseCreationForm
    template_name = 'entreprises/form.html'

    def dispatch(self, request, *args, **kwargs):
        # Relation 1–1 : un utilisateur qui gère déjà une entreprise ne peut pas en créer une deuxième
        entreprise = getattr(request.user, 'entreprise', None)
        if request.user.is_authenticated and entreprise is not None:
            return redirect('entreprises:detail', pk=entreprise.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # gerant : jamais choisi par le client, il est déduit de l'utilisateur connecté
        form.instance.gerant = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('entreprises:detail', kwargs={'pk': self.object.pk})


class EntrepriseUpdateView(LoginRequiredMixin, UpdateView):
    model = Entreprise
    form_class = EntrepriseForm
    template_name = 'entreprises/form.html'
    context_object_name = 'entreprise'

    def get_success_url(self):
        return reverse('entreprises:detail', kwargs={'pk': self.object.pk})


class EntrepriseDeleteView(LoginRequiredMixin, DeleteView):
    model = Entreprise
    template_name = 'entreprises/confirm_delete.html'
    context_object_name = 'entreprise'
    success_url = reverse_lazy('entreprises:liste')


# =============================================================================
# Partie 1 — Function-Based Views (référence, non routées)
# =============================================================================
@login_required
def liste_entreprises(request):
    entreprises = (
        Entreprise.objects
        .select_related('gerant')
        .order_by('raison_sociale')
    )
    return render(request, 'entreprises/liste.html', {'entreprises': entreprises})


@login_required
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