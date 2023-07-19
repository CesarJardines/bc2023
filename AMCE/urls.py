from django.contrib import admin
from django.urls import include, path
from AMCE.forms import CustomAuthForm
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

#se agrega para heroku
#from django.conf import settings 
#from django.conf.urls.static import static

# Views
import AMCE.views as views

app_name = "AMCE"
urlpatterns = [
#URLS CRECIÓN DE TIPOS DE USUARIOS
path('estudiante/vistaEstudiante/', views.vistaAlumno, name = 'vistaAlumno'),
path('profesor/vistaProfesor/', views.vistaProfesor, name = 'vistaProfesor'),
# URLS COMPARTIDAS
path('', views.index, name = 'index'),
path('registro/', views.signup, name = 'signup'),
path('registro/estudiante/', views.EstSignup.as_view(), name='EstSignup'),
path('registro/profesor/', views.ProfSignup.as_view(), name='ProfSignup'),
path('test_password', views.password_validation, name='test_password'),



# Recuperación de contraseñas
path('password_reset', 
    auth_views.PasswordResetView.as_view(
        template_name = 'registration/reset_password.html', 
        email_template_name = 'registration/reset_password_email.html', #me servira para el diseño del correo
        success_url = reverse_lazy('AMCE:password_reset_done')), 
    name='reset_password'),
path('reset_password_sent', auth_views.PasswordResetDoneView.as_view(template_name = 'registration/reset_password_sent.html'), name='password_reset_done'),
path('reset/<uidb64>/<token>/', 
    auth_views.PasswordResetConfirmView.as_view(
        template_name = 'registration/reset_password_form.html',
        success_url = reverse_lazy('AMCE:password_reset_complete')), name='password_reset_confirm'),
path('reset_password_complete', auth_views.PasswordResetCompleteView.as_view(template_name='registration/reset_password_done.html'), name='password_reset_complete'),

# URLS ESTUDIANTE
path('estudiante/MisGrupos/', views.EstMisGrupos, name = 'EstMisGrupos'),
path('estudiante/InscribirGrupo/', views.EstInscribirGrupo, name = 'EstInscribirGrupo'),
path('estudiante/Grupo/<str:id_grupo>/', views.EstPaginaGrupo, name = 'EstPaginaGrupo'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/actividad/aviso', views.AvisoNoContinuar, name = 'AvisoNoContinuar'),

path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/', views.AnalisisPreguntaInicial, name = 'AnalisisPreguntaInicial'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntaInicial/', views.postPreguntaInicial, name = 'PreguntaInicial'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntaInicial/actividad/aviso', views.AvisoNoContinuarAnalisis, name = 'AvisoNoContinuarAnalisis'), 
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntaInicial/FeedPreguntaInicial/', views.feedPIHecha, name = 'feedPIHecha'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntaInicial/DefiniciónPreguntaInicial/', views.defPreguntaInicial, name = 'defPreguntaInicial'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntasSecundarias/', views.PreguntasSecundarias, name = 'PreguntasSecundarias'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntasSecundarias/actividad/aviso', views.PSAvisoNoContinuar, name = 'PSAvisoNoContinuar'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntasSecundarias/evaluación', views.EvaluacionPS, name = 'EvaluacionPS'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntasSecundarias/evaluación/evaluacionsecundarias', views.EvaluacionPreSec, name = 'EvaluacionPreSec'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntasSecundarias/evaluación/aviso', views.AvisoNoContinuarEvaPS, name = 'AvisoNoContinuarEvaPS'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/PreguntasSecundarias/evaluación/actividad/plandeevaluación', views.PlanDeInvestigacion, name = 'PlanDeInvestigacion'),


# URLS ESTUDIANTE Paso 2
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/fuentes', views.seleccionaFuentes, name = "seleccionFuentes"),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/<str:definirFuente>/nueva-fuente', views.FuenteCreateView.as_view(), name = 'CrearFuenteView'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/editar-fuente/<pk>', views.FuenteUpdateView.as_view(), name = 'FuenteUpdateView'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/eliminar-fuente/<pk>', views.FuenteDeleteView.as_view(), name = 'FuenteDeleteView'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/instrucciones-evaluar-fuentes', views.instuccionesNuevaFuente, name = 'instuccionesNuevaFuente'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/EvaluarFuentes', views.evaluarFuentes, name = "evaluarFuentes"),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/EvaluarFuentes/aviso', views.AvisoNoContinuarEvaFuentes, name = "AvisoNoContinuarEvaFuentes"),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/EvaluarFuentes/aviso2', views.AvisoNoContinuarEvaFuentes2, name = "AvisoNoContinuarEvaFuentes2"),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/EvaluarFuentes/PlanDeInvestigaciónPaso2', views.EvaluarFuentesPlanInvestigación, name = "EvaluarFuentesPlanInvestigación"),



#URLS ESTUDIANTE PASO 3
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/RespuestaFuente', views.RespuestaFuente, name = 'RespuestaFuente'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/InstruccionesP3P1', views.InstruccionesP3P1, name = 'InstruccionesP3P1'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/AvisoNoContinuarP3P1', views.AvisoNoContinuarP3P1, name = 'AvisoNoContinuarP3P1'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/RespuestaSintetizada/<int:id_pregunta_id>', views.RespuestaSintetizada, name = 'RespuestaSintetizada'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/InstruccionesP3P2', views.InstruccionesP3P2, name = 'InstruccionesP3P2'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/AvisoNoContinuarP3P2', views.AvisoNoContinuarP3P2, name = 'AvisoNoContinuarP3P2'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/EvaluarRespuestaSintetizada/<int:id_pregunta_id>', views.EvaluarRespuestaSintetizada, name = 'EvaluarRespuestaSintetizada'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/InstruccionesP3P3', views.InstruccionesP3P3, name = 'InstruccionesP3P3'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/AvisoNoContinuarP3P3', views.AvisoNoContinuarP3P3, name = 'AvisoNoContinuarP3P3'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/RankingRespuestasP3P4', views.RankingRespuestasP3P4, name = 'RankingRespuestasP3P4'),


# URLS ESTUDIANTE Paso 4
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/ResponderPreguntaInicial', views.ResponderPreguntaInicial, name = "ResponderPreguntaInicial"),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/InstruccionesGeneraPDF', views.InstruccionesGeneraPDF, name = "InstruccionesGeneraPDF"),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/InstruccionesGeneraPDF/GeneraPDF', views.generaInvestigacionPDF, name = "GeneraInvestigacionPDF"),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/VotoRespuestaPI', views.VotoRespuestaPI, name = "VotoRespuestaPI"),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/MejorRespuestaPI', views.MejorRespuestaPI, name = "MejorRespuestaPI"),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/TrabajoFinal', views.TrabajoFinal, name = "TrabajoFinal"),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/Final', views.Final, name = "Final"),
#http://localhost:8000/estudiante/Grupo/56xjbvp/Tema/1/InstruccionesFinalP4/generaPDF'
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/InstruccionesPaso4', views.InstruccionesPaso4, name = "InstruccionesPaso4"),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/AvisoNoContinuarResponderPreguntaInicial', views.AvisoNoContinuarResponderPreguntaInicial, name = 'AvisoNoContinuarResponderPreguntaInicial'),
path('estudiante/Grupo/<str:id_grupo>/Tema/<str:id_tema>/AvisoNoContinuarVotoRespuestaPI', views.AvisoNoContinuarVotoRespuestaPI, name = 'AvisoNoContinuarVotoRespuestaPI'),



# URLS PROFESOR
#GRUPOS
path('profesor/MisGrupos/', views.ProfMisGrupos, name = 'ProfMisGrupos'),
path('profesor/CrearGrupo/', views.ProfCrearGrupo, name = 'ProfCrearGrupo'),
path('profesor/EditarGrupo/<str:id_grupo>', views.ProfEditarGrupo, name = 'ProfEditarGrupo'),
path('profesor/EliminarGrupo/<str:id_grupo>', views.ProfEliminarGrupo, name = 'ProfEliminarGrupo'),
path('profesor/Grupo/<str:id_grupo>/', views.ProfPaginaGrupo, name = 'ProfPaginaGrupo'),
path('profesor/Grupo/<str:id_grupo>/CrearEquipo/', views.ProfCrearEquipo, name = 'ProfCrearEquipo'),
path('profesor/Grupo/<str:id_grupo>/Equipo/<int:id_equipo>/', views.ProfPaginaEquipo, name = 'ProfPaginaEquipo'),
path('profesor/Grupo/<str:id_grupo>/AsignarTema/', views.ProfAsignarTemaGrupo, name = 'ProfAsignarTemaGrupo'),
path('profesor/Grupo/<str:id_grupo>/Tema/<int:id_tema>/', views.ProfTemaAsignado, name = 'ProfTemaAsignado'),
path('profesor/Grupo/<str:id_grupo>/Tema/<int:id_tema>/ProgresoGrupo', views.ProfProgresoGrupo, name = 'ProfProgresoGrupo'),
path('profesor/Grupo/<str:id_grupo>/Tema/<int:id_tema>/Equipo/<int:id_equipo>', views.ProfProgresoEquipo, name = 'ProfProgresoEquipo'),
path('profesor/Grupo/<str:id_grupo>/Tema/<int:id_tema>/Equipo/<int:id_equipo>/Retro/<int:paso>', views.ProfRetro, name = 'ProfRetro'),
#EQUIPOS
path('profesor/Grupo/<str:id_grupo>/EditarEquipo/<int:id_equipo>', views.ProfEditarEquipo, name = 'ProfEditarEquipo'),
path('profesor/Grupo/<str:id_grupo>/EliminarEquipo/<int:id_equipo>', views.ProfEliminaEquipo, name = 'ProfEliminaEquipo'),
#TEMAS
path('profesor/MisTemas/', views.ProfMisTemas, name = 'ProfMisTemas'),
path('profesor/CrearTema/', views.ProfCrearTema, name = 'ProfCrearTema'),
path('profesor/EditarTema/<str:id_tema>', views.ProfEditarTema, name = 'ProfEditarTema'),
path('profesor/EliminarTema/<str:id_tema>', views.ProfEliminarTema, name = 'ProfEliminarTema')
]

