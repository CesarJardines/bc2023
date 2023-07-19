"""TesisImp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
#Importamos la función handler404 para mostrar la vista de error 404 personalizada
from django.views import defaults as default_views
#Importamos las vistas de la aplicación django AMCE
from AMCE import views

admin.site.site_header = "Administrador de Búsqueda Colaborativa"
admin.site.site_title = "Administrador"
admin.site.index_title = "Bienvenido al administrador de Búsqueda Colaborativa"

#Indicamos la vista asociada al error 404
handler404 = 'AMCE.views.compartidas.custom_404_view'

#Indicamos la vista asociada al error 500
handler500 = 'AMCE.views.compartidas.custom_500_view'

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("AMCE.urls")),
    path('accounts/', include('django.contrib.auth.urls'))
]

urlpatterns += staticfiles_urlpatterns()