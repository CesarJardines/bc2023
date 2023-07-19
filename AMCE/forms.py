from gettext import translation
from django import forms 
from re import U
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, UsernameField
from django.contrib.auth.models import User
from django.forms import ModelForm
#from django.forms import ModelChoiceField #Importamos ModelChoiceField para sobreeescribir la representación de cadena de los modelos
from django.forms.widgets import PasswordInput, TextInput
from django.db import transaction
from django.db.models import Count

from django.utils.translation import gettext_lazy as _
from django.core.validators import URLValidator

from .models import *


DUMMY_CHOICES =(
	("1", "Placeholder"),
	("2", "Placeholder"),
)

class CustomAuthForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(CustomAuthForm, self).__init__(*args, **kwargs)
		
    username = UsernameField(widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Nombre de Usuario', 'id': 'username'}))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña',
            'id': 'password',
        }
	))

class EstSignupForm(UserCreationForm):
	
	class Meta(UserCreationForm):
		model = User
		fields = ['username', "first_name", "last_name", "email", "password1", "password2"]

	def save(self):
		user = super().save(commit=False)
		user.es_estudiante = True
		user.save()
		estudiante = Estudiante.objects.create(user_estudiante=user)
		return user

class FormInscribirGrupo(forms.Form):
	#Form el cual se usa para poder capturar un código de matería/clase dado por el profesor
	codigo = forms.CharField(label='Ingresa el código de la clase', max_length = 10)


class PreguntaInicial(forms.Form):
	#Form que captura la pregunta inicial de paso 1.1 del Modelo Gavilán
	contenido = forms.CharField(label='', max_length = 500, widget=forms.Textarea(attrs={'rows':2, 'placeholder': 'Ingresa tu pregunta inicial'}))


class RetroalimentacionPI(forms.Form):
	#Form que captura la pregunta inicial de paso 1.1 del Modelo Gavilán
	contenido = forms.CharField(label='', max_length = 500, widget=forms.Textarea(attrs={'rows':2, 'placeholder': 'Ingresa tu comentario'}))

# FORMS PROFESOR

class ProfSignupForm(UserCreationForm):
	class Meta(UserCreationForm.Meta):
		model = User
		fields = ['username', "first_name", "last_name", "email", "password1", "password2"]
	
	def save(self, commit=True):
		user = super().save(commit=False)
		user.es_profesor = True
		if commit:
			user.save()
		profesor = Profesor.objects.create(user_profesor=user)
		return user
class FormGrupo(ModelForm):
	class Meta:
		model = Grupo
		fields = ['nombre_grupo', 'materia', 'institucion']
		labels = {
            'nombre_grupo': _('Nombre del grupo')
        }

class FormTema(ModelForm):
	class Meta:
		model = Tema
		fields = ['nombre_tema']
		labels = {
            'nombre_tema': _('Nombre del tema')
        }


class FormCrearEquipo(forms.Form):
	nombre_equipo = forms.CharField(label='Nombre del equipo',max_length=100, widget= forms.TextInput(attrs={'class': 'form-control'}))
	integrantes = forms.ModelMultipleChoiceField(queryset=Estudiante.objects.all(), required=True, widget=forms.SelectMultiple)
	
	def clean_integrantes(self):
		value = self.cleaned_data['integrantes']
		if len(value) > 4 or len(value) < 2:
			raise forms.ValidationError("Los equipos deben de tener de 2 a 4 integrantes.")
		return value
	
class FormEditarEquipo(ModelForm):
	class Meta:
		model = Equipo
		fields = ['nombre_equipo']
		labels = {
            'nombre_tema': _('Nombre del equipo')
        }

class AsignarTemaGrupo(forms.Form):

	TIPO_ENTREGABLE = (
        ('0', 'Infografía'),
        ('1', 'Mapa conceptual'),
        ('2', 'Mapa mental'),
        ('3', 'Presentación'),
        ('4', 'Video'),
    )
	tema = forms.ModelChoiceField(queryset=Tema.objects.all(), empty_label="Seleccione un tema", required=True, widget=forms.Select(attrs={'class': 'form-select'}))
	#required=False para que se muestre el mensaje personalizado cuando el campo está vacío
	equipos = forms.ModelMultipleChoiceField(queryset=Equipo.objects.all(), required=False, widget=forms.SelectMultiple)
	preguntas_secundarias = forms.IntegerField(label='Número de preguntas secundarias por alumno', required=False, min_value=1, widget= forms.TextInput(attrs={'class': 'form-control'}))
	fuentes = forms.IntegerField(label='Número de fuentes por alumno', required=False,min_value=1, widget= forms.TextInput(attrs={'class': 'form-control'}))
	entregable = forms.ChoiceField(choices=TIPO_ENTREGABLE, widget=forms.Select(attrs={'class': 'form-select'}))
	
	#TODO: Poner una función que en general verifique si un campo están blanco para no tener estas 3 funciones
	
	def clean_equipos(self):
		"""Función que verifica si el campo equipos está vacío"""
		data = self.cleaned_data['equipos']
		if not data:
			raise forms.ValidationError("Este campo es obligatorio")
		return data
	
	def clean_preguntas_secundarias(self):
		"""Función que verifica si el campo preguntas_secundarias está vacío"""
		data = self.cleaned_data['preguntas_secundarias']
		if not data:
			raise forms.ValidationError("Este campo es obligatorio")
		return data
	
	def clean_fuentes(self):
		"""Función que verifica si el campo fuentes está vacío"""
		data = self.cleaned_data['fuentes']
		if not data:
			raise forms.ValidationError("Este campo es obligatorio")
		return data

class FormRetro(forms.Form):
	retro = forms.CharField(label='Comentarios', widget=forms.Textarea(attrs={'class': 'form-control'}))
'''
#Heredo del userCreationForm que viene en django
class CustomUserCreationForm(UserCreationForm):
	
	#Forms el cual se usa para la creación de un usuario nuevo, su uso se ve refejado en la base de
	#datos del modelo User que tiene django por defecto
	
	class Meta:
		#Se define que es el modelo User el cual se le agregaran los datos capturados
		model = User
		fields = ['username', "first_name", "last_name", "email", "password1", "password2"]

class FormInscribirGrupo(forms.Form):
	
	#Form el cual se usa para poder capturar un código de matería/clase dado por el profesor
	
	codigo = forms.CharField(label='Ingresa el código de la clase', max_length = 10)

class FormActividadPI(forms.Form):
	
	#Form que captura la pregunta inicial de paso 1.1 del Modelo Gavilán
	
	contenido = forms.CharField(label='', max_length = 500, widget=forms.Textarea(attrs={'rows':2, 'placeholder': 'Ingresa tu pregunta inicial'}))

#FORM EN ETAPA DE PRUEBA
class PostPreguntaInicial(forms.ModelForm):
	#Aqui se obtiene el campo de contenido de nuestro modelo Forms para Post
	content = forms.CharField(label='', widget=forms.Textarea(attrs={'rows':2, 'placeholder': 'Ingresa tu pregunta inicial'}))

	class Meta:
		model = Post
		fields = ['content']
'''


class NuevaFuenteForm(forms.Form):

	TIPO_FUENTE_CHOISES = (
        ('0', 'LIBRO'),
        ('1', 'REVISTA'),
        ('2', 'PERIODICO'),
        ('3', 'SITIO WEB'),
        ('4', 'VIDEO'),
        ('5', 'IMAGEN')
    )
	TIPO_RECURSO_CHOISES = (
        #('0', 'ARCHIVO'), Se agregara la opcion hasta encontrar una forma de almacenar archivos
        ('1', 'ENLACE'),
    )

	titulo = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Ingrese el título', 'class': 'form-control'}))
	autor = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Ingrese el autor', 'class': 'form-control'}))
	fecha_publicacion = forms.CharField(widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}))
	lugar = forms.CharField(widget=forms.TextInput(attrs={ 'placeholder': 'Ingrese el lugar de publicación', 'class': 'form-control'}))
	tipo_fuente = forms.ChoiceField(choices=TIPO_FUENTE_CHOISES, widget=forms.Select(attrs={'class': 'form-select'}))
	#tipo_recurso = forms.ChoiceField(choices=TIPO_RECURSO_CHOISES, widget=forms.Select(attrs={'class': 'form-select'}), initial='1')
	enlace = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Ingrese un enlace', 'class': 'form-control'}))


class EditFuenteForm(forms.ModelForm):

    class Meta:
        model = Fuente
        fields = (
			'titulo',
			'autor',
			'fecha_publicacion',
			'lugar',
			'tipo_fuente',
			#'tipo_recurso',
			'enlace',
        )

        widgets = {
            'titulo': forms.TextInput(
                attrs={
                    'placeholder': 'Ingrese el título',
					'class': 'form-control',
                }
            ),
			'autor': forms.TextInput(
                attrs={
                    'placeholder': 'Ingrese el autor',
					'class': 'form-control',
                }
            ),
			'fecha_publicacion': forms.DateInput(
               format='%Y-%m-%d', attrs={'type': 'date'}
			),
			'lugar': forms.TextInput(
                attrs={
                    'placeholder': 'Ingrese el lugar de publicación',
					'class': 'form-control',
                }
            ),
			'enlace': forms.TextInput(
                attrs={
					'id': 'enlace',
                    'placeholder': 'Ingrese el enlace',
					'class': 'form-control',
                }
            ),
			#'tipo_recurso': forms.Select(
			#	attrs={
			#		'class': 'form-select'
			#	}
			#),
			'tipo_fuente': forms.Select(
				attrs={
					'class': 'form-select'
				}
			)
			
        }

class EvaluarFuente(forms.Form):
	#Form que captura la pregunta inicial de paso 1.1 del Modelo Gavilán
	contenido = forms.CharField(label='', max_length = 700, widget=forms.Textarea(attrs={'rows':2, 'placeholder': 'Argumenta el por qué seleccionaste esa fuente'}))

"""
#Extendemos la clase ModelChoice para 
class MyModelChoiceField(ModelChoiceField):
	#Clase que extiende a ModelChoiceField
	def label_from_instance(self, obj):
		return '<button onclick="%s">Llévame a otro lado</button>' % obj.enlace
		#return 'Fuente: <a href="%s"></a>' % obj.enlace
"""

# Paso3.
class RespuestaPregSecFuente(forms.Form):
	respPregSecFuente = forms.CharField(label='Respuesta:', 
										max_length = 10000, 
										widget=forms.Textarea(attrs={'rows':10, 'placeholder': 'Respuesta extraida de la fuente'}))
	referenciaFuente = forms.CharField(label='Referencia de la fuente:', 
										max_length = 10000, 
										widget=forms.Textarea(attrs={'rows':5, 'placeholder': 'Referencia de la fuente'}))
	fuentes = forms.ModelChoiceField(queryset=Fuente.objects.all(), 
									empty_label=None, 
									#required=True, 
									widget=forms.Select(attrs={'class': 'form-select'}))

	def __init__(self, *args, **kwargs):
		id_defproblema = ''
		if 'id_defproblema' in kwargs.keys():
			id_defproblema = kwargs.pop('id_defproblema')
		super().__init__(*args, **kwargs)
		if id_defproblema != '':
			self.fields['fuentes'].queryset = Fuente.objects.filter(id_defproblema=id_defproblema, ganadora = True)

class RespuestaPregSecSintetizada(forms.Form):
	respPregSecSintetizada = forms.CharField(label='Respuesta sintetizada:', 
										max_length = 10000, 
										widget=forms.Textarea(attrs={'rows':7, 'placeholder': 'Respuesta sintetizada'}))
	
class RespuestaPreguntaInicialForm(forms.Form):
	#Form que captura la respuesta a la pregunta inicial en el paso 4.1
	contenido = forms.CharField(label='', max_length = 500, widget=forms.Textarea(attrs={'rows':13, 'placeholder': 'Ingresa tu respuesta a la pregunta inicial'}))

class RespuestaTrabajoFinalForm(forms.Form):
	#Form que captura la respuesta a la pregunta inicial en el paso 4.1
	contenido = forms.URLField(max_length=500, label='', widget=forms.URLInput(attrs={'rows':13, 'placeholder': 'Pega aquí el enlace de tu trabajo'}))
	#contenido = forms.CharField(validators=[URLValidator()])

