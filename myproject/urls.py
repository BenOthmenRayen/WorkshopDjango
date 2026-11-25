"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from EntrepriseApp.views import InscriptionView

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='expeditions:liste', permanent=False), name='home'),
    path('admin/', admin.site.urls),
    path('comptes/inscription/', InscriptionView.as_view(), name='inscription'),
    # login (comptes/login/), logout (comptes/logout/), password_change... : routes sans app_name
    path('comptes/', include('django.contrib.auth.urls')),
    path('expeditions/', include('ExpeditionApp.urls')),
    path('vehicules/', include('VehiculesApp.urls')),
    path('offres/', include('OffreApp.urls')),
    path('entreprises/', include('EntrepriseApp.urls')),
]