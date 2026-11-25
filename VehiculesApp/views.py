from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import VehiculeForm
from .models import Vehicule


# =============================================================================
# Partie 2 — Class-Based Views (routées)
# =============================================================================
class VehiculeListView(LoginRequiredMixin, ListView):
    model = Vehicule
    template_name = 'vehicules/liste.html'
    context_object_name = 'vehicules'

    def get_queryset(self):
        return Vehicule.objects.select_related('entreprise').order_by('immatriculation')


class VehiculeDetailView(LoginRequiredMixin, DetailView):
    model = Vehicule
    template_name = 'vehicules/detail.html'
    context_object_name = 'vehicule'

    def get_queryset(self):
        return Vehicule.objects.select_related('entreprise')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['offres'] = (
            self.object.offre_set
            .select_related('expedition')
            .order_by('-date_proposition')
        )
        return context


class VehiculeCreateView(LoginRequiredMixin, CreateView):
    model = Vehicule
    form_class = VehiculeForm
    template_name = 'vehicules/form.html'

    def get_initial(self):
        # Préremplissage depuis la page d'une entreprise : ?entreprise=5
        initial = super().get_initial()
        entreprise_id = self.request.GET.get('entreprise')
        if entreprise_id:
            initial['entreprise'] = entreprise_id
        return initial

    def get_success_url(self):
        return reverse('vehicules:detail', kwargs={'pk': self.object.pk})


class VehiculeUpdateView(LoginRequiredMixin, UpdateView):
    model = Vehicule
    form_class = VehiculeForm
    template_name = 'vehicules/form.html'
    context_object_name = 'vehicule'

    def get_success_url(self):
        return reverse('vehicules:detail', kwargs={'pk': self.object.pk})


class VehiculeDeleteView(LoginRequiredMixin, DeleteView):
    model = Vehicule
    template_name = 'vehicules/confirm_delete.html'
    context_object_name = 'vehicule'
    success_url = reverse_lazy('vehicules:liste')


# =============================================================================
# Partie 1 — Function-Based Views (référence, non routées)
# =============================================================================
@login_required
def liste_vehicules(request):
    vehicules = (
        Vehicule.objects
        .select_related('entreprise')
        .order_by('immatriculation')
    )
    return render(request, 'vehicules/liste.html', {'vehicules': vehicules})


@login_required
def detail_vehicule(request, pk):
    vehicule = get_object_or_404(
        Vehicule.objects.select_related('entreprise'),
        pk=pk,
    )
    offres = (
        vehicule.offre_set
        .select_related('expedition')
        .order_by('-date_proposition')
    )
    return render(
        request,
        'vehicules/detail.html',
        {'vehicule': vehicule, 'offres': offres},
    )


@login_required
@require_POST
def supprimer_vehicule(request, pk):
    vehicule = get_object_or_404(Vehicule, pk=pk)
    vehicule.delete()
    return redirect('vehicules:liste')