
from pyexpat import ParserCreate
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse,FileResponse
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from ..forms import *
from django.contrib.auth import authenticate, login
from django.template import RequestContext
from django.contrib.auth.models import User
from django.views.generic import (CreateView, UpdateView, DeleteView)
from django.views.generic.edit import FormView
from ..models import *
from ..decorators import student_required
from django.urls import reverse
#se importa para aumentar el contador de votos en feed
from django.db.models import F
from django.conf import settings
from django.core.mail import send_mail
import datetime
#Para obtener el max de votos en una pregunta inicial
from django.db.models import Max
#para la bíusqueda de fuentes del paso 2
import requests
#redirect
from django.urls import reverse_lazy
from js.momentjs import moment
from django.utils.decorators import method_decorator
#para harcordear el json
import json
from functools import partial, wraps
from django.forms import formset_factory
# Biblioteca utilizada para la creación del PDF
from fpdf import FPDF


class EstSignup(CreateView):
	model = User
	form_class = EstSignupForm
	template_name = 'registration/signup_form.html'
	
	def get_context_data(self, **kwargs):
		kwargs['user_type'] = 'Estudiante'
		return super().get_context_data(**kwargs)

	def form_valid(self, form):
		user = form.save()
		login(self.request, user)
		return redirect('AMCE:EstMisGrupos')
		

@student_required
def vistaAlumno(request):
	current_user = get_object_or_404(User, pk=request.user.pk)
	#Comento esta linea porque me daba error sin saber el por qué
	#grupos_inscritos = Estudiante.objects.filter(user_estudiante=current_user.id).values_list('grupos_inscritos', flat=True)

	#Se agregan estas lineas con el fin de sustituir la linea de arriba 
	estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
	#Consultamos todos grupos a los cual el usuario estudiante está inscrito y los mostramos
	grupos_inscritos = estudiante.grupos_inscritos.all()

	return render(request,"estudiante/MisGrupos.html", {'grupos_inscritos':grupos_inscritos,'current_user':current_user})

@student_required
@login_required
def EstInscribirGrupo(request):
	'''
	Función para que un usuario alumno pueda inscribir una matería dado un código de clase
	por parte del profesor 
	'''
	current_user = get_object_or_404(User, pk=request.user.pk)
	grupos_inscritos = Estudiante.objects.filter(user_estudiante=request.user.pk)
	
	if request.method == 'POST':
		form = FormInscribirGrupo(request.POST)
		if form.is_valid():
			repetido = Estudiante.objects.filter(user_estudiante=current_user.id, grupos_inscritos=form.cleaned_data['codigo'])
			codigo = form.cleaned_data['codigo']
			try:
				if repetido.exists():
					messages.success(request, 'Ya estás inscrito en el grupo con código ' + codigo)
					return redirect(to="AMCE:EstMisGrupos")
				else:
					grupo = Grupo.objects.get(id_grupo=codigo) 
					grupo_a_inscribir= Estudiante(user_estudiante_id=current_user.id)
					grupo_a_inscribir.grupos_inscritos.add(grupo.id_grupo)
					grupo_a_inscribir.save()
					messages.success(request, 'Grupo inscrito')
					return redirect(to="AMCE:EstMisGrupos")
			except Grupo.DoesNotExist:
				messages.error(request, 'El código de grupo que ingresaste no es válido')
				return redirect(to="AMCE:EstMisGrupos")
	else:
		form = FormInscribirGrupo()

	return render(request, 'estudiante/InscribirGrupo.html', {'form': form})

@student_required
@login_required
def EstMisGrupos(request):
	'''
	Función la cual muestra al usuario alumno los grupos a los cuales está inscrito  
	'''
	current_user = get_object_or_404(User, pk=request.user.pk)
	#Obtenemos el objeto estudiante actual
	estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
	#Consultamos todos grupos a los cual el usuario estudiante está inscrito y los mostramos
	grupos_inscritos = estudiante.grupos_inscritos.all()

	return render(request,"estudiante/MisGrupos.html",{'grupos_inscritos':grupos_inscritos, 'current_user':current_user})

@student_required
@login_required
def EstPaginaGrupo(request, id_grupo):
	'''
	Función la cual muestra los temas asignados al equipo del usuario.
	Un usuario debe de tener un equipo pero este puede ser diferente para cada tema, lo que se hace es que 
	se haga una búsqueda que llegue hasta la tabla Asignar, la cual muestra que equipos (id) tienen el tema (id)
	Args:
		id_grupo (char): código de la materia 
	'''
	#Se verifica que el usuario tenga equipo
	try:
		current_user = get_object_or_404(User, pk=request.user.pk)
		#Se obtiene el objeto Equipo de nuestro actual estudiante
		print("current_user", current_user)
		equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
		print("equipo", equipo)
		#Consultamos los temas asigandos que tiene el equipo del usuario y los filtramos por materia 
		temas_asignados = equipo.temas_asignados.filter()
		# print("temas_asignados", temas_asignados[0].id_tema)
		#Consultamos e identificamos el grupo actual para mostrar los datos de grupo y materia en el header 
		grupo = Grupo.objects.filter(id_grupo = id_grupo)
	#De no tener equipo se le notifica que aún no tiene equipo
	except Equipo.DoesNotExist:
		messages.error(request, 'Aún no tienes equipo, espera a que tu profesor te asigne uno.')
		return redirect('AMCE:EstMisGrupos')
	

	return render(request, 'estudiante/PaginaGrupo.html', {'grupo':grupo.first(),'id_grupo':id_grupo ,'temas_asignados':temas_asignados, 'current_user':current_user})	

@student_required
@login_required
def AvisoNoContinuar(request, id_tema, id_grupo):
	'''
	Funcion para mostrar el aviso de que el equipo aún no acaba esta parte
	'''
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#obtengo todos los integrantes del equipo con ese id_equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo).values_list('estudiantes', flat=True)
	#Se consulta el equipo actual del usuario para pasarselo como parámetro en defProbPreguntaQuery
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema

	#Por cada integrante del equipo se va a buscar su participación de la PI
	for i in integrantesEquipo:
		#Si se encuentra la participación de un usuario no pasa nada
		try:
			obj = Pregunta.objects.get(id_pregunta__estudiante_part=i, definirProb_pregunta_id=defProbPreguntaQuery, tipo_pregunta=1)
		#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
		except Pregunta.DoesNotExist:
			#Obtenemos el id para posteriormente usar el nombre del usuario en el cuerpo del mensaje
			obj2 = User.objects.get(id=i)
			send_mail(
    		'Aviso, Faltas tu!',
    		f'Hola {obj2.first_name}, tu equipo ya realizó la actividad de formular la pregunta inicial del tema {temaNombre}, faltas tu! Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.',
    		settings.EMAIL_HOST_USER,
    		[obj2.email],
    		fail_silently=False,
			)
	
	return render(request, 'estudiante/paso1/AvisoNoContinuar.html', {'id_tema':id_tema, 'id_grupo':id_grupo, 'current_user':current_user})

@student_required
@login_required
def postPreguntaInicial(request, id_tema ,id_grupo):
	'''
	Función la cual habilita que un usuario pueda ingresar una función principal mediante un form.

	Args:
		tema (string): El tema asignado de la pregunta inicial

		codigo (string): codigo de la materia 
	
	'''
	#Consulta para obtener el tema de la actividad asignada y mostrarla en el template, así como usarla en defProbPreguntaQuery
	temaPreguntaInicial = Tema.objects.get(id_tema=id_tema)
	current_user = get_object_or_404(User, pk=request.user.pk)
	#Se consulta el equipo actual del usuario para pasarselo como parámetro en defProbPreguntaQuery
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = temaPreguntaInicial.id_tema)
	#Obtenemos todas las participaciones del equipo de nuestro actual usuario (AGREGAR CÓMO PARÁMETRO 1 COMO PREGUNTA INICIAL)
	numTotalPartici = Pregunta.objects.filter(definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo_pregunta=1)
	#Obtenemos los integrantes del  equipo (ARREGLAR ESTO)
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)

	#Se obtienen los ids del usuario actual 
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)
	#Se obtienen los id's de id_pregunta del numTotalPartici que asocia al equipo del actual estudiante y el del tema asignado
	idsUsuarioPregunta = numTotalPartici.values_list('id_pregunta', flat=True)
	#Verificamos para ver en qué paso se encuentra el equipo y redireccionarlo a la función correspondiente
	if defProbPreguntaQuery.paso == 1:
		#Se pregunta si el numero total de particiapciones con id_definirProb del equipo es igual al número de integrantes
		if numTotalPartici.count() == integrantesEquipo.count():
			#Si el numero de integrantes coincide con el número de participaciones entonces pasamos al siguente paso
			return redirect('AMCE:AnalisisPreguntaInicial',id_grupo=id_grupo, id_tema=id_tema)
			#Si no lo mandamos al modal de aviso 
		else:
			#Verificamos si hay una intersección entre los ids de participaciones del usuario con los ids de las preguntas asociadas a un id de DefinirPregunta
			if bool(set(idsUsuarioParticipacion)&set(idsUsuarioPregunta)):
				#Si hay un elemento en comun quiere decir que ya tiene su participación
				return redirect('AMCE:AvisoNoContinuar' , id_grupo=id_grupo, id_tema=id_tema)
			#Si no hay participación previa del usuario en este paso, quiere decir que no hay hecho este paso y se le permite hacerlo
			else:
				#Validación del forms de PreguntaInicial
				if request.method == 'POST':
					#Se captura la información proporcionada en el form del template
					form = PreguntaInicial(request.POST)
					if form.is_valid():
						#Creamos un elemento para nuestra tabla de actividad 
						nuevaParticipacion = ParticipacionEst(contenido = form.cleaned_data['contenido'],
													estudiante_part_id = current_user.id)
						messages.success(request, 'Pregunta inicial guardada')
						nuevaParticipacion.save()
						#De igual menera creamos un elemento del modelo Pregunta con el id_actividad que se acabó de crear con la variable nuevaParticipacion
						nuevoCampoPregunta = Pregunta(id_pregunta_id=nuevaParticipacion.id_actividad, tipo_pregunta=1, definirProb_pregunta_id=defProbPreguntaQuery.id_definirProb)
						nuevoCampoPregunta.save()

						#Participación actual del estudiante del tema actual para verificar si es la uñtima participación que el equipo necesita para continuar con el sig paso
						par = Pregunta.objects.get(id_pregunta__estudiante_part_id = current_user.id ,definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo_pregunta=1)
						#Entero el cual define la ultima participación del equipo
						ultimaParticipacion = integrantesEquipo.count()-1
						try:
							#Si la participación que hizo el estudiante es la ultima participación que se espera, manda el correo
							if par == numTotalPartici[ultimaParticipacion]:
								print('manda correo')
								#Se les notifica a los integrantes del equipo que todos han acabado
								for i in integrantesEquipo:
									nombreUsuario = User.objects.get(id=i)
									send_mail(
									'Tu equipo ya acabó de formular la pregunta inicial!',
									f'Hola {nombreUsuario.first_name}, el último integrante de tu equipo ha terminado de formular la pregunta inicial del tema {temaPreguntaInicial.nombre_tema}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.',
									settings.EMAIL_HOST_USER,
									[nombreUsuario.email],
									fail_silently=False,
									)
						#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
						except IndexError:
							print('no se manda correo correo')
						#Se redirige a la pregunta inicial para que se valide si puede avanzar o no al siguente paso
						return redirect('AMCE:PreguntaInicial',id_grupo=id_grupo, id_tema=id_tema)
				else:
					form = PreguntaInicial()
	#Redireccionamos si el sistema encuentra que está en el paso dos
	if defProbPreguntaQuery.paso == 2:
		return redirect('AMCE:seleccionFuentes',id_grupo=id_grupo, id_tema=id_tema)
	
	if defProbPreguntaQuery.paso == 3:
		return redirect('AMCE:RespuestaFuente',id_grupo=id_grupo, id_tema=id_tema)
	if defProbPreguntaQuery.paso == 4:
		return redirect('AMCE:InstruccionesPaso4',id_grupo=id_grupo, id_tema=id_tema)
	return render(request, 'estudiante/paso1/PreguntaInicial.html', {'id_tema':id_tema,'id_grupo':id_grupo ,'temaPreguntaInicial':temaPreguntaInicial, 'form': form, 'current_user':current_user})

@student_required
@login_required
def AnalisisPreguntaInicial(request, id_tema ,id_grupo):
	#corroborar si ya comentaron las preguntas iniciales
	temaPreguntaInicial = Tema.objects.get(id_tema=id_tema)
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = temaPreguntaInicial.id_tema)
	numTotalPartici = Pregunta.objects.filter(definirProb_pregunta=defProbPreguntaQuery.id_definirProb)
	#integrantesEquipo = Equipo.objects.filter(estudiantes__grupos_inscritos=equipo.grupo_equipo_id, temas_asignados__id_tema=id_tema)
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)

	comentariosPregunta = ComentariosPreguntaInicial.objects.filter(pregunta__definirProb_pregunta = defProbPreguntaQuery).values_list('participacionEst_id', flat=True)
	#Se obtienen los ids del usuario actual 
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)
	#Si todos los integrantes retrolimentaron la pregunta inicial se redirecciona al siguente paso
	if comentariosPregunta.count() == integrantesEquipo.count():
		#Redireccionamos al usuario a la pantalla Definición de la Pregunta inicial
		return redirect('AMCE:defPreguntaInicial', id_grupo=id_grupo, id_tema=id_tema)
	else:
		print('ir a analisis pregunta inicial')
		#Se corrobora si ya tiene participación en la actividad
		if bool(set(idsUsuarioParticipacion)&set(comentariosPregunta)):
			#Si ya tiene una retroalimentación se le redireciona a la pantalla de No continuar
			return redirect('AMCE:AvisoNoContinuarAnalisis' , id_grupo=id_grupo, id_tema=id_tema)
	return render(request,"estudiante/paso1/Actividad.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'current_user':current_user})

@student_required
@login_required
def feedPIHecha(request, id_tema ,id_grupo):
	'''
	Esta es una de las dos funciones semejantes que se tienen en el views de estudiante, la unica diferencia que tienen 
	es que regresan un template diferente. Las funciones cuentan los integrantes del equipo del usuario actual relacionado al tema 
	de la pregunta inicial 
		Args:
		id_tema (string): El tema asignado de la pregunta inicial

		id_grupo (string): codigo de la materia 
	'''
	temaPreguntaInicial = Tema.objects.get(id_tema=id_tema)
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = temaPreguntaInicial.id_tema)
	numTotalPartici = Pregunta.objects.filter(definirProb_pregunta=defProbPreguntaQuery.id_definirProb)
	#integrantesEquipo = Equipo.objects.filter(estudiantes__grupos_inscritos=equipo.grupo_equipo_id, temas_asignados__id_tema=id_tema)
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	#Se hace una consulta para input text del template con atributo comentario, esto devuelve la lista con lo
	comentario = request.POST.getlist('comentario')
	#Se quitan los caracteres vacios
	respuesta = "".join(string for string in comentario if len(string) > 0)

	#Se obtienen los ids del usuario actual 
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)

	#Se obtienen los id's de ComentariosPreguntaInicial asociados al tema asignado y equipo del usuario. Sacamos las participacionEst_id y aplicamos intersección para revisar si ya hay una participación previa 
	preguntasIniUsuario = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, tipo_pregunta=1).values_list('id_pregunta', flat=True)
	#comentariosPregunta = ComentariosPreguntaInicial.objects.filter(pregunta__definirProb_pregunta = defProbPreguntaQuery).values_list('participacionEst_id', flat=True)


	#Se obtienen los id's de ComentariosPreguntaInicial asociados al tema asignado y equipo del usuario. Sacamos las participacionEst_id y aplicamos intersección para revisar si ya hay una participación previa 
	comentariosPregunta = ComentariosPreguntaInicial.objects.filter(pregunta__definirProb_pregunta = defProbPreguntaQuery).values_list('participacionEst_id', flat=True)
	print(comentariosPregunta)

	#Se verifica que numero total de comentarios con los ids de participaciones estudiantes sean las mismas a los integrantes, de serlo es porque todos comentarno una PI
	if comentariosPregunta.count() == integrantesEquipo.count():
		print(comentariosPregunta)
		print(integrantesEquipo.count())
		#Redireccionamos al usuario a la pantalla Definición de la Pregunta inicial
		return redirect('AMCE:defPreguntaInicial', id_grupo=id_grupo, id_tema=id_tema)
	else:
		#----------------------
		#Si faltan integrantes por retroalimentar la pregunta inicial, se verifica si ya retroalimentó anteriormente 
		if bool(set(idsUsuarioParticipacion)&set(comentariosPregunta)):
			#Si ya tiene una retroalimentación se le redireciona a la pantalla de No continuar
			return redirect('AMCE:AvisoNoContinuarAnalisis' , id_grupo=id_grupo, id_tema=id_tema)
		else:
			#Si no hay retroalimentación previa, se le permite entrar para que haga su retroalimentación
			if request.method == 'POST':
				#se captura el nombre de usuario por el cual se está votando
				voto = request.POST.get("voto")

				#Preguntamos si el voto es nulo (no seleccionó ninguna pregunta inicial)
				if(voto == None):
					#Redireccionamos a otra página
					print("Formulario inválido, se redirecciona a la misma página")
					return render(request, 'estudiante/paso1/FeedPreguntaInicialHecha.html', {'temaPreguntaInicial':temaPreguntaInicial, 'numTotalPartici':numTotalPartici, 'current_user':current_user})

				#Preguntamos si el comentario está vacio
				if(len(respuesta) == 0):
					#En este caso redireccionamos a la misma página
					print("Formulario inválido, se redirecciona a la misma página")
					return render(request, 'estudiante/paso1/FeedPreguntaInicialHecha.html', {'temaPreguntaInicial':temaPreguntaInicial, 'numTotalPartici':numTotalPartici, 'current_user':current_user})
				
				#comentario = request.POST.get("comentario")
				print(respuesta)
				print(voto)
				nuevaParticipacion = ParticipacionEst(contenido = respuesta,
														estudiante_part_id = current_user.id)
				nuevaParticipacion.save()
				id_PreguntaAsociadaAUsuario = Pregunta.objects.filter(id_pregunta__estudiante_part_id=voto, definirProb_pregunta=defProbPreguntaQuery).values_list('id_pregunta', flat=True)

				nuevoComentario = ComentariosPreguntaInicial(participacionEst_id = nuevaParticipacion.id_actividad, pregunta_id = id_PreguntaAsociadaAUsuario)
				nuevoComentario.save()
				#Se agrega voto y se agrega comentario a las respectivas celdas de la Bade de Datos
				voto_sumar = Pregunta.objects.filter(id_pregunta__estudiante_part_id=voto, definirProb_pregunta=defProbPreguntaQuery).update(votos=F('votos')+1)

				contador = 0
				for i in integrantesEquipo:
					try:
						#Obtenemos los usuarios que aún les falta su participación y se les manda correo
						if bool(set(idsParticipacionUsuarioN)&set(comentariosPregunta)):
							print()
					#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
					except:
						#Obtenemos el id para posteriormente usar el nombre del usuario en el cuerpo del mensaje
						print('todo está bien')
					#para cada integrante del equipo se verifican sus participaciones
					idsParticipacionUsuarioN = ParticipacionEst.objects.filter(estudiante_part=i).values_list('id_actividad', flat=True)
					print(idsParticipacionUsuarioN)
					print(comentariosPregunta)
					if bool(set(idsParticipacionUsuarioN)&set(comentariosPregunta)):
						print('entré al if')
						contador = contador + 1
						print('usuario')
						print(i)
						print('contador')
						print(contador)
		
					if contador == integrantesEquipo.count():
						print('se manda correo')
				messages.success(request, 'Comentario y voto guardado correctamente')
				return redirect('AMCE:feedPIHecha', id_grupo=id_grupo, id_tema=id_tema)
	return render(request, 'estudiante/paso1/FeedPreguntaInicialHecha.html', {'temaPreguntaInicial':temaPreguntaInicial, 'numTotalPartici':numTotalPartici, 'current_user':current_user})

@student_required
@login_required
def AvisoNoContinuarAnalisis(request, id_tema, id_grupo):
	'''
	Esta es una de las dos funciones semejantes que se tienen en el views de estudiante, la unica diferencia que tienen 
	es que regresan un template diferente. Las funciones cuentan los integrantes del equipo del usuario actual relacionado al tema 
	de la pregunta inicial 
		Args:
		tema (string): El tema asignado de la pregunta inicial

		codigo (string): codigo de la materia 
	'''
	current_user = get_object_or_404(User, pk=request.user.pk)
	#Se consulta el equipo actual del usuario para pasarselo como parámetro en defProbPreguntaQuery
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#obtengo todos los integrantes del equipo con ese id_equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo).values_list('estudiantes', flat=True)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo, tema_definirProb_id = id_tema)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema

	#Se obtienen los ids del usuario actual 
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)
	#Se obtienen los id's de ComentariosPreguntaInicial asociados al tema asignado y equipo del usuario. Sacamos las participacionEst_id y aplicamos intersección para revisar si ya hay una participación previa 
	comentariosPregunta = ComentariosPreguntaInicial.objects.filter(pregunta__definirProb_pregunta = defProbPreguntaQuery).values_list('participacionEst_id', flat=True)
	
	#Por cada integrante del equipo se va a buscar su participación de la PI
	for i in integrantesEquipo:
		nombreUsuario = User.objects.get(id=i)
		#Si se encuentra la participación de un usuario no pasa nada
		#Se consulta integrante x integrante para ver si tiene participación 
		integranteN = ParticipacionEst.objects.filter(estudiante_part=i).values_list('id_actividad', flat=True)
		try:
			#Obtenemos los usuarios que aún les falta su participación y se les manda correo
			if not(bool(set(integranteN)&set(comentariosPregunta))):
				print('Manda correo a los que no han hecho la actividad')
				send_mail(
				'Aviso, Faltas tu!',
				f'Hola {nombreUsuario.first_name}, tu equipo ya terminó de evaluar la pregunta inicial del tema {temaNombre}, faltas tu! Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.',
				settings.EMAIL_HOST_USER,
				[nombreUsuario.email],
				fail_silently=False,
				)
		#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
		except:
			#Obtenemos el id para posteriormente usar el nombre del usuario en el cuerpo del mensaje
			print('todo está bien')
	#envioCorreo = envioCorreoAvisoNoContinuar()
	return render(request, 'estudiante/paso1/AnalisisAviso.html', {'id_tema':id_tema, 'id_grupo':id_grupo, 'current_user':current_user})

@student_required
@login_required
def defPreguntaInicial(request,  id_tema, id_grupo):
	'''
	Función que muestra el avance hasta el paso de evaluar la pregunta inicial, se regresa como contexto la pregunta inicial que más fue votada y 
	los comentarios a esa pregunta inicial más votada
		Args:
		id_tema (string): El id del tema asignado de la pregunta inicial

		id_grupo (string): El código de la materia 
	'''
	temaPreguntaInicial = Tema.objects.get(id_tema=id_tema)
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#obtenemos el equiopo y tema a los cuales se asocian 
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = temaPreguntaInicial.id_tema)

	#Preguntas iniciales del equipo
	pregunta = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery)

	#Obtenemos todas las participaciones del equipo de nuestro actual usuario 
	numTotalPartici = Pregunta.objects.filter(definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo_pregunta=2)

	#Se obtienen los ids de las participaciones del usuario actual 
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)
	#Se obtienen las preguntas secundarias para ver si se le redirecciona al paso de no continuar o seguir la actividad
	preguntasSecUsuario = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, tipo_pregunta=2).values_list('id_pregunta', flat=True)
	#Obtenemos los integrantes del  equipo 
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	#Comprobamos si tienen preguntas secundarias ya hechas
	noPreguntasSec = DefinirProblema.objects.get(equipo_definirProb_id= equipo.id_equipo, tema_definirProb_id =id_tema).preguntas_secundarias

	#Se obtienen los id's de ComentariosPreguntaInicial asociados al tema asignado y equipo del usuario. Sacamos las participacionEst_id y aplicamos intersección para revisar si ya hay una participación previa 
	preguntasIniUsuario = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, tipo_pregunta=1).values_list('id_pregunta', flat=True)
	print(preguntasIniUsuario)

	#Se pregunta si el numero total de particiapciones con id_definirProb del equipo es igual al número de integrantes
	if numTotalPartici.count() == (integrantesEquipo.count() * noPreguntasSec):
		#Si el numero de integrantes coincide con el número de participaciones entonces pasamos al siguente paso
		return redirect('AMCE:EvaluacionPS', id_grupo=id_grupo, id_tema=id_tema)
		#Si no lo mandamos al modal de aviso 
	else:
		#Si faltan integrantes por retroalimentar la pregunta inicial, se verifica si ya retroalimentó anteriormente 
		if bool(set(idsUsuarioParticipacion)&set(preguntasSecUsuario)):
			#Si ya tiene una retroalimentación se le redireciona a la pantalla de No continuar
			return redirect('AMCE:PSAvisoNoContinuar' , id_grupo=id_grupo, id_tema=id_tema)
		else:
			#Buscamos cual es la pregunta inicial con más votos, como lo ordena en orden ascendente, si por alguna razón hay un empate en votos de las PI se tomará la primera
			masVotada = pregunta.order_by('-votos')[0]
			#Actualizamos el campo ganadora a True a la pregunta inicial más votada
			preguntaGanadora = Pregunta.objects.filter(id_pregunta_id=masVotada.id_pregunta_id).update(ganadora=True)
			preguntaSel = Pregunta.objects.get(id_pregunta_id=masVotada.id_pregunta_id, definirProb_pregunta = defProbPreguntaQuery, ganadora=True)

			#Se obtienen los comentarios de la pregunta ganadora para mostrarlos en la pantalla de definición de la pregunta inicial
			comentariosPregunta = ComentariosPreguntaInicial.objects.filter(pregunta_id = masVotada)	
			

	return render(request, "estudiante/paso1/DefinicionPreguntaIncial.html",{'id_tema': id_tema, 'id_grupo':id_grupo, 'preguntaSel':preguntaSel, 'comentariosPregunta':comentariosPregunta, 'current_user':current_user})

@student_required
@login_required
def PreguntasSecundarias(request,  id_tema, id_grupo):
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	#Obtenemos todas las participaciones del equipo de nuestro actual usuario 
	numTotalPartici = Pregunta.objects.filter(definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo_pregunta=2)

	#Obtenemos los integrantes del  equipo
	#integrantesEquipo = Equipo.objects.filter(estudiantes__grupos_inscritos=equipo.grupo_equipo_id, temas_asignados__id_tema=id_tema)
	#integrantesEquipoCorreo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)

	#Se obtienen los ids de las participaciones del usuario actual 
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)
	#Se obtienen los id's de ComentariosPreguntaInicial asociados al tema asignado y equipo del usuario. Sacamos las participacionEst_id y aplicamos intersección para revisar si ya hay una participación previa 
	preguntasSecUsuario = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, tipo_pregunta=2 ).values_list('id_pregunta', flat=True)
	#Consulta para obtener la pregunta inicial ganadora y mostrala en el template
	pregunta = Pregunta.objects.get(definirProb_pregunta = defProbPreguntaQuery, ganadora=True)
	#Consutlar los id de los integrantes del equipo para mandar correo
	integrantesEquipoCorreo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	#Obtenemos el número de preguntas secundarias que tiene el tema del equipo
	noPreguntasSec = DefinirProblema.objects.get(equipo_definirProb_id= equipo.id_equipo,tema_definirProb_id = id_tema).preguntas_secundarias
	#Se pregunta si el numero total de particiapciones con id_definirProb del equipo es igual al número de integrantes
	if numTotalPartici.count() == (integrantesEquipoCorreo.count() * noPreguntasSec):
		#Si el numero de integrantes coincide con el número de participaciones entonces pasamos al siguente paso
		return redirect('AMCE:EvaluacionPS', id_grupo=id_grupo, id_tema=id_tema)
		#Si no lo mandamos al modal de aviso 
	else:
		#Si faltan integrantes por retroalimentar la pregunta inicial, se verifica si ya retroalimentó anteriormente 
		if bool(set(idsUsuarioParticipacion)&set(preguntasSecUsuario)):
			#Si ya tiene una retroalimentación se le redireciona a la pantalla de No continuar
			return redirect('AMCE:PSAvisoNoContinuar' , id_grupo=id_grupo, id_tema=id_tema)
		else:
			if request.method == 'POST':
				comentario = request.POST.getlist('preguntaSecundaria')

				#For para verificar que cada campo no sea vacío
				for i in comentario:
					#Preguntamos sino se ingresó nada a los campos
					if(i == ""):
						#En este caso redireccionamos de nuevo a la misma página
						print("Formulario inválido, se redirecciona a la misma página")
						return render(request, "estudiante/paso1/PreguntasSecundarias.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'range': range(noPreguntasSec), 'temaNombre':temaNombre, 'pregunta':pregunta, 'noPreguntasSec':noPreguntasSec, 'current_user':current_user})

				for i in comentario:
					#Creamos un elemento para nuestra tabla de actividad 
					nuevaParticipacion = ParticipacionEst(contenido = i,
															estudiante_part_id = current_user.id)
					nuevaParticipacion.save()
					#De igual menera creamos un elemento del modelo Pregunta con el id_actividad que se acabó de crear con la variable nuevaParticipacion
					nuevoCampoPregunta = Pregunta(id_pregunta_id=nuevaParticipacion.id_actividad, tipo_pregunta=2, definirProb_pregunta_id=defProbPreguntaQuery.id_definirProb)
					nuevoCampoPregunta.save()
					#Se redirige a la pregunta inicial para que se valide si puede avanzar o no al siguente paso
				#Participación actual del estudiante del tema actual para verificar si es la uñtima participación que el equipo necesita para continuar con el sig paso
				par = Pregunta.objects.filter(id_pregunta__estudiante_part_id = current_user.id ,definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo_pregunta=2)
				#Entero el cual define la ultima participación del equipo
				ultimaParticipacion = (integrantesEquipoCorreo.count() * noPreguntasSec)-1
				try:
					#Si la participación que hizo el estudiante es la ultima participación que se espera, manda el correo
					if par[noPreguntasSec-1] == numTotalPartici[ultimaParticipacion]:
						print('manda correo')
						#Se les notifica a los integrantes del equipo que todos han acabado
						for i in integrantesEquipoCorreo:
							nombreUsuario = User.objects.get(id=i)
							send_mail(
							'Tu equipo ya acabó de formular las preguntas secundaria!',
							f'Hola {nombreUsuario.first_name}, el último integrante de tu equipo ha terminado de formular las preguntas secundarias del tema {temaNombre}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.',
							settings.EMAIL_HOST_USER,
							[nombreUsuario.email],
							fail_silently=False,
							)
				#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
				except IndexError:
					print('no se manda correo correo')
				messages.success(request, 'Preguntas secundarias guardadas correctamente')
				return redirect('AMCE:PreguntasSecundarias',  id_grupo=id_grupo, id_tema=id_tema)


	return render(request, "estudiante/paso1/PreguntasSecundarias.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'range': range(noPreguntasSec), 'temaNombre':temaNombre, 'pregunta':pregunta, 'noPreguntasSec':noPreguntasSec, 'current_user':current_user})

@student_required
@login_required
def PSAvisoNoContinuar(request,  id_tema, id_grupo):
	current_user = get_object_or_404(User, pk=request.user.pk)
	#Se consulta el equipo actual del usuario para pasarselo como parámetro en defProbPreguntaQuery
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	#Obtenemos todas las participaciones del equipo de nuestro actual usuario 
	numTotalPartici = Pregunta.objects.filter(definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo_pregunta=2)
	#Obtenemos los integrantes del  equipo
	integrantesEquipo = Equipo.objects.filter(estudiantes__grupos_inscritos=equipo.grupo_equipo_id, temas_asignados__id_tema=id_tema)
	#Consulta para obtener los integrantes de equipo para mandar correo
	integrantesEquipoCorreo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Mandar correo a los que aún no tienen su participación de pregunta secundaria
	noPreguntasSec = DefinirProblema.objects.get(id_definirProb=defProbPreguntaQuery.id_definirProb ,tema_definirProb_id = id_tema).preguntas_secundarias
	#Se pregunta si el numero total de particiapciones con id_definirProb del equipo es igual al número de integrantes
	if numTotalPartici.count() == (integrantesEquipo.count() * noPreguntasSec):
		#Si el numero de integrantes coincide con el número de participaciones entonces pasamos al siguente paso
		return redirect('AMCE:EvaluacionPS', id_grupo=id_grupo, id_tema=id_tema)
		#Si no lo mandamos al modal de aviso 

	print(integrantesEquipoCorreo)
	for i in integrantesEquipoCorreo:
		#Si se encuentra la participación de un usuario no pasa nada
		try:
			obj = Pregunta.objects.filter(id_pregunta__estudiante_part=i, definirProb_pregunta_id=defProbPreguntaQuery, tipo_pregunta=2)
			if not obj:
				#Obtenemos el id para posteriormente usar el nombre del usuario en el cuerpo del mensaje
				obj2 = User.objects.get(id=i)
				send_mail(
    			'Aviso, Faltas tu!',
    			f'Hola {obj2.first_name}, tu equipo ya realizó la actividad de formular las preguntas secundarias del tema {temaNombre}, faltas tu! Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.',
    			settings.EMAIL_HOST_USER,
    			[obj2.email],
    			fail_silently=False,
				)
		#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
		except Pregunta.DoesNotExist:
			print('se atrapó la excepción')
		
	return render(request, "estudiante/paso1/PSAvisoNoContinuar.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'current_user':current_user})


@student_required
@login_required
def AvisoNoContinuarEvaPS(request, id_tema, id_grupo):
	'''
	Esta es una de las dos funciones semejantes que se tienen en el views de estudiante, la unica diferencia que tienen 
	es que regresan un template diferente. Las funciones cuentan los integrantes del equipo del usuario actual relacionado al tema 
	de la pregunta inicial 
		Args:
		tema (string): El tema asignado de la pregunta inicial

		codigo (string): codigo de la materia 
	'''
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#obtengo todos los integrantes del equipo con ese id_equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo).values_list('estudiantes', flat=True)
	#Se consulta el equipo actual del usuario para pasarselo como parámetro en defProbPreguntaQuery
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Por cada integrante del equipo se va a buscar su participación de la PI
	hora = datetime.datetime.now()

	for i in integrantesEquipo:
		#Si se encuentra la participación de un usuario no pasa nada
		try:
			#Consultamos si existe una paritcipación del usuario relacionada al tema actual
			obj = EvaPreguntaSecundarias.objects.get(estudiante=i ,id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo = 1)
			print(obj)
		#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
		except EvaPreguntaSecundarias.DoesNotExist:
			#Obtenemos el id para posteriormente usar el nombre del usuario en el cuerpo del mensaje
			obj2 = User.objects.get(id=i)
			send_mail(
			'Aviso, Faltas tu!',
			f'Hola {obj2.first_name}, tu equipo ya realizó la actividad de evaluar las preguntas secundarias del tema {temaNombre}, faltas tu! Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.\n {hora}',
			settings.EMAIL_HOST_USER,
			[obj2.email],
			fail_silently=False,
			)
	return render(request, 'estudiante/paso1/EvPsAvisoNoContinuar.html', {'id_tema':id_tema, 'id_grupo':id_grupo, 'current_user':current_user})



@student_required
@login_required
def EvaluacionPS(request,  id_tema, id_grupo):
	#corroborar que el numero de integrantes sea el numero de filter con defquerry 
	temaPreguntaInicial = Tema.objects.get(id_tema=id_tema)
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = temaPreguntaInicial.id_tema)
	#identificamos si existe la participación de un usuario
	participacionPSusuario = EvaPreguntaSecundarias.objects.filter(estudiante=current_user ,id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo = 1)
	#identificamos las participaciones totales del equipo con el 
	participacionPSEquipo = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo = 1)
	#si el usuario ya tiene un campo en EvaPreguntaSecundarias asociado a un definirproblema_id entonces ya hizo ese paso
	#integrantesEquipo = Equipo.objects.filter(estudiantes__grupos_inscritos=equipo.grupo_equipo_id, temas_asignados__id_tema=id_tema)
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)

	numTotalPartici = Pregunta.objects.filter(definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo_pregunta=2)
	noPreguntasSec = DefinirProblema.objects.get(equipo_definirProb_id= equipo.id_equipo, tema_definirProb_id = id_tema).preguntas_secundarias

	print(numTotalPartici.count())
	print(integrantesEquipo.count() * noPreguntasSec)

	#corroboramos si existe participación
	if participacionPSusuario.exists():
		#si existe verificamos si el numero total de integrantes del equipo es el numero total de participaciones con el defProbPreguntaQuery_id del equipo
		if participacionPSEquipo.count() == integrantesEquipo.count():
			#redireccionar a pantalla de no continuar Evaluación preguntas seundarias
			return redirect('AMCE:PlanDeInvestigacion', id_grupo=id_grupo, id_tema=id_tema)
		else:
			return redirect('AMCE:AvisoNoContinuarEvaPS', id_grupo=id_grupo, id_tema=id_tema)

	return render(request, "estudiante/paso1/1EvaluacionPreguntasSecundarias.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'current_user':current_user})

@student_required
@login_required
def EvaluacionPreSec(request,  id_tema, id_grupo):
	current_user = get_object_or_404(User, pk=request.user.pk)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	#Consulta para obtener la pregunta inicial ganadora y mostrala en el template
	pregunta = Pregunta.objects.get(definirProb_pregunta = defProbPreguntaQuery, ganadora=True, tipo_pregunta=1)
	#Consulta que identifica las preguntas secundarias del equipo actual con el tema actual
	preguntasSec = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, tipo_pregunta=2)
	print(defProbPreguntaQuery)
	#verificamos si hay participación del usuario
	preSec = EvaPreguntaSecundarias.objects.filter(estudiante=current_user, id_definirProb_pregunta=defProbPreguntaQuery, tipo = 1)
	participacionPSusuario = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo = 1)
	integrantesEquipo = Equipo.objects.filter(estudiantes__grupos_inscritos=equipo.grupo_equipo_id, temas_asignados__id_tema=id_tema)
	#Consulta para obtener los integrantes de equipo para mandar correo
	integrantesEquipoCorreo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	if preSec.exists():
		if participacionPSusuario.count() == integrantesEquipoCorreo.count():
			#redireccionar a pantalla de no continuar Evaluación preguntas seundarias
			return redirect('AMCE:PlanDeInvestigacion', id_grupo=id_grupo, id_tema=id_tema)
		else:
			return redirect('AMCE:AvisoNoContinuarEvaPS', id_grupo=id_grupo, id_tema=id_tema)
	else:
		#permitirle hacer el 
		print('aún no tienes participación')
		#Se hace un request POST para identificar que botón(me gusta, no me gusta, no le entiendo) selecciona el usuario 
		if request.method == 'POST':
			#definimos el numero de iteración del foorloop que lleva como tag name de nuestra template, esto para indetificar el botón que se está seleccinoando con valor 1 o -1
			numBoton = 1
			#iteramos el número de preguntas secundarias que el equipo debe de tener 
			for i in preguntasSec:
				#obtenemos el valor del botón que el usuario selecciona
				option = request.POST.get("options%s" % numBoton)
				numBoton = numBoton + 1
				print(i.id_pregunta)

				#Preguntamos sino se ingresó nada
				if(option == None):
					print("Formulario inválido, se redirecciona a la misma página")
					#En este caso volvemos a mandar la misma página
					return render(request, "estudiante/paso1/2EvaluacionPreguntasSecundarias.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'temaNombre':temaNombre, 'pregunta':pregunta, 'preguntasSec':preguntasSec, 'current_user':current_user})

				if option == '3':
					#se actualiza el valor a +1 en el campo votos
					i.votos = F('votos')+3
					i.save(update_fields=['votos'])
				elif option == '-2':
					#se actualiza el valor a -1 en el campo votos
					i.votos = (F('votos')-2)
					i.save(update_fields=['votos'])
				elif option == '-1':
					#se actualiza el valor a -1 en el campo votos
					i.votos = (F('votos')-1)
					i.save(update_fields=['votos'])
			nuevaPartPS = EvaPreguntaSecundarias(estudiante=current_user, id_definirProb_pregunta=defProbPreguntaQuery, tipo = 1)
			nuevaPartPS.save() 
			#Obtenemos todas las participaciones del equipo de nuestro actual usuario
			numTotalPartici = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo = 1)
			#Participación actual del estudiante del tema actual para verificar si es la uñtima participación que el equipo necesita para continuar con el sig paso
			par = EvaPreguntaSecundarias.objects.get(estudiante=current_user, id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo = 1)
			#Entero el cual define la ultima participación del equipo
			ultimaParticipacion = integrantesEquipoCorreo.count()-1
			try:
				#Si la participación que hizo el estudiante es la ultima participación que se espera, manda el correo
				if par == numTotalPartici[ultimaParticipacion]:
					print('manda correo')
					#Se les notifica a los integrantes del equipo que todos han acabado
					for i in integrantesEquipoCorreo:
						nombreUsuario = User.objects.get(id=i)
						send_mail(
							'Tu equipo ya acabó de evaluar las preguntas secundarias!',
							f'Hola {nombreUsuario.first_name}, el último integrante de tu equipo ha terminado de evaluar la pregunta inicial del tema {temaNombre}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.',
							settings.EMAIL_HOST_USER,
							[nombreUsuario.email],
							fail_silently=False,
						)
			#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
			except IndexError:
				print('no se manda correo correo')

			messages.success(request, 'Evaluación guardada correctamente')
			#redireccionar a la misma función para evaluar si sigue o no
			return redirect('AMCE:EvaluacionPreSec', id_grupo=id_grupo, id_tema=id_tema)
	return render(request, "estudiante/paso1/2EvaluacionPreguntasSecundarias.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'temaNombre':temaNombre, 'pregunta':pregunta, 'preguntasSec':preguntasSec, 'current_user':current_user})

@student_required
@login_required
def PlanDeInvestigacion(request,  id_tema, id_grupo):
	#Consulta para obtener la pregunta inicial ganadora y mostrala en el template
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	pregunta = Pregunta.objects.get(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=1)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	noFuentes = DefinirProblema.objects.get(equipo_definirProb_id= equipo.id_equipo,tema_definirProb_id = id_tema).fuentes
	#Obtenemos los integrantes del  equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	#preguntasSec = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, tipo_pregunta=2).order_by('votos')
	'''
	for i in preguntasSec:
		if i.votos >= 2:
			i.ganadora = True
			i.save(update_fields=['ganadora'])
	'''
	#Se hace la consulta de las preguntas con más votos de manera ascendente
	preguntasSecGanadas = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, tipo_pregunta=2).order_by('-votos')
	noPreguntasSec = DefinirProblema.objects.get(equipo_definirProb_id= equipo.id_equipo, tema_definirProb_id = id_tema).preguntas_secundarias
	contador = 0
	#Definimos las respuestas ganadoras en la base de datos.
	for i in preguntasSecGanadas:
		i.ganadora = True
		i.save(update_fields=['ganadora'])
		contador += 1
		if contador == noPreguntasSec:
			break
	#Se hace la consulta de las preguntas con más votos de manera ascendente
	preguntasSecGanadas = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, tipo_pregunta=2).order_by('-votos')
	participacionPasoDosEquipo = FuentesSeleccionadas.objects.filter(id_defproblema= defProbPreguntaQuery.id_definirProb)
	participacionPasoDos = FuentesSeleccionadas.objects.filter(id_defproblema= defProbPreguntaQuery.id_definirProb, id_estudiante=current_user.id)
	if participacionPasoDos.exists():
		if participacionPasoDosEquipo.count() == integrantesEquipo.count() * noFuentes:
			print("Todo el equipo completó el paso 1 y se actualiza la variable paso a 2")
			actualizacionPaso = DefinirProblema.objects.filter(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema).update(paso=2)
		return redirect('AMCE:seleccionFuentes',id_grupo=id_grupo, id_tema=id_tema)
	else:
		print("Todo bien y se muestra la página de PlanDeInvestigación")
	return render(request, "estudiante/paso1/PlanDeInvestigacion.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'temaNombre':temaNombre, 'pregunta':pregunta, 'preguntasSecGanadas':preguntasSecGanadas, 'current_user':current_user})

@student_required
@login_required
def seleccionaFuentes(request, id_tema, id_grupo):
	current_user = get_object_or_404(User, pk=request.user.pk)
	estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Se consulta el equipo del usuario 
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	#Se consulta el número de fuentes que el profesor definió para el equipo/tema
	noFuentes = DefinirProblema.objects.get(equipo_definirProb_id= equipo.id_equipo,tema_definirProb_id = id_tema).fuentes
	#Se obtienen las fuentes relacionadas a mostrar en el paso de Evaluar las fuentes
	fuentesRelacionadas = FuentesSeleccionadas.objects.filter(id_defproblema= defProbPreguntaQuery.id_definirProb, id_estudiante = current_user.id)
	fuentesRelacionadasEquipo = FuentesSeleccionadas.objects.filter(id_defproblema= defProbPreguntaQuery.id_definirProb)
	#Obtenemos los integrantes del  equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	#Obtenemos todas las participaciones del equipo de nuestro actual usuario 
	numTotalPartici = FuentesSeleccionadas.objects.filter(id_defproblema = defProbPreguntaQuery)
	

	#Corrroboramos que ya hayan realizado este paso, si se cumple redireccionamos al siguiente paso
	if fuentesRelacionadasEquipo.count() == integrantesEquipo.count() * noFuentes:
		return redirect('AMCE:instuccionesNuevaFuente',id_grupo=id_grupo, id_tema=id_tema)
	#Si no
	else:
		if fuentesRelacionadas.count() == noFuentes:
			print("fuentesRelacionadas", fuentesRelacionadas)
			return redirect('AMCE:AvisoNoContinuarEvaFuentes',id_grupo=id_grupo, id_tema=id_tema)
		else:
			fuentes_creadas = []
			for x in fuentesRelacionadas:
				''''
				print("fuente seleccionada", x)
				print("id_fuente seleccionada", x.id_fuente.id)
				print()
				'''
				#Se agrega el id de nuestras fuentes creadas
				fuentes_creadas.append(x.id_fuente)

			#fuentes_creadas = Fuente.objects.filter(estudiante=estudiante, definirProb_fuentes_id=defProbPreguntaQuery)
			#print("---- fuentes_creadasr ----")
			#print(fuentes_creadas)
			elegidas = fuentes_creadas
			for fuente in fuentes_creadas:
				fuente.type_resource = tipoFuente(fuente.tipo_fuente)
			# APIKEY del servicio de google
			search_items = []
			if request.method == 'GET':
				search_items = []
				print("tipo get")
				API_KEY = "AIzaSyBqnJ74Q3Dq_Myj0YHdek-_diI_3Qr-FTA"
				# ID del motor de búsqueda personal que hayamos creado
				SEARCH_ENGINE_ID = "0f56893eb6c3e0fb9"

				# La búsqueda
				query = "qué es " + temaNombre
				page = 1
				#no de resultados que se desean
				start = (page - 1) * 10 + 1
				#URL con la cual se permitirá buscar en google con los filtros correspondientes 
				url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}&start={start}"

				data = requests.get(url).json()
				#print(data)
				#Se obtiene la lista de la búsqueda de google con los filtros correspondientes 
				search_items = data.get("items")
				print("seleccionar fuentes")
				
				#Verificamos si hay fuentes disponibles
				if(data.get("items") == None):
					messages.warning(request, "No hay fuentes sugeridas, prueba ingresándolas manualmente")
					search_items = [] #hacemos que search_items esté vació para no tener errores con len()
				#Acomodamos aleatoriamente la lista de items y la guardamos en una nueva lista con los items en orden aleatorio
				search_items_r = random.sample(search_items,len(search_items))

				return render(request, "estudiante/paso2/SeleccionFuentes.html",  {'elegidas': elegidas, 'search_items':search_items_r, 'id_tema':id_tema, 'id_grupo':id_grupo, 'noFuentes':noFuentes, 'temaNombre':temaNombre, 'definirFuente':defProbPreguntaQuery.id_definirProb, 'current_user':current_user})
			
			#convertimos el json a un diccionario
			#a = type(search_items) 
			#se recibe petición cuando presionas boton continuar al siguiente paso
			if request.method == 'POST':
				print("---- se hace post ---")
				#datos de fuentes sugeridas a guardar
				fuentes_a_guardar = request.POST.get('fuentes-preparadas')
				#print("fuentes_a_guardar", fuentes_a_guardar)
				fuentes_a_guardar = eval(fuentes_a_guardar)
				#print("fuentes_a_guardar", fuentes_a_guardar)
				for item in fuentes_a_guardar:
					item = eval(item)
					#print("x", x)
					print(item['title'])
					try:
						titulo = item["pagemap"]["metatags"][0]["title"]
					except KeyError:
						titulo = item["title"]
					try:
						fecha_publi = item["pagemap"]["metatags"][0]["citation_publication_date"]
					except KeyError:
						fecha_publi = "N/A"
					try:						
						autor = item["pagemap"]["metatags"][0]["author"]
					except KeyError:
						autor = "N/A"
					link = item["link"]
					lugar = "N/A"
					print('exito')
					print("Title:", titulo)
					print("fecha publicación:", fecha_publi)
					print("autor:", autor)
					print("link:", link)
					print("------------")
					fuenteCreada = False
					#si existe no hay necesidad de crear el objeto porque ya existe uno 
					try:
						#verificamos si ya existe una fuente seleccionada con el mismo titulo
						verificaFuente = Fuente.objects.get(titulo=titulo, id_defproblema = defProbPreguntaQuery)
						
					except Fuente.DoesNotExist:
						fuenteCreada = True
						print("se crea la fuente")
						nuevaFuente = Fuente(titulo=titulo,
											autor=autor, 
											fecha_publicacion= None, 
											lugar=lugar, 
											tipo_fuente=3, 
											tipo_recurso=1,
											enlace = link,
											id_defproblema = defProbPreguntaQuery
											)
						nuevaFuente.save()

						variable = FuentesSeleccionadas.objects.create(
							id_estudiante = estudiante,
							id_defproblema = defProbPreguntaQuery,
							id_fuente = nuevaFuente
						)
						variable.save()

					except IndexError:
						print('se atrapó la excepción')
					#si existe la fuente verifica si ya existe en el equipo
					if not fuenteCreada:
						variable = FuentesSeleccionadas.objects.create(
							id_estudiante = estudiante,
							id_defproblema = defProbPreguntaQuery,
							id_fuente = verificaFuente
						)
						variable.save()
						
				#aqui verificamos si es el ultimo participante por hacer la actividad
				#Participación actual del estudiante del tema actual para verificar si es la uñtima participación que el equipo necesita para continuar con el sig paso
				par = FuentesSeleccionadas.objects.filter(id_estudiante = estudiante , id_defproblema = defProbPreguntaQuery)
				#Entero el cual define la ultima participación del equipo
				ultimaParticipacion = (integrantesEquipo.count() * noFuentes)-1
				try:
					#Si la participación que hizo el estudiante es la ultima participación que se espera, manda el correo
					if par[noFuentes-1] == numTotalPartici[ultimaParticipacion]:
						print('manda correo')
						#Se les notifica a los integrantes del equipo que todos han acabado
						for i in integrantesEquipo:
							nombreUsuario = User.objects.get(id=i)
							send_mail(
							'Tu equipo ya acabó de seleccionar las fuentes!',
							f'Hola {nombreUsuario.first_name}, el último integrante de tu equipo ha terminado de seleccionar las fuentes del tema {temaNombre}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.',
							settings.EMAIL_HOST_USER,
							[nombreUsuario.email],
							fail_silently=False,
							)
				except IndexError:
					print('no se manda correo correo')
				print("Estoy en redirect", id_grupo, id_tema)
				messages.success(request, 'Fuentes elegidas guardadas correctamente')
				return HttpResponse(status=200)
		
			

def tipoFuente(x):
    return {
        '0': 'LIBRO',
        '1': 'REVISTA',
		'2': 'PERIODICO',
		'3': 'SITIO WEB',
		'4': 'VIDEO',
		'5': 'IMAGEN',
    }[x]

def seleccionaTipoFuente(request):
	return render(request, "estudiante/TipoFuente.html")

DECORATORS = [student_required, login_required]

@method_decorator(DECORATORS, name='dispatch')
class FuenteCreateView(FormView):
	template_name = 'estudiante/paso2/NuevaFuente.html'
	form_class = NuevaFuenteForm

	def form_valid(self, form):
		#fuente = form.save(commit=False)
		#fuente.save()
		equipo = Equipo.objects.get(estudiantes=self.estudiante, grupo_equipo=self.id_grupo)
		defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = self.id_tema)

		fuente = Fuente.objects.create(
			titulo = form.cleaned_data['titulo'],
			autor = form.cleaned_data['autor'],
			fecha_publicacion = form.cleaned_data['fecha_publicacion'],
			lugar = form.cleaned_data['lugar'],
			tipo_fuente = form.cleaned_data['tipo_fuente'],
			#tipo_recurso = form.cleaned_data['tipo_recurso'],
			enlace = form.cleaned_data['enlace'],
			id_defproblema = defProbPreguntaQuery
			
		)
		fuente.save()
		

		#crear una instancia de FuentesSeleccionadas
		variable = FuentesSeleccionadas.objects.create(
			id_estudiante = self.estudiante,
			id_defproblema = defProbPreguntaQuery,
			id_fuente = fuente
		)

		return super(FuenteCreateView, self).form_valid(form)

	def get_form_kwargs(self, *args, **kwargs):
		form_kwargs = super(FuenteCreateView, self).get_form_kwargs(*args, **kwargs)
		current_user = get_object_or_404(User, pk=self.request.user.pk)
		self.estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
		self.definirProbFuente =  self.kwargs['definirFuente'] 
		self.id_tema = self.kwargs['id_tema']
		self.id_grupo = self.kwargs['id_grupo']
		self.success_url = reverse_lazy('AMCE:seleccionFuentes', kwargs={'id_grupo': self.kwargs['id_grupo'] ,'id_tema':self.kwargs['id_tema']})
		return form_kwargs
	
	def get_context_data(self, **kwargs):
		"""
		Función que permite mandar datos al front
		"""
		#Obtenemos los datos de contexto y los guardamos en un diccionario
		context = super().get_context_data(**kwargs)
		#Guardamos el objeto usuario de la sesión actual
		current_user = get_object_or_404(User, pk=self.request.user.pk)
		#a la llave current_user le asignamos el objeto usuario de la sesión actual
		context["current_user"] = current_user
		#Devolvermos el diccionario con los datos que queremos mandar al front 
		return context


@method_decorator(DECORATORS, name='dispatch')
class FuenteUpdateView(UpdateView):
	template_name = 'estudiante/paso2/NuevaFuente.html'
	model = Fuente
	form_class = EditFuenteForm

	def form_valid(self, form):
		fuente = form.save(commit=False)
		fuente.estudiante = self.estudiante
		if(fuente.tipo_recurso == '0'):
			element = self.request.FILES['resourceFile']
			fuente.enlace = element.name
		fuente.save()
		return super(FuenteUpdateView, self).form_valid(form)

	def get_form_kwargs(self, *args, **kwargs):
		form_kwargs = super(FuenteUpdateView, self).get_form_kwargs(*args, **kwargs)
		current_user = get_object_or_404(User, pk=self.request.user.pk)
		self.estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
		self.success_url = reverse_lazy('AMCE:seleccionFuentes', kwargs={'id_grupo': self.kwargs['id_grupo'] ,'id_tema':self.kwargs['id_tema']})
		return form_kwargs


@method_decorator(DECORATORS, name='dispatch')
class FuenteDeleteView(DeleteView):
	model = Fuente
	template_name = "estudiante/paso2/EliminarFuente.html"

	def get_success_url(self, **kwargs):
		current_user = get_object_or_404(User, pk=self.request.user.pk)
		self.estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
		return reverse_lazy('AMCE:seleccionFuentes', kwargs={'id_grupo': self.kwargs['id_grupo'] ,'id_tema':self.kwargs['id_tema']})

@student_required
@login_required
def instuccionesNuevaFuente(request, id_tema, id_grupo):
	current_user = get_object_or_404(User, pk=request.user.pk)
	estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Se consulta el equipo del usuario 
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	#Consultamos las evaluaciones totales del equipo por el tema que están trabajando
	evaluacionesFuentes = EvaluacionFuentesSel.objects.filter(id_defproblema=defProbPreguntaQuery)
	fuentesRelacionadas = FuentesSeleccionadas.objects.filter(id_defproblema= defProbPreguntaQuery.id_definirProb, id_estudiante = current_user.id)
	fuentesRelacionadasEquipo = FuentesSeleccionadas.objects.filter(id_defproblema= defProbPreguntaQuery.id_definirProb)
	#Se consulta el número de fuentes que el profesor definió para el equipo/tema
	noFuentes = DefinirProblema.objects.get(equipo_definirProb_id= equipo.id_equipo,tema_definirProb_id = id_tema).fuentes
	#corroborar si todo el equipo ya evaluó las fuentes
	if integrantesEquipo.count() == evaluacionesFuentes.count():
		#Si sí pasa al fin paso 2
		return redirect('AMCE:EvaluarFuentesPlanInvestigación', id_grupo=id_grupo, id_tema=id_tema)
	else:
		if fuentesRelacionadas.exists():
			if fuentesRelacionadasEquipo.count() != integrantesEquipo.count() * noFuentes:
				return redirect('AMCE:AvisoNoContinuarEvaFuentes',id_grupo=id_grupo, id_tema=id_tema)	
		try:
			participacionEvaluacionesFuentes = EvaluacionFuentesSel.objects.get(id_defproblema=defProbPreguntaQuery, id_estudiante = estudiante)
			return redirect('AMCE:AvisoNoContinuarEvaFuentes2', id_grupo=id_grupo, id_tema=id_tema)
		except EvaluacionFuentesSel.DoesNotExist:
			print("hola")
	# si ya tiene participación pero su equipo aún no acaba entonces redirecionar al paso  
	return render(request, "estudiante/paso2/InstruccionesEvaluarFuentes.html", {'id_tema':id_tema, 'id_grupo':id_grupo, "current_user":current_user})

@student_required
@login_required
def evaluarFuentes(request, id_tema, id_grupo):
	current_user = get_object_or_404(User, pk=request.user.pk)
	estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Se consulta el equipo del usuario 
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	#se obtiene unicamente los id de las fuentes, y hacemos el filtro por equipo, despues obtenemos los elementos distintos
	fuentesAEvaluarTemp = FuentesSeleccionadas.objects.values('id_fuente').filter(id_defproblema = defProbPreguntaQuery).distinct()
	fuentesEquipoSel = FuentesSeleccionadas.objects.filter(id_defproblema = defProbPreguntaQuery)
	noFuentes = DefinirProblema.objects.get(id_definirProb=defProbPreguntaQuery.id_definirProb).fuentes
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	"""
	idFuentesAgregadas = []
	fuentesAEvaluar = []
	for x in fuentesAEvaluarTemp:
		#Se agrega la fuente
		if(x.id_fuente.id not in idFuentesAgregadas):
			fuentesAEvaluar.append(x.id_fuente)
			idFuentesAgregadas.append(x.id_fuente.id)
	"""		
	fuentesAEvaluar = []
	for x in fuentesAEvaluarTemp:
		#print("valor de x",  x['id_fuente'])
		fuentesAEvaluar.append(Fuente.objects.get(id = x['id_fuente']))

	#Se verifica que todo el equipo haya seleccionado sus fuentes
	if fuentesEquipoSel.count() == (integrantesEquipo.count() * noFuentes):
		#aqui va el back para votar por la fuente
		if request.method == 'POST':
			#se captura el nombre de usuario por el cual se está votando
			voto = request.POST.get("voto")#Voto obtenido del front, es un id
			form = EvaluarFuente(request.POST)
	
			#Si el usuario no votó por una fuente entonces lo redireccionamos a la misma página
			if(voto == None):
				print("Formulario inválido, se redirecciona a la misma página")
				return render(request, "estudiante/paso2/EvaluarFuentes.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'fuentesAEvaluar':fuentesAEvaluar, 'temaNombre':temaNombre, 'form':form, 'current_user':current_user})

			obtenIdFuente = Fuente.objects.get(id=voto)
			if form.is_valid():
				print("se guardó el contenido", form.cleaned_data['contenido'])
				nuevaEvaluacion = EvaluacionFuentesSel(comentario=form.cleaned_data['contenido'],
									id_defproblema=defProbPreguntaQuery,
									id_estudiante=estudiante,
									id_fuente_id = obtenIdFuente.id
				)
				nuevaEvaluacion.save()
				nuevoVoto = Fuente.objects.filter(id=voto).update(votos=F('votos')+1)

				#Verificamos si el usuario es el último integrante del equipo que faltaba por terminar el paso
				#Consulta para verificar
				par = EvaluacionFuentesSel.objects.get(id_defproblema = defProbPreguntaQuery, id_estudiante=current_user.id)
				#Entero el cual define la ultima participación del equipo
				ultimaParticipacion = integrantesEquipo.count()
				numTotalPartici = EvaluacionFuentesSel.objects.filter(id_defproblema = defProbPreguntaQuery)
				try:
					#Si la participación que hizo el estudiante es la ultima participación que se espera, manda el correo
					if par == numTotalPartici[ultimaParticipacion-1]:
						print('manda correo')
						#Se les notifica a los integrantes del equipo que todos han acabado
						for i in integrantesEquipo:
							nombreUsuario = User.objects.get(id=i)
							send_mail(
							'Tu equipo ya acabó de evaluar las fuentes!',
							f'Hola {nombreUsuario.first_name}, el último integrante de tu equipo ha terminado de evaluar las fuentes del tema {temaNombre}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.',
							settings.EMAIL_HOST_USER,
							[nombreUsuario.email],
							fail_silently=False,
							)
				#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
				except IndexError:
					print('no se manda correo correo')
				messages.success(request, 'Voto y comentario guardado correctamente')
				return redirect('AMCE:EvaluarFuentesPlanInvestigación', id_grupo=id_grupo, id_tema=id_tema)
		else:
			form = EvaluarFuente()
	else:
		return redirect('AMCE:AvisoNoContinuarEvaFuentes',id_grupo=id_grupo, id_tema=id_tema)
	
	return render(request, "estudiante/paso2/EvaluarFuentes.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'fuentesAEvaluar':fuentesAEvaluar, 'temaNombre':temaNombre, 'form':form, 'current_user':current_user})

@student_required
@login_required
def AvisoNoContinuarEvaFuentes(request, id_tema, id_grupo):
	'''
	Esta es una de las dos funciones semejantes que se tienen en el views de estudiante, la unica diferencia que tienen 
	es que regresan un template diferente. Las funciones cuentan los integrantes del equipo del usuario actual relacionado al tema 
	de la pregunta inicial 
		Args:
		tema (string): El tema asignado de la pregunta inicial

		codigo (string): codigo de la materia 
	'''
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#obtengo todos los integrantes del equipo con ese id_equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo).values_list('estudiantes', flat=True)
	#Se consulta el equipo actual del usuario para pasarselo como parámetro en defProbPreguntaQuery
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Por cada integrante del equipo se va a buscar su participación de la PI
	hora = datetime.datetime.now()
	
	
	for i in integrantesEquipo:
		#Si se encuentra la seleccion de fuentes de un usuario no pasa nada
		try:
			#Consultamos si existe una paritcipación del usuario relacionada al tema actual
			obj = FuentesSeleccionadas.objects.filter(id_defproblema= defProbPreguntaQuery.id_definirProb, id_estudiante = i)
			if not obj:
				#Obtenemos el id para posteriormente usar el nombre del usuario en el cuerpo del mensaje
				obj2 = User.objects.get(id=i)
				send_mail(
				'Aviso, Faltas tu!',
				f'Hola {obj2.first_name}, tu equipo ya realizó la actividad de seleccionar las fuentes del tema {temaNombre}, faltas tu! Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.\n {hora}',
				settings.EMAIL_HOST_USER,
				[obj2.email],
				fail_silently=False,
				)
		#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
		except EvaPreguntaSecundarias.DoesNotExist:
			print("todo bien")
	
	return render(request, 'estudiante/paso2/EvFuentesAvisoNoContinuar.html', {'id_tema':id_tema, 'id_grupo':id_grupo, 'current_user':current_user})

@student_required
@login_required
def AvisoNoContinuarEvaFuentes2(request, id_tema, id_grupo):
	'''
	Esta es una de las dos funciones semejantes que se tienen en el views de estudiante, la unica diferencia que tienen 
	es que regresan un template diferente. Las funciones cuentan los integrantes del equipo del usuario actual relacionado al tema 
	de la pregunta inicial 
		Args:
		tema (string): El tema asignado de la pregunta inicial

		codigo (string): codigo de la materia 
	'''
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#obtengo todos los integrantes del equipo con ese id_equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo).values_list('estudiantes', flat=True)
	#Se consulta el equipo actual del usuario para pasarselo como parámetro en defProbPreguntaQuery
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Por cada integrante del equipo se va a buscar su participación de la PI
	hora = datetime.datetime.now()
	
	for i in integrantesEquipo:
		#Si se encuentra la participación de un usuario no pasa nada
		try:
			#Consultamos si existe una paritcipación del usuario relacionada al tema actual
			obj = EvaluacionFuentesSel.objects.get(id_defproblema=defProbPreguntaQuery, id_estudiante = i)
			print(obj)
		#Si no encuentra la participación de un usuario entonces manda correo a ese usuario quién no tiene la participación
		except EvaluacionFuentesSel.DoesNotExist:
			#Obtenemos el id para posteriormente usar el nombre del usuario en el cuerpo del mensaje
			obj2 = User.objects.get(id=i)
			send_mail(
			'Aviso, Faltas tu!',
			f'Hola {obj2.first_name}, tu equipo ya realizó la actividad de evaluar las fuentes del tema {temaNombre}, faltas tu! Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.\n {hora}',
			settings.EMAIL_HOST_USER,
			[obj2.email],
			fail_silently=False,
			)
	
	return render(request, 'estudiante/paso2/EvFuentesAvisoNoContinuar2.html', {'id_tema':id_tema, 'id_grupo':id_grupo, 'current_user':current_user})

@student_required
@login_required
def EvaluarFuentesPlanInvestigación(request, id_tema, id_grupo):
	current_user = get_object_or_404(User, pk=request.user.pk)
	estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Se consulta el equipo del usuario 
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	#Profesor
	grupo = Grupo.objects.get(id_grupo=id_grupo)
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	#Consultamos las evaluaciones totales del equipo por el tema que están trabajando
	evaluacionesFuentes = EvaluacionFuentesSel.objects.filter(id_defproblema=defProbPreguntaQuery)
	#corroborar si todo el equipo ya evaluó las fuentes
	if integrantesEquipo.count() == evaluacionesFuentes.count():
		#Si sí pasa al fin paso 2
		print("Todo bien!")
		fuentesEquipo = Fuente.objects.filter(id_defproblema=defProbPreguntaQuery)
		for i in fuentesEquipo:
			if i.votos >= 1:
				i.ganadora = True
				i.save(update_fields=['ganadora'])
		fuentesEquipoGanadoras = Fuente.objects.filter(id_defproblema=defProbPreguntaQuery, ganadora = True)
		fuentesEquipoGanadoras2 = Fuente.objects.filter(id_defproblema=defProbPreguntaQuery, ganadora = True).values_list('id', flat=True)
		print("fuentes ganadoras 2", fuentesEquipoGanadoras2)
		ejemplo = EvaluacionFuentesSel.objects.filter(id_defproblema=defProbPreguntaQuery)
		print('ejemplo', ejemplo)
		#verificar que el usuario actual tenga participación del primer subpaso del paso 3
			#Se obtienen las preguntas secundarias para ver si se le redirecciona al paso de no continuar o seguir la actividad
		respuestasUsuario = Respuesta.objects.filter(definirProb = defProbPreguntaQuery, tipo=1).values_list('id_respuesta', flat=True)
		#Se obtienen los ids de las participaciones del usuario actual 
		idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)
		if bool(set(idsUsuarioParticipacion)&set(respuestasUsuario)):
			return redirect('AMCE:InstruccionesP3P1', id_grupo=id_grupo, id_tema=id_tema)
		else:
			print('todo bien jejeje')
		
	else:
		return redirect('AMCE:AvisoNoContinuarEvaFuentes2', id_grupo=id_grupo, id_tema=id_tema)

	return render(request, "estudiante/paso2/EvFuPlanInvestigación.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'fuentesEquipoGanadoras':fuentesEquipoGanadoras, 'ejemplo':ejemplo, 'current_user':current_user})





#---Apartir de aquí las funciones corresponden al PASO 3 ---
# El paso tres del modelo gavilán tiene como finalidad la generación de respuestas para las preguntas 
# secundarías, que se utilizarán para generar la respuesta de la pregunta inicial del paso4. 
# Este paso consta de cuatro, por lo que se desarrollo cada uno y se engloban las funciones que
# corresponden a su respectivo subpaso.  


# Subpaso1, responder las preguntas secundarías con información extraída directamente de la fuente. 
# Dadas las fuentes ganadoras, se muestra un formulario que contiene todas las preguntas secundarías con sus respectivos campos; el primero correspone a la información extraída directamente de la fuente, se copia y pega tal cual, en la segunda entrada se agrega una referencia del parrafo, página en cuestión de libros o pdf y renglones de donde fue extraída la información anterior, y como ultimo campo tenemos un botón de tipo select, donde se selecciona la fuente a la que corresponde la info y la referencia. 

# Instrucciones que se mandan cuando todos terminaron el paso dos.
# Estas instricciones corresponden al subpaso1Paso3.
def InstruccionesP3P1(request, id_tema, id_grupo):
	# Si accesas al URL sin haber hecho login con un usuario, 
	# te manda un error, en otro caso te devuelve al usuario actual(estudiante).
	current_user = get_object_or_404(User, pk=request.user.pk)
	## Regresa el número id delequipo del usuario actual.
	equipo_id = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo_id, tema_definirProb_id = id_tema)
	# Obtengo todos los integrantes del equipo con ese id_equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo_id).values_list('estudiantes', flat=True)
	#Para obtener el número de preguntas secundarias ganadoras con las cuales se va a trabajar
	noPreguntasSec2 = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=2)
	#Para obtener las respuestas-fuente que han hecho en el equipo, nos devuelve la lista de id's.
	respuestasUsuario = Respuesta.objects.filter(definirProb = defProbPreguntaQuery, tipo=1).values_list('id_respuesta', flat=True)
	#Se obtienen los ids de las participaciones del usuario actual 
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)

	if (noPreguntasSec2.count() * integrantesEquipo.count()) == respuestasUsuario.count():
		#Si todo el equipo terminó redirigir a la pantalla de instrucciones del subpaso siguiente
		return redirect('AMCE:InstruccionesP3P2',  id_grupo=id_grupo, id_tema=id_tema)
	else:
		#Si el usuario ya tiene participación (i.e. existen elementos en el queryset)
		if bool(set(idsUsuarioParticipacion)&set(respuestasUsuario)):
			#Lo redireccional al avisoNoContinuar del paso en el que estamos.
			return redirect('AMCE:AvisoNoContinuarP3P1', id_grupo=id_grupo, id_tema=id_tema)
 
	return render(request, "estudiante/paso3/InstruccionesP3P1.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'current_user':current_user})


#Se manda a llamar a esta función cuando el usuario ya respondió el formulario pero sus compañeros no. Renderiza al html que muestra un mensaje de espera, y se deja de mostrar cuando se verifica que ya todos terminaron.
@student_required
@login_required
def AvisoNoContinuarP3P1(request, id_tema, id_grupo):
	'''
	Funcion para mostrar el aviso de que el equipo aún no acaba esta parte
	'''
	# Si accesas al URL sin haber hecho login con un usuario, 
	# te manda un error, en otro caso te devuelve al usuario actual(estudiante).
	current_user = get_object_or_404(User, pk=request.user.pk)
	# Regresa el número id delequipo del usuario actual.
	equipo_id = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	# Obtengo todos los integrantes del equipo con ese id_equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo_id).values_list('estudiantes', flat=True)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo_id, tema_definirProb_id = id_tema)
	#Se obtienen todas las respuestas-fuente hechas por el equipo del usuario.
	respuestasUsuario = Respuesta.objects.filter(definirProb = defProbPreguntaQuery, tipo=1).values_list('id_respuesta', flat=True)
	#Obtenemos el tema asignado al equipo.
	temaPreguntaInicial = Tema.objects.get(id_tema=id_tema)
	#Por cada integrante del equipo vamos a verificar si ya tienen participación o no, esto para saber si debe quedarse en la pantalla del aviso o continuar a las instrucciones del siguiente paso.

	#Por cada integrante
	for i in integrantesEquipo:
		#Consultamos su usuario
		nombreUsuario = User.objects.get(id=i)
		#Si se encuentra la participación de un usuario no pasa nada
		#Se consulta integrante x integrante para ver si tiene participación 
		integranteN = ParticipacionEst.objects.filter(estudiante_part=i).values_list('id_actividad', flat=True)
		try:
			#Si no se encuentra participación entonces debemos mandarle una notificación por correo, para que responda las preguntas.
			if not(bool(set(integranteN)&set(respuestasUsuario))):
				hora = datetime.datetime.now()
				send_mail(
				'Aviso, Faltas tu!',
				f'Hola {nombreUsuario.first_name}, tu equipo ya realizó la actividad de dar respuesta a las preguntas secundarias ganadoras del tema {temaPreguntaInicial.nombre_tema}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.\n {hora}',
				settings.EMAIL_HOST_USER,
				[nombreUsuario.email],
				fail_silently=False,
				)
		except:
			print('Todo está bien')
	return render(request, 'estudiante/paso3/AvisoNoContinuarP3P1.html', {'id_tema':id_tema, 'id_grupo':id_grupo, 'current_user':current_user})

# Paso3. (Función principal)
# Esta es la función donde se genera el ciclo que maneja todo lo correspondiente al paso tres, 
# se cachan todo el tipo de excepciones, para que después mande a las respectivas funciones auxiliares.
# Este es el paso que redirecciona al formulario de tipo formset para el llenado de las respuestas.
def RespuestaFuente(request, id_tema ,id_grupo):
	#El contexto que renderizamos para el html
	context = {}
	# Si accesas al URL sin haber hecho login con un usuario, 
	# te manda un error, en otro caso te devuelve al usuario actual(estudiante).
	current_user = get_object_or_404(User, pk=request.user.pk)
	# Regresa el número de id del equipo del usuario actual.
	equipo_id = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#obtengo todos los integrantes del equipo con ese equipo_id
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo_id).values_list('estudiantes', flat=True)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo_id, tema_definirProb_id = id_tema)	
	#Para obtener el número de preguntas secundarias ganadoras con las cuales se va a trabajar
	noPreguntasSec2 = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=2)
	#Obtenemos todas las participaciones del equipo de nuestro actual usuario, es decir el número de respuestas que han contestado, esto se usa para saber si ya realizaron todos sus respuestas, mandar el correo de finalización y para redireccionar a las siguientes instrucciones.
	respuestasUsuario = Respuesta.objects.filter(definirProb = defProbPreguntaQuery, tipo=1).values_list('id_respuesta', flat=True)
	#Se obtienen los ids de las participaciones del usuario actual 
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)
	#Vamos a entrar al ciclo que va a manejar las excepciones dependiendo las participaciones de los alumnos.
	# Regresa el nombre del tema que están trabajando.
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#CASO 1: SI TODO EL EQUIPO TERMINA (el numero de preguntas secundarias por el numero de integrantes es igual a las prticipaciones totales, ej. 2 preg sec * 3 integrantes == 6 participaciones o 6 respuestas.)
	
	if (noPreguntasSec2.count() * integrantesEquipo.count()) == respuestasUsuario.count():
		#Si todo el equipo terminó redirigir a la pantalla de instrucciones del subpaso siguiente
		return redirect('AMCE:InstruccionesP3P2',  id_grupo=id_grupo, id_tema=id_tema)
	else:
		# CASO 2: EL EQUIPO AUN NO TERMINA SE VERIFICA SI EL USUARIO ACTUAL YA TIENE PARTICIPACIÓN, 
		#		  SI YA TIENE PARTICIPACION LO MANDAMOS AL AVISO DE NO CONTINUAR (porque ya participó y debe esperar a que sus otros compañeros lo hagan.)
		# Corroboras si el usuario actual ya participó. (el num de respuestas de él es igual al de las preguntas # que corresponden a ese id_defprobpregquery.) (se hace con el exists por que el formulario obliga a contestar las dos preguntas, entonces minimo debe haber una respuesta en el query.)
		if bool(set(idsUsuarioParticipacion)&set(respuestasUsuario)):
			return redirect('AMCE:AvisoNoContinuarP3P1',  id_grupo=id_grupo, id_tema=id_tema)
			
		# CASO 3: EL USUARIO ACTUAL NO TIENE PARTICIPACIÓN 
		else:
			#Formset (Generamos el formulario de preguntas con los input y el boton de selección.)
			# Convertimos QuerySet a Lista, para poder mandarla al html.
			preguntasSecLista = []
			# Agregamos las preguntas secundarias ganadoras a una lista
			for x in noPreguntasSec2:
				preguntasSecLista.append(x)
			# En forms.py definimos un formulario que almacena la respuesta extraída de la fuente, la referencia y el boton de selección (RespuestaPregSecFuente), pero con esta línea generamos el formulario de formularios, es decir, por cada pregunta generamos un formulario pequeño (noPreguntasSec2) y en conjunto hacen el formulario mayor.
			respuestasFormSet = formset_factory(wraps(RespuestaPregSecFuente)(partial(RespuestaPregSecFuente,
												id_defproblema=defProbPreguntaQuery.id_definirProb)),
												extra=len(noPreguntasSec2))
			#Validación del formsset
			if request.method == 'POST':
				formset = respuestasFormSet(request.POST)
				# Revisamos si el formset (conjunto de formularios) es válido
				if formset.is_valid():
					# Iteramos sobre el formset para obtener uno a uno los formularios
					for i,form in enumerate(formset):
						# Si el formulario actual es válido
						if form.is_valid():
							cd = form.cleaned_data
							#Creamos un elemento para nuestra tabla de actividad 
							nuevaParticipacion = ParticipacionEst(contenido = cd['respPregSecFuente'],
																	estudiante_part_id = current_user.id)
							nuevaParticipacion.save()
							respuestas_cd = Respuesta(
												id_respuesta_id=nuevaParticipacion.id_actividad,
												tipo = 1,
												pregunta = preguntasSecLista[i], 
												fuente = cd['fuentes'],
												referencia = cd['referenciaFuente'],
												definirProb = defProbPreguntaQuery,
												)
							# Guardamos en la base de datos
							respuestas_cd.save()
							print("Se hizo el save")
		
					#Mandamos el mensaje de exito al html.
					messages.add_message(request, messages.SUCCESS, 'La respuesta se ha agregado correctamente.', extra_tags='alert-success')
					# Se redirige a RespondiendoPregSec para que se valide si puede avanzar o no al siguente paso. Esto lo hacemos por que entra de nuevo a esta función y verifica a que caso le corresponde pasar, a esperar que contesten o a que pasen al siguiente subpaso.
							
					#Vamos a manejar el caso de los correos, como el usuario ya contesto, verificaremos si el era el último en contestar. Si este es el caso debe anunciarle a los demás que ya pueden continuar con el siguiente subpaso.
					#Vuelvo a consultar cuantas respuestas hay de los usuarios para verificar que ya todos contestaron
					respuestasUsuario2 = Respuesta.objects.filter(definirProb = defProbPreguntaQuery, tipo=1).values_list('id_respuesta', flat=True)
					try: 
						print("Entramos al try de mandar los correos por que ya todo termino")
						# Verificando si la participación actual del estudiante es la última
						# participación que el equipo necesita para continuar con el sig paso
						if (noPreguntasSec2.count() * integrantesEquipo.count()) == respuestasUsuario2.count():
							print("TODOS LOS ESTUDIANTES RESPONDIERÓN LAS PREGUNTAS SECUNDARIAS GANADORAS")
							#Se les notifica a los integrantes del equipo que todos han acabado
							for i in integrantesEquipo:
								nombreUsuario = User.objects.get(id=i)
								hora = datetime.datetime.now()
								send_mail('Tu equipo ya acabó de dar respuesta a las preguntas secundarias ganadoras.',f'Hola {nombreUsuario.first_name}, el último integrante de tu equipo ha terminado de dar respuesta a las preguntas secundarias ganadoras del tema {temaNombre}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.\n {hora}',
								settings.EMAIL_HOST_USER,
								[nombreUsuario.email],
								fail_silently=False,
								)
					except IndexError:
						print('No se manda correo correo, hubo un problema.')
					return redirect('AMCE:RespuestaFuente', id_grupo=id_grupo, id_tema=id_tema)
				else:
					# El formset fue inválido
					# Lo muestra por cada forms que lo conforma.
					for form in formset:
						print("Form invalid")
			else:
				# Manda de nuevo el formulario.
				formset = respuestasFormSet()
	#Agregamos al contexto(diccionario) lo que queremos renderizar al html. 
	context['formset']= formset
	context['preguntasSec'] = preguntasSecLista
	context['temaNombre'] = temaNombre
	context['current_user'] = current_user
	return render(request, "estudiante/paso3/RespuestaFuente.html", context)

def InstruccionesP3P2(request, id_tema, id_grupo):
	# Si accesas al URL sin haber hecho login con un usuario, 
	# te manda un error, en otro caso te devuelve al usuario actual(estudiante).
	current_user = get_object_or_404(User, pk=request.user.pk)
	# Regresa el número id delequipo del usuario actual.
	equipo_id = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#Hacemos la actualización del paso ya que avanzamos a estas instrucciones
	#Para que el usuario continue siempre desde el paso 3, es necesario actualizar este en la tabla de DefinirProblema.
	actualizacionPaso = DefinirProblema.objects.filter(equipo_definirProb_id = equipo_id, tema_definirProb_id = id_tema).update(paso=3)
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo_id, tema_definirProb_id = id_tema)
	# Obtengo todos los integrantes del equipo con ese id_equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo_id).values_list('estudiantes', flat=True)
	#Para obtener el número de preguntas secundarias ganadoras con las cuales se va a trabajar
	noPreguntasSec2 = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=2)
	#Obtenemos las respuestas sintetizadas hechas por los integrantes del equipo del usuario.
	respuestasUsuario = Respuesta.objects.filter(definirProb = defProbPreguntaQuery, tipo=2).values_list('id_respuesta', flat=True)
	#Se obtienen todas las respuestas-fuente hechas por los integrantes del equipo.
	respuestasUsuarioFuente = Respuesta.objects.filter(definirProb = defProbPreguntaQuery, tipo=1).values_list('id_respuesta', flat=True)
	#Se obtienen los ids de las participaciones del usuario actual, para hacer el join y traer el contenido.
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)

	#Si todo el usuario ha hecho sus respuestas sintetizadas.
	if (noPreguntasSec2.count() * integrantesEquipo.count()) == respuestasUsuario.count():
		#Si todo el equipo terminó redirigir a la pantalla de instrucciones del subpaso siguiente
		return redirect('AMCE:InstruccionesP3P3',  id_grupo=id_grupo, id_tema=id_tema)
	else:
		#Si no
		#Si el usuario ya tiene participación (i.e. existen elementos en el queryset)
		if len(set(idsUsuarioParticipacion)&set(respuestasUsuario)) == noPreguntasSec2.count():
			return redirect('AMCE:AvisoNoContinuarP3P2', id_grupo=id_grupo, id_tema=id_tema)
		#El usuario tiene participación en directamente de la fuente y no tiene ninguna respuesta contestada.
		elif len(set(idsUsuarioParticipacion)&set(respuestasUsuario)) == 0:
			#Si no, verificamos que el usuario actual ya tenga participación
			try:
				#Obtenemos los id de las respuestas-fuente del usuario.
				respuestas_fuente = Respuesta.objects.filter(id_respuesta__estudiante_part_id = current_user.id ,definirProb=defProbPreguntaQuery.id_definirProb, tipo = 1).values_list('pregunta', flat=True)
				#Rederizamos a las instrucciones del subpaso dos, pasandole el id de la primera pregunta que debe evaluar. Esto es porque desde aquí se manda a llamar la primera vez la funcion  de respuestaSintetizada.
				return render(request, "estudiante/paso3/InstruccionesP3P2.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'id_pregunta_id': respuestas_fuente[0], 'current_user':current_user})
			except IndexError:
				print("Entramos al Index error")
		else:
			#El caso anterior se da cuando no han hecho ninguna sintesis, en este caso si se ha hecho alguna, por ello mandamos desde aquí a la siguiente respuesta-fuente que haga falta por sintetizar.
			#Buscamos las respuestas sintetizadas que ha hecho.
			respuestas_sintetizadas_hechas = Respuesta.objects.filter(id_respuesta__estudiante_part_id = current_user.id,definirProb=defProbPreguntaQuery.id_definirProb, tipo = 2)	
			#Vemos cuales son los id-pregunta a los que correspoden a las preguntas que han respondido.
			respuestas_fuente= Respuesta.objects.filter(id_respuesta__estudiante_part_id = current_user.id ,definirProb=defProbPreguntaQuery.id_definirProb, tipo = 1).values_list('pregunta', flat=True)
			#Redireccionamos a la pantalla con el id de la pregunta que corresponde por sintetizar.
			return redirect('AMCE:RespuestaSintetizada', id_grupo=id_grupo, id_tema=id_tema, id_pregunta_id = respuestas_fuente[respuestas_sintetizadas_hechas.count()])
	#Redireccionamos al avisoNo continuar, pues ya se hicieron las respuestas sintetizadas, y esta pantalla solo debe aparecer la primera vez que empieza a sintetizar.
	return redirect('AMCE:AvisoNoContinuarP3P2',  id_grupo=id_grupo, id_tema=id_tema)	

def AvisoNoContinuarP3P2(request, id_tema, id_grupo):
	# Si accesas al URL sin haber hecho login con un usuario, 
	# te manda un error, en otro caso te devuelve al usuario actual(estudiante).
	current_user = get_object_or_404(User, pk=request.user.pk)
	estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	## Regresa el número id delequipo del usuario actual.
	equipo_id = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo_id, tema_definirProb_id = id_tema)
	print("el definir problema pregunta query de este tema es el siguiente:")
	print(defProbPreguntaQuery.id_definirProb)
	# Obtengo todos los integrantes del equipo con ese id_equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo_id).values_list('estudiantes', flat=True)
	#Para obtener el número de preguntas secundarias ganadoras con las cuales se va a trabajar
	noPreguntasSec2 = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=2)
	#Obtenemos todas las respuestas sintetizadas hechas por el equipo.
	respuestasUsuario = Respuesta.objects.filter(definirProb = defProbPreguntaQuery, tipo=2).values_list('id_respuesta', flat=True)
	respuestasUsuarioFuente = Respuesta.objects.filter(definirProb = defProbPreguntaQuery, tipo=1).values_list('id_respuesta', flat=True)

	#Si todos los integrantes ya sintetizaron sus respuestas fuente
	if (noPreguntasSec2.count() * integrantesEquipo.count()) == respuestasUsuario.count():
		#Se les notifica a los integrantes del equipo que todos han acabado
		for i in integrantesEquipo:
			nombreUsuario = User.objects.get(id=i)
			hora = datetime.datetime.now()
			send_mail(
			'Tu equipo ya acabó de sintetizar las respuestas de las preguntas secundarias ganadoras.',
			f'Hola {nombreUsuario.first_name}, el último integrante de tu equipo ha terminado de sintetizar las respuestas de las preguntas secundarias ganadoras del tema {temaNombre}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.\n {hora}',
			settings.EMAIL_HOST_USER,
			[nombreUsuario.email],
			fail_silently=False,
			)
		#Si todo el equipo terminó redirigir a la pantalla de instrucciones del subpaso siguiente
		return redirect('AMCE:InstruccionesP3P3', id_grupo=id_grupo, id_tema=id_tema)
	else:
		#Por cada integrante del equipo vamos a verificar si ya tienen participación o no.
		for i in integrantesEquipo:
			nombreUsuario = User.objects.get(id=i)
			#Si se encuentra la participación de un usuario no pasa nada
			#Se consulta integrante x integrante para ver si tiene participación 
			
			integranteN = ParticipacionEst.objects.filter(estudiante_part=i).values_list('id_actividad', flat=True)
			try: #Si no tiene participación entonces le avisamos que no ha hecho el paso.
				if len(set(integranteN)&set(respuestasUsuario))!= noPreguntasSec2.count():
					#Por cada integrante del equipo se va a buscar su participación de la PI
					hora = datetime.datetime.now()
					send_mail(
					'Aviso, Faltas tu!',
					f'Hola {nombreUsuario.first_name}, tu equipo ya realizó la actividad de sintetizar las respuestas a las preguntas secundarias ganadoras del tema {temaNombre}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.\n {hora}',
					settings.EMAIL_HOST_USER,
					[nombreUsuario.email],
					fail_silently=False,
					)
			except:
				print('Todo está bien')

	return render(request, "estudiante/paso3/AvisoNoContinuarP3P2.html",{'id_tema':id_tema, 'id_grupo':id_grupo, 'current_user':current_user})

#Paso3Subpaso2 (función principal)
#Después de realizar todo el código me di cuenta que llame como id_pregunta_id a lo que realmente es id_respuesta_id, por que lo que se pasa es el id_de la respuesta fuente que corresponde sintetizar. En todos los casos lo que se pasa es el id de la respuesta fuente.
def RespuestaSintetizada(request, id_tema, id_grupo,id_pregunta_id):
	# Si accesas al URL sin haber hecho login con un usuario, 
	# te manda un error, en otro caso te devuelve al usuario actual(estudiante).
	current_user = get_object_or_404(User, pk=request.user.pk)
	estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	# Regresa el número id delequipo del usuario actual.
	equipo_id = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo_id, tema_definirProb_id = id_tema)
	# Obtengo todos los integrantes del equipo con ese id_equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo_id).values_list('estudiantes', flat=True)
	print("Todos los integrantes del equipo")
	print(integrantesEquipo)
	#Para obtener el número de preguntas secundarias ganadoras con las cuales se va a trabajar
	noPreguntasSec2 = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=2)
	numTotalPartici = Respuesta.objects.filter(definirProb=defProbPreguntaQuery.id_definirProb, tipo = 2)
	#Se obtienen los id's de las respuestas sintetizadas hechas por los integrantes del equipo.
	respuestasUsuario = Respuesta.objects.filter(definirProb = defProbPreguntaQuery, tipo=2).values_list('id_respuesta', flat=True)
	#Se obtienen las respuestas de la fuente hechas por el equipo.
	respuestasUsuarioFuente = Respuesta.objects.filter(definirProb = defProbPreguntaQuery, tipo=1).values_list('id_respuesta', flat=True)
	#Se obtienen los ids de las participaciones del usuario actual. 
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)
		#CASO 1: SI TODO EL EQUIPO TERMINA
	if ((noPreguntasSec2.count() * integrantesEquipo.count()) == respuestasUsuario.count()):
		#Mandamos a las instrucciones del paso3subpaso3 (votaciones)
		return redirect('AMCE:InstruccionesP3P3', id_grupo=id_grupo, id_tema=id_tema)
	else:
		# CASO 2: EL EQUIPO NO TERMINA SE VERIFICA SI EL USUARIO ACTUAL YA TIENE PARTICIPACIÓN, 
		#		  SI YA TIENE PARTICIPACION LO MANDAMOS AL AVISO DE NO CONTINUAR
		#Corroboras si el usuario actual ya participó.
		if len(set(idsUsuarioParticipacion)&set(respuestasUsuario)) == noPreguntasSec2.count():
			#Si ya terminó, lo mantenemos en el aviso no continuar hasta que todos terminen.
			return redirect('AMCE:AvisoNoContinuarP3P2',  id_grupo=id_grupo, id_tema=id_tema)
		# CASO 3: EL USUARIO ACTUAL NO TIENE PARTICIPACIÓN
		else:
			#Mandamos a la sintesis de las respuestas de la id_pregunta_id que corresponde.
			#Formulario de sintetizar respuesta
			#Como ya tenemos el id de la respuesta fuente a la que corresponde la sintesis, entonces traemos el contenido de esta respuesta fuente.
			preguntaSec = ParticipacionEst.objects.get(id_actividad=id_pregunta_id).contenido
			#Hacemos el join para traer todos los datos de la respuestafuente, junto con lo de participacionest.
			respuesta_fuente = Respuesta.objects.get(id_respuesta__estudiante_part_id = current_user.id,definirProb=defProbPreguntaQuery.id_definirProb,pregunta_id = id_pregunta_id, tipo = 1)
			respuesta_fuente_contenido = ParticipacionEst.objects.get(id_actividad=respuesta_fuente.id_respuesta_id).contenido
			#La fuente de donde se extrajo el contenido
			fuente = respuesta_fuente.fuente
			#La referencia de la fuente, es decir, los renglones y parrafos de donde se extrajo la información.
			referencia_fuente = respuesta_fuente.referencia
			print(referencia_fuente)
			# If this is a POST request then process the Form data
			if request.method == 'POST':
				# Create a form instance and populate it with data from the request (binding):
				form = RespuestaPregSecSintetizada(request.POST)
				#Si el formulario es válido, entonces creamos la instancia de la participacionEst que se va a guardar en la BD.
				if form.is_valid():
					print("Entramos al is_valid")
					cd = form.cleaned_data
					#Creamos un elemento para nuestra tabla ParticipacionEst 
					nuevaParticipacion = ParticipacionEst(contenido = cd['respPregSecSintetizada'],
																	estudiante_part_id = current_user.id)
					nuevaParticipacion.save()
					#Creamos la respuesta, y como es una relación oneToOne, usamos el id de la participacionEst que se creo anteriormente.
					respuestas_cd = Respuesta(
												id_respuesta_id=nuevaParticipacion.id_actividad,
												tipo = 2,
												pregunta = Pregunta.objects.get(id_pregunta=id_pregunta_id),
												definirProb = defProbPreguntaQuery,
												)
					# Guardamos en la base de datos
					respuestas_cd.save()
					print("Se hizo el save")
					messages.add_message(request, messages.SUCCESS, 'Se ha sintetizado correctamente tu respuesta.', extra_tags='alert-success')
					#---Ya que se guardo la respuesta debemos redireccionar a la siguiente respuesta fuente que será sintetizada.
					respuestas_sintetizadas_hechas = Respuesta.objects.filter(id_respuesta__estudiante_part_id = current_user.id,definirProb=defProbPreguntaQuery.id_definirProb, tipo = 2)	
					#Traemos los id de las respuestas fuente que hizo el usuario.
					respuestas_fuente= Respuesta.objects.filter(id_respuesta__estudiante_part_id = current_user.id ,definirProb=defProbPreguntaQuery.id_definirProb, tipo = 1).values_list('pregunta', flat=True)
					#Si el número de las respuestas sintetizadas es distinto al de las preguntas secundarias ganadoras
					if(respuestas_sintetizadas_hechas.count() != noPreguntasSec2.count()):
						#Redireccionamos a la siguiente respuesta por sintetizar.
						return redirect('AMCE:RespuestaSintetizada', id_grupo=id_grupo, id_tema=id_tema, id_pregunta_id = respuestas_fuente[respuestas_sintetizadas_hechas.count()])
					else:
						#Ya no hay respuestas fuente por sintetizar y mandamos al aviso.
						return redirect('AMCE:AvisoNoContinuarP3P2', id_grupo=id_grupo, id_tema=id_tema)
			else:
				form = RespuestaPregSecSintetizada()
	return render(request, "estudiante/paso3/RespuestaSintetizada.html", {'form' : form, 'preguntaSec': preguntaSec, 'temaNombre': temaNombre, 'id_pregunta_id':id_pregunta_id, 'respuesta_direc_fuente': respuesta_fuente_contenido, 'referencia_fuente':referencia_fuente, 'fuente':fuente, 'current_user':current_user})

def InstruccionesP3P3(request, id_tema, id_grupo):
	# Si accesas al URL sin haber hecho login con un usuario, 
	# te manda un error, en otro caso te devuelve al usuario actual(estudiante).
	current_user = get_object_or_404(User, pk=request.user.pk)
	#Devuelve el id del equipo del estudiante logeado.
	equipo_id = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo_id, tema_definirProb_id = id_tema)
	#Obtenemos a los integrantes del equipo.
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo_id).values_list('estudiantes', flat=True)
	#Obtenemos las preguntas secundarias ganadoras del equipo.
	noPreguntasSec2 = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=2).values_list('id_pregunta', flat = True)
	#Obtenemos los votos que han hecho los estudiantes del equipo.
	votosEquipo = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo=3)
	#Obtenemos los votos que ha hecho el estudiante.
	votosEstudiante = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb,estudiante = current_user, tipo=3)

	print("HEMOS ENTRADO A LAS INSTRUCCIONESP3P3")
	#CASO 1: SI TODO EL EQUIPO TERMINA
	if (noPreguntasSec2.count() * integrantesEquipo.count()) == votosEquipo.count():
		#Si todo el equipo terminó redirigir a la pantalla de instrucciones del subpaso siguiente
		print("Instrucciones paso tres subpaso cuatro desde instrucciones subpaso3")
		return redirect('AMCE:RankingRespuestasP3P4',  id_grupo=id_grupo, id_tema=id_tema)
		#return redirect('AMCE:EstMisGrupos')
	else:
		print("HEMOS ENTRADO AL ELSE DE LAS INSTRUCCIONESP3P3")
		# CASO 2: EL EQUIPO NO TERMINA SE VERIFICA SI EL USUARIO ACTUAL YA TIENE PARTICIPACIÓN, 
		#		  SI YA TIENE PARTICIPACION LO MANDAMOS AL AVISO DE NO CONTINUAR
		#Corroboras si el usuario actual ya participó.
		#Si el usuario ya tiene participación (i.e. existen elementos en el queryset)
		if (votosEstudiante.count() == noPreguntasSec2.count()):
			print("El usuario ya participo pero debe esperar a que los demás lo hagan.")
			return redirect('AMCE:AvisoNoContinuarP3P3', id_grupo=id_grupo, id_tema=id_tema)

		# CASO 3: EL USUARIO ACTUAL NO TIENE NI UNA PARTICIPACION
		elif votosEstudiante.count() == 0:
			#Si no, intentamos mandar a la primera pantalla de las respuestas de la primera id_pregunta
			try:
				print("La primer pregunta en sintetizar es", noPreguntasSec2[0])
				return render(request, "estudiante/paso3/InstruccionesP3P3.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'id_pregunta_id': noPreguntasSec2[0], 'current_user':current_user})
			except IndexError:
				print("Entramos al Index error")
		else:
			#Obtenemos los votos que ha hecho el estudiante.
			votosEstudianteHechos = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb,estudiante = current_user, tipo=3)
			return redirect('AMCE:EvaluarRespuestaSintetizada', id_grupo=id_grupo, id_tema=id_tema, id_pregunta_id = noPreguntasSec2[votosEstudianteHechos.count()])
	return render(request, "estudiante/paso3/AvisoNoContinuarP3P3.html",{'id_tema':id_tema, 'id_grupo':id_grupo, 'current_user':current_user})

def AvisoNoContinuarP3P3(request, id_tema, id_grupo):
	# Si accesas al URL sin haber hecho login con un usuario, 
	# te manda un error, en otro caso te devuelve al usuario actual(estudiante).
	current_user = get_object_or_404(User, pk=request.user.pk)
	#Devuelve el id del equipo del estudiante logeado.
	equipo_id = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#Se obtiene el Tema del equipo.
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo_id, tema_definirProb_id = id_tema)
	#Obtenemos a los integrantes del equipo.
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo_id).values_list('estudiantes', flat=True)
	#Obtenemos las preguntas secundarias ganadoras del equipo.
	noPreguntasSec2 = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=2).values_list('id_pregunta', flat = True)
	#Obtenemos los votos que han hecho los estudiantes del equipo.
	votosEquipo = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo=3)
	#Obtenemos los votos que ha hecho el estudiante.
	votosEstudiante = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb,estudiante = current_user, tipo=3)

	print("HEMOS ENTRADO A AvisoNoContinuarP3P3")
	#CASO 1: SI TODO EL EQUIPO TERMINA
	if (noPreguntasSec2.count() * integrantesEquipo.count()) == votosEquipo.count():
		#Si todo el equipo terminó redirigir a la pantalla de las votaciones de mayor a menor.
		#Mandamos los correos de finalización de paso
		for i in integrantesEquipo:
			nombreUsuario = User.objects.get(id=i)
			hora = datetime.datetime.now()
			send_mail(
			'Tu equipo ya acabó de evaluar las respuestas de las preguntas secundarias ganadoras.',
			f'Hola {nombreUsuario.first_name}, el último integrante de tu equipo ha terminado de evaluar las respuestas de las preguntas secundarias ganadoras del tema {temaNombre}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.\n {hora}',
			settings.EMAIL_HOST_USER,
			[nombreUsuario.email],
			fail_silently=False,
			)
		return redirect('AMCE:RankingRespuestasP3P4',  id_grupo=id_grupo, id_tema=id_tema)
		#return redirect('AMCE:EstMisGrupos')
	else:
		#Por cada integrante del equipo vamos a verificar si ya tienen participación o no.
		for i in integrantesEquipo:
			nombreUsuario = User.objects.get(id=i)
			#Si se encuentra la participación de un usuario no pasa nada
			#Se consulta integrante x integrante para ver si tiene participación 
			integranteN = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb,estudiante = i, tipo=3)
			try:
				if integranteN.count() != noPreguntasSec2.count():
					print("integranteN",integranteN.count())
					print("mandamos mensaje a ", nombreUsuario.first_name)
					#Por cada integrante del equipo se va a buscar su participación de la PI
					hora = datetime.datetime.now()
					send_mail(
					'Aviso, Faltas tu!',
					f'Hola {nombreUsuario.first_name}, tu equipo ya evaluó las respuestas de las preguntas secundarias ganadoras del tema {temaNombre}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.\n {hora}',
					settings.EMAIL_HOST_USER,
					[nombreUsuario.email],
					fail_silently=False,
					)
			except:
				print('Todo está bien')

	return render(request, "estudiante/paso3/AvisoNoContinuarP3P3.html",{'id_tema':id_tema, 'id_grupo':id_grupo, 'current_user':current_user})

def EvaluarRespuestaSintetizada(request, id_tema, id_grupo,id_pregunta_id):
	# Si accesas al URL sin haber hecho login con un usuario, 
	# te manda un error, en otro caso te devuelve al usuario actual(estudiante).
	current_user = get_object_or_404(User, pk=request.user.pk)
	#Obtenemos el tema asignado al equipo
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	#Obtenemos la pregunta secundaria con el id que pasamos por parametro, esto para pasarlo al template.
	preguntaSec = ParticipacionEst.objects.get(id_actividad=id_pregunta_id).contenido
	#Devuelve el id del equipo del estudiante logeado.
	equipo_id = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo_id, tema_definirProb_id = id_tema)
	#Hacemos la consulta de las respuestas sintetizadas del equipo (a la pregunta con id_pregunta_id), nos devuelve una lista con los id's.
	respuestas_sintetizadas_ids = Respuesta.objects.filter(definirProb=defProbPreguntaQuery.id_definirProb, pregunta_id = id_pregunta_id, tipo = 2).values_list('id_respuesta', flat = True)
	#Creamos una lista que almacenará las respuestas sintetizadas (objetos).
	resp_sintet_lista = []
	#Agregamos los elementos del query a la lista, para pasarla al template.
	for x in respuestas_sintetizadas_ids:
		respuesta_fuente_contenido = ParticipacionEst.objects.get(id_actividad=x).contenido
		resp_sintet_lista.append(respuesta_fuente_contenido)
	#Obtenemos a los integrantes del equipo.
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo_id).values_list('estudiantes', flat=True)
	#Obtenemos las preguntas secundarias ganadoras del equipo.
	noPreguntasSec2 = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=2).values_list('id_pregunta', flat = True)
	#Debemos considerar que una pregunta secundaria tiene sus respectivas respuestas sintetizadas, por ello,
	#para saber cuando un estudiante ha hecho una votación, relacionamos con la el id_pregunta, pues se cuenta por
	#bloque de respuestas.
	#Cada que un alumno vota por las respuestas de una pregunta se almacena una verificación en la tabla de EvaPreguntaSecundarias, con el id del estudiante, el id de la pregunta a la que corresponden esas respuestas y el tipo de voto que es. 
	#Obtenemos los votos que han hecho los estudiantes del equipo.
	votosEquipo = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo=3)
	#Obtenemos los votos que ha hecho el estudiante.
	votosEstudiante = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb,estudiante = current_user, tipo=3)
	numIntegrantes = integrantesEquipo.count()
	#print("HEMOS ENTRADO A LA FUNCIÓN DE EvaluarRespuestaSintetizada")
		#CASO 1: SI TODO EL EQUIPO TERMINA
	if ((noPreguntasSec2.count() * numIntegrantes) == votosEquipo.count()):
		#print("Entramos a las instrucciones de paso tres subpaso tres")
		return redirect('AMCE:RankingRespuestasP3P4', id_grupo=id_grupo, id_tema=id_tema)
		#return redirect('AMCE:EstMisGrupos')
	else:
		# CASO 2: EL EQUIPO NO TERMINA SE VERIFICA SI EL USUARIO ACTUAL YA TIENE PARTICIPACIÓN, 
		#		  SI YA TIENE PARTICIPACION LO MANDAMOS AL AVISO DE NO CONTINUAR
		#Corroboras si el usuario actual ya participó.
		if (votosEstudiante.count() == noPreguntasSec2.count()):
			# Página de: "Aviso: Tu equipo aún no termina de responder el formulario."
			#print("Manda al aviso no continuar porque no han terminado de votar todos los integrantes del equipo")
			return redirect('AMCE:AvisoNoContinuarP3P3',  id_grupo=id_grupo, id_tema=id_tema)
		# CASO 3: EL USUARIO ACTUAL NO TIENE PARTICIPACIÓN
		else:
			# If this is a POST request then process the Form data
			if request.method == 'POST':
				data=json.loads(request.body.decode('utf-8'))
				ratings=data['ratings']
				for key_respuesta, value_respuesta in ratings.items():
					#Se suma la cantidad de estrellitas que le dio el estudiante a la respectiva respuesta.
					print("Data", value_respuesta)
					voto_sumar = Respuesta.objects.filter(id_respuesta=key_respuesta, definirProb=defProbPreguntaQuery).update(votos=F('votos')+value_respuesta)
				#Se agrega el identificador del voto hecho por las respuestas de la pregunta_id
				voto_registro = EvaPreguntaSecundarias(estudiante=current_user,pregunta_id = id_pregunta_id, id_definirProb_pregunta=defProbPreguntaQuery, tipo = 3)
				voto_registro.save()
				#print("Se hizo el save")
				messages.add_message(request, messages.SUCCESS, 'Se ha guardado tu votación.', extra_tags='alert-success')
				#Obtenemos los votos que ha hecho el estudiante.
				votosEstudianteHechos = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb,estudiante = current_user, tipo=3)
				# Ya que se ha recibido el Post es importarle notificarle al HTML que haga un refresh y mande a
				# la siguiente pantalla. 
				# Por lo anterior, primero verificaremos si vamos a pasar a votar por las respuestas de la siguiente pregunta (si aún faltan) o nos vamos al aviso no continuar.
				# SI EL NUMERO DE VOTOS ES IGUAL AL NÚMERO DE PREGUNTAS SECUNDARIAS, ES POR QUE YA VOTO POR TODAS # LAS RESPUESTAS RELACIONADAS A CADA PREGUNTA. POR LO TANTO EL POST QUE SE RECIBIÓ FUE EL ÚLTIMO Y # TENEMOS QUE RECTIFICARLE AL HTML QUE YA FUE EL ÚLTIMO Y CAMBIE AL AVISO.
				if (votosEstudianteHechos.count() == noPreguntasSec2.count()):

					#Le mandaremos al html un json con los siguientes datos:
					response_data = {
						'url': 'AMCE:EvaluarRespuestaSintetizada',
						'id_grupo': id_grupo,
                        'id_tema': id_tema,
                        'id_pregunta_id': noPreguntasSec2[0], #Mandamos este para que no halla un error.
                        'ultimo': True  #Este post ya fue el último
					}

					#Por cada integrante del equipo vamos a verificar si ya tienen participación o no.
					for i in integrantesEquipo:
						nombreUsuario = User.objects.get(id=i)
						#Si se encuentra la participación de un usuario no pasa nada
						#Se consulta integrante x integrante para ver si tiene participación 
						integranteN = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb,estudiante = i, tipo=3)
						try:
							if integranteN.count() != noPreguntasSec2.count():
								print("integranteN",integranteN.count())
								print("mandamos mensaje a ", nombreUsuario.first_name)
								#Por cada integrante del equipo se va a buscar su participación de la PI
								hora = datetime.datetime.now()
								send_mail(
								'Aviso, Faltas tu!',
								f'Hola {nombreUsuario.first_name}, tu equipo ya evaluó las respuestas de las preguntas secundarias ganadoras del tema {temaNombre}. Entra a Búsqueda Colaborativa y continua con tu proceso de investigación.\n {hora}',
								settings.EMAIL_HOST_USER,
								[nombreUsuario.email],
								fail_silently=False,
								)
						except:
							print('Todo está bien')
					return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)
				else:
					#SI NO, AÚN FALTAN RESPUESTAS POR VOTAR, ENTONCES MANDAMOS EL ID DE LA PREGUNTA QUE SIGUE PARA
					# HACER
					response_data = {
							'url': 'AMCE:EvaluarRespuestaSintetizada',
							'id_grupo': id_grupo,
							'id_tema': id_tema,
							'id_pregunta_id': noPreguntasSec2[votosEstudianteHechos.count()], #Mandamos el id de la pregunta con respuestas que sigue por evaluar.
							'ultimo': False # El post aún no fue el último
					}
					#Mandamos la HTTP response con el json anterior.
					return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)

	return render(request, "estudiante/paso3/EvaluarRespuestaSintetizada.html",{'temaNombre': temaNombre, 'preguntaSec': preguntaSec,'id_tema':id_tema, 'id_grupo':id_grupo , 'resp_sintet_lista':resp_sintet_lista, 'respuestas_sintetizadas_ids': respuestas_sintetizadas_ids,'id_pregunta_id':id_pregunta_id, 'numIntegrantes':numIntegrantes, 'current_user':current_user})


def RankingRespuestasP3P4(request, id_tema, id_grupo):
	# Si accesas al URL sin haber hecho login con un usuario, 
	# te manda un error, en otro caso te devuelve al usuario actual(estudiante).
	current_user = get_object_or_404(User, pk=request.user.pk)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	## Regresa el número id delequipo del usuario actual.
	equipo_id = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo).id_equipo
	#Se obtiene el problema asignado a un equipo, esto para poder obtener el parámetro definirProb_pregunta_id
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo_id, tema_definirProb_id = id_tema)
	print("el definir problema pregunta query de este tema es el siguiente:")
	print(defProbPreguntaQuery.id_definirProb)
	# Obtengo todos los integrantes del equipo con ese id_equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo_id).values_list('estudiantes', flat=True)
	print("Todos los integrantes del equipo")
	print(integrantesEquipo)
	respuestasOrdenadasIds = Respuesta.objects.filter(definirProb=defProbPreguntaQuery.id_definirProb, tipo = 2).order_by('-votos')
	#Para obtener el número de preguntas secundarias ganadoras con las cuales se va a trabajar
	noPreguntasSec2 = Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=2)
	#Vamos a generar las listas que pasaremos en rquest, con los datos de las preguntas y respuestas sintetizadas.
	#Lista de preguntas
	preguntasSecLista = []
	#Agregamos las preguntas secundarias ganadoras a una lista
	for x in noPreguntasSec2:
		preguntasSecLista.append(x)
	#Lista de listas de respuestas por cada pregunta.
	respuestasOrdenadasIdsLista = []
	#Por cada pregunta secundaria
	for x in noPreguntasSec2:
		#Generamos la lista de sus respuestas sintetizadas, ordenadas de mayor cantidad de votos a menor cantidad de votos.
		respuestasOrdenadasIdsListaPreg = []
		respuestasOrdenadasIdsP = Respuesta.objects.filter(definirProb=defProbPreguntaQuery.id_definirProb, tipo = 2, pregunta = x).order_by('-votos')
		for y in respuestasOrdenadasIdsP:
			respuesta_fuente_contenido = ParticipacionEst.objects.get(id_actividad=y.id_respuesta_id).contenido
			respuestasOrdenadasIdsListaPreg.append(respuesta_fuente_contenido)
			#ASIGNAMOS LA RESPUESTA GANADORA (MÁS VOTADA)
			#Consultamos la respuesta que responde a la pregunta x, más votada.
			respuestaMasVotada = Respuesta.objects.filter(definirProb=defProbPreguntaQuery.id_definirProb, tipo = 2, pregunta = x).order_by('-votos')[0]
			#La volvemos ganadora
			respuestaGanadora = Respuesta.objects.filter(id_respuesta_id=respuestaMasVotada.id_respuesta_id).update(ganadora=True)
		respuestasOrdenadasIdsLista.append(respuestasOrdenadasIdsListaPreg)
	print(respuestasOrdenadasIdsLista)
	return render(request, "estudiante/paso3/RankingRespuestasP3P4.html",{'temaNombre': temaNombre, 'preguntasSecLista': preguntasSecLista,'id_tema':id_tema, 'id_grupo':id_grupo , 'respuestasOrdenadasIdsLista':respuestasOrdenadasIdsLista, 'current_user':current_user})

# --------------------------------------- ------ ---------------------------------------
# --------------------------------------- ------ ---------------------------------------
# --------------------------------------- Paso 4 ---------------------------------------
# --------------------------------------- ------ ---------------------------------------
# --------------------------------------- ------ ---------------------------------------
@student_required
@login_required
def VotoRespuestaPI(request, id_tema, id_grupo):
	# http://localhost:8000/estudiante/Grupo/56xjbvp/Tema/1/VotoRespuestaPI
	#Obtenemos informacion relevante sobre el usuario y su equipo
	current_user = get_object_or_404(User, pk=request.user.pk)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Obtenemos el problema asignado al equipo
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	#Obtenemos la pregunta inicial ganadora
	pregunta = Pregunta.objects.get(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=1)
	preguntaInicial = pregunta.id_pregunta.contenido
	#Revisamos si todo el equipo ya termino de emitir su voto para redirigir a la pagina de MejorRespuestaPI
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	#Obtenemos las respuestas a la pregunta inicial de todo el equipo.
	votosEquipo = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo=4)
	if len(integrantesEquipo) == len(votosEquipo):
		return redirect('AMCE:MejorRespuestaPI', id_tema=id_tema, id_grupo=id_grupo)
	#Revisamos si el usuario actual ya emitio su voto
	for v in votosEquipo:
		if v.estudiante.id == current_user.id:
			return redirect('AMCE:AvisoNoContinuarVotoRespuestaPI', id_tema=id_tema, id_grupo=id_grupo)

	if request.method == 'POST':
		#Obtenemos el cuerpo en formato JSON de la peticion que realiza el estudiante
		#El cuerpo de la peticion tiene la forma
		# {
		#	"ratings": {
		#		"id_respuesta": numero_estrellas,
		#	}
		# }
		data=json.loads(request.body.decode('utf-8'))
		ratings = data['ratings']
		#Iteramos sobre el diccionario de respuestas y sus respectivos votos
		for key_respuesta, value_respuesta in ratings.items():
			#Se suma la cantidad de estrellas que dio el estudiante a la respuesta.
			Respuesta.objects.filter(id_respuesta=key_respuesta, definirProb=defProbPreguntaQuery).update(votos=F('votos')+value_respuesta)
		#Registramos que un alumno ya realizo su voto, recordemos que el tipo de voto es 4 ya que pertenece al paso 4.
		voto_alumno = EvaPreguntaSecundarias(estudiante=current_user,pregunta = pregunta, id_definirProb_pregunta=defProbPreguntaQuery, tipo = 4)
		voto_alumno.save()
		messages.add_message(request, messages.SUCCESS, 'Se ha guardado tu votación.', extra_tags='alert-success')
		#Creamos el objeto json que se mandara como respuesta, el objeto contiene la url a la cual se redireccionara al usuario.
		response_data = {
			'url': '/estudiante/Grupo/#$333/Tema/#$334/AvisoNoContinuarVotoRespuestaPI'
			}
		#Mandamos la respuesta con el json anterior.
		return HttpResponse(json.dumps(response_data), content_type="application/json", status=200)

	#La primera vez que el usuario entra a la pagina (i.e., hace una peticion GET) se le mostrarán las respuestas por las que debera votar.
	#Obtenemos los identificadores de las respuestas de los integrantes del equipo
	respuestasId = Respuesta.objects.filter(definirProb=defProbPreguntaQuery, pregunta=pregunta,tipo=3).values_list('id_respuesta', flat=True).values_list('id_respuesta', flat = True)
	#Obtenemos  el contenido de las respuestas de los integrantes del equipo
	contenidoRespuestas = list(ParticipacionEst.objects.filter(id_actividad__in=respuestasId))
	#Obtenemos el numero de integrantes del equipo
	numIntegrantes=len(Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True))
	return render(request,"estudiante/paso4/VotoRespuestaPI.html",{'id_tema':id_tema, 'id_grupo':id_grupo, 'respuestas':contenidoRespuestas, 'respuestasId':respuestasId,'nombre_equipo': equipo.nombre_equipo, 'tema_nombre': temaNombre,'pregunta':preguntaInicial,'integrantes':numIntegrantes, 'current_user':current_user})

@student_required
@login_required
def ResponderPreguntaInicial(request, id_tema, id_grupo):
	# http://localhost:8000/estudiante/Grupo/56xjbvp/Tema/1/ResponderPreguntaInicial

	#Obtenemos informacion relevante sobre el usuario y su equipo
	current_user = get_object_or_404(User, pk=request.user.pk)
	estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
	temaNombre = Tema.objects.get(id_tema=id_tema).nombre_tema
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Obtenemos el problema asignado al equipo
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	#Obtenemos la pregunta inicial ganadora
	pregunta = Pregunta.objects.get(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=1)
	preguntaInicial = pregunta.id_pregunta.contenido

	#---------------------- Información obtenida del paso 3 ------------------------
	#Obtenemos las preguntas secundarias ganadoras 
	pregSecGanadoras = list(Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=2))
	#Almacenamos infoPaso3 = {'Contenido pregunta secundaria ganadora': 'Contenido respuesta sintetizada ganadora correspondiente a la pregunta secundaria ganadora',...}
	infoPaso3 = dict()
	for p in pregSecGanadoras:
		contenidoPregunta= p.id_pregunta.contenido
		#Por cada pregunta obtenemos sus respuestas sintetizadas ganadoras
		respuestasOrdenadasIdsP = list(Respuesta.objects.filter(definirProb=defProbPreguntaQuery.id_definirProb, tipo = 2, pregunta = p, ganadora = True))
		infoPaso3[contenidoPregunta] = [r.id_respuesta.contenido for r in respuestasOrdenadasIdsP]
	#-------------------------------------------------------------------------------

	#Procesamos el formulario que contiene la respuesta del estudiante a la pregunta inicial
	if request.method == 'POST':
		form = RespuestaPreguntaInicialForm(request.POST)
		#Revisamos que la informacion que contiene el formulario sea valida
		if form.is_valid():
			respuesta=form.cleaned_data['contenido']
			#Creamos una participacion estudiante con el fin de crear una respuesta 
			participacion=ParticipacionEst()
			participacion.estudiante_part=estudiante
			participacion.contenido=respuesta
			participacion.save()
			#Creamos una respuesta a la pregunta inicial (es por eso que es tipo=3) con la praticipacion creada previamente
			respuesta=Respuesta()
			respuesta.id_respuesta=participacion
			respuesta.pregunta=pregunta
			respuesta.definirProb=defProbPreguntaQuery
			respuesta.tipo=3
			respuesta.save()
			return redirect('AMCE:AvisoNoContinuarResponderPreguntaInicial', id_tema=id_tema, id_grupo=id_grupo)
	#La primera vez que el usuario entre a la pagina (i.e., hace una peticion GET) se le mostrara el formulario para que responda la pregunta inicial
	form = RespuestaPreguntaInicialForm()
	return render(request,"estudiante/paso4/ResponderPreguntaInicial.html", {'form':form,'id_tema':id_tema, 'id_grupo':id_grupo, 'nombre_tema':temaNombre, 'pregunta_inicial': preguntaInicial,'info_paso3':infoPaso3, 'current_user':current_user})

@student_required
@login_required
def AvisoNoContinuarResponderPreguntaInicial(request, id_tema, id_grupo):
	# http://localhost:8000/estudiante/Grupo/56xjbvp/Tema/1/AvisoNoContinuarResponderPreguntaInicial
	
	#Obtenemos informacion relevante sobre el usuario y su equipo
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Obtenemos el problema asignado al equipo
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	#Obtenemos la pregunta inicial ganadora
	pregunta = Pregunta.objects.get(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=1)
	nombreTemaPreguntaInicial = Tema.objects.get(id_tema=id_tema).nombre_tema

	#Revisamos si todo el equipo ya respondio la pregunta inicial
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	#Obtenemos las respuestas a la pregunta inicial de todo el equipo.
	respuestas = Respuesta.objects.filter(definirProb=defProbPreguntaQuery, pregunta=pregunta,tipo=3).values_list('id_respuesta', flat=True)
	#Verificamos si la longitud de la lista que contiene al equipo que ya respondio la pregunta inicial es igual a las respuestas iniciales dadas por el equipo.
	if len(integrantesEquipo) == len(respuestas):
		
		#Si ya respondieron todos los integrantes,notificamos que puede continuar con la investigación
		asunto = 'Tu equipo ya acabó de dar respuesta a la pregunta inicial.'
		mensaje=f'Hola #$%#, el ultimo integrante de tu equipo ha terminado de dar respuesta a la pregunta inicial del tema {nombreTemaPreguntaInicial}. Entra a Busqueda Colaborativa y continua con tu proceso de investigacion.'
		envia_correo(integrantesEquipo, asunto, mensaje)
		return redirect('AMCE:VotoRespuestaPI', id_grupo=id_grupo, id_tema=id_tema)

	#Si no se ha respondido la pregunta inicial, se redirecciona a la pagina de aviso no continuar
		
	#Por cada integrante del equipo vamos a verificar si ya tienen participación o no y se le manda el correo
	for i in integrantesEquipo:
		integranteN = ParticipacionEst.objects.filter(estudiante_part=i).values_list('id_actividad', flat=True)
		try:
			if not(bool(set(integranteN)&set(respuestas))):
				asunto = 'Aviso, Faltas tu!'
				mensaje=f"Hola #$%#, tu equipo ya realizó la actividad de dar respuesta a la pregunta inicial del tema {nombreTemaPreguntaInicial}, faltas tu! Entra a Busqueda Colaborativa y continua con tu proceso de investigacion."
				envia_correo([i], asunto, mensaje)
		except Exception as e:
			print('Todo está bien')
			print(e)
		
	return render(request, 'estudiante/paso4/AvisoNoContinuarResponderPreguntaInicial.html', {'id_tema':id_tema, 'id_grupo':id_grupo, 'current_user':current_user})

@student_required
@login_required
def AvisoNoContinuarVotoRespuestaPI(request, id_tema, id_grupo):

	#Obtenemos informacion relevante sobre el usuario y su equipo
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Obtenemos el problema asignado al equipo
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	nombreTemaPreguntaInicial = Tema.objects.get(id_tema=id_tema).nombre_tema

	#Revisamos si todo el equipo ya respondio la pregunta inicial
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	
	#Obtenemos las respuestas a la pregunta inicial de todo el equipo.
	votosEquipo = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery.id_definirProb, tipo=4)
	if len(integrantesEquipo) == len(votosEquipo):
		#Si ya respondieron todos los integrantes, notificamos que puede continuar con la investigación
		asunto = 'Tu equipo ya acabó de de dar su voto a las respuestas de la pregunta inicial.'
		mensaje=f'Hola #$%#, el ultimo integrante de tu equipo ha terminado de dar su voto a las respuestas de la pregunta inicial del tema {nombreTemaPreguntaInicial}. Entra a Busqueda Colaborativa y continua con tu proceso de investigacion.'
		envia_correo(integrantesEquipo, asunto, mensaje)
		return redirect('AMCE:MejorRespuestaPI', id_grupo=id_grupo, id_tema=id_tema)
	
	#Por cada integrante del equipo vamos a verificar si ya tienen participación o no y se le manda el correo a los integrantes
	#que falten por responder
	for i in integrantesEquipo:
		votoIntegrante = EvaPreguntaSecundarias.objects.filter(id_definirProb_pregunta=defProbPreguntaQuery,estudiante = i, tipo=4)
		if len(votoIntegrante) == 0:
			try:
				asunto = 'Aviso, Faltas tu!'
				mensaje=f"Hola #$%#, tu equipo ha terminado de dar su voto a las respuestas de la pregunta inicial del tema {nombreTemaPreguntaInicial}, faltas tu! Entra a Busqueda Colaborativa y continua con tu proceso de investigacion."
				envia_correo([i], asunto, mensaje)
			except Exception as e:
				print(e)
	return render(request, 'estudiante/paso4/AvisoNoContinuarVotoRespuestaPI.html', {'id_tema':id_tema, 'id_grupo':id_grupo, 'current_user':current_user})


@student_required
@login_required
def MejorRespuestaPI(request, id_tema, id_grupo):
	# http://localhost:8000/estudiante/Grupo/56xjbvp/Tema/1/MejorRespuestaPI

	#Obtenemos informacion relevante sobre el usuario y su equipo
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Obtenemos el problema asignado al equipo
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	#Obtenemos la pregunta inicial ganadora
	pregunta = Pregunta.objects.get(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=1)
	#Obtenemos las respuestas de la pregunta inicial de acuerdo a su numero de votos ordenadas de mayor a menor
	respuestas = list(Respuesta.objects.filter(definirProb=defProbPreguntaQuery, pregunta=pregunta,tipo=3).order_by('-votos'))
	respuesta_mayor_votos = respuestas[0].votos
	#Lista para almacenar todas las respuestas a la pregunta inicial que hayan resultado ganadoras
	respuestasGanadoras = []
	#Revisamos si el trabajo final ya fue entregado por el equipo
	if(defProbPreguntaQuery.trabajo_final):
		return redirect('AMCE:Final', id_grupo=id_grupo, id_tema=id_tema)

	#Agregamos el contenido de las respuestas con mayor numero de votos a la lista de respuestas ganadoras
	for r in respuestas:
		if r.votos == respuesta_mayor_votos:
			contenidoRespuesta =r.id_respuesta.contenido
			respuestasGanadoras.append(contenidoRespuesta)
			#Marcamos la respuesta como ganadora
			r.ganadora = True
			r.save()
		else:
			break
	#Lo siguiente únicamente sirve para modificar el texto en el html de acuerdo al número de respuestas ganadoras que tengamos
	mensaje_titulo = ''
	if(len(respuestasGanadoras)>1):
		mensaje_titulo = 'Respuestas más votadas a pregunta inicial:'
	else:
		mensaje_titulo = 'Respuesta más votada a pregunta inicial:'
	return render(request,"estudiante/paso4/MejorRespuestaPI.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'mensaje_titulo':mensaje_titulo,'respuestas':respuestasGanadoras,"respuesta_mayor_votos":respuesta_mayor_votos, 'current_user':current_user })


def envia_correo(integrantesEquipo,asunto,mensaje):
	"""
	Función para enviar un correo electrónico
	"""
	try:
		for i in integrantesEquipo:
			nombreUsuario = User.objects.get(id=i)
			msg = mensaje.replace("#$%#", nombreUsuario.first_name)
			send_mail(
			#Asunto
			asunto,
			#Mensaje
			msg,
			#Correo de quien envia
			settings.EMAIL_HOST_USER,
			[nombreUsuario.email],
			#Correo de quien recibe
			fail_silently=False,
			)
	#Si no se puede enviar el correo, se imprime el error		
	except Exception as e:
		print('ERROR AL TRATAR DE ENVIAR EL CORREO')
		#Imprimimos el error
		print(e)

@student_required
@login_required
def InstruccionesGeneraPDF(request, id_tema, id_grupo):
	# http://localhost:8000/estudiante/Grupo/56xjbvp/Tema/1/InstruccionesGeneraPDF
	#Obtenemos informacion relevante sobre el usuario y su equipo
	current_user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	#Obtenemos el problema asignado al equipo
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	#Obtenemos el tipo de entregable asignado al equipo
	tipo_entregable = int(defProbPreguntaQuery.entregable)
	#Obtenemos la lista de tuplas (número, tipo_de_entregable) de los distintos tipos de entregables
	ent=[ c for c in DefinirProblema.entregable.field.choices]
	entregable=ent[tipo_entregable][1]
	return render(request,"estudiante/paso4/InstruccionesGeneraPDF.html",{'id_tema':id_tema, 'id_grupo':id_grupo, 'entregable':entregable, 'current_user':current_user})


@student_required
@login_required
def TrabajoFinal(request, id_tema, id_grupo):
	# http://localhost:8000/estudiante/Grupo/56xjbvp/Tema/1/TrabajoFinal
	# http://localhost:8000/estudiante/Grupo/q995b68/Tema/2/TrabajoFinal
	# Obtenenmos información relevante
	current_user = get_object_or_404(User, pk=request.user.pk)
	estudiante = Estudiante.objects.get(user_estudiante=current_user.id)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)

	#Obtenemos el tipo de entregable asignado al equipo
	tipo_entregable = int(defProbPreguntaQuery.entregable)
	#Obtenemos la lista de tuplas (número, tipo_de_entregable) de los distintos tipos de entregables
	ent=[ c for c in DefinirProblema.entregable.field.choices]
	entregable=ent[tipo_entregable][1]

	# Revisamos si algun alumno del equipo ya subio el trabajo final, 
	# en caso de que sí lo redirigimos a la pantalla final.
	if defProbPreguntaQuery.trabajo_final:
		return redirect('AMCE:Final', id_tema=id_tema, id_grupo=id_grupo)
	
	
	# Manejamos la entrega del trabajo final por parte del usuario
	# Nota: Recuerda que solo uno de los usuarios de todo el equipo debe entregar el trabajo final.
	if request.method == 'POST':
		#Si ya fue entregado previamente por un integrante del equipo, ignoramos entonces el contenido del formulario
		if defProbPreguntaQuery.trabajo_final:
			return redirect('AMCE:Final', id_tema=id_tema, id_grupo=id_grupo)
		form = RespuestaPreguntaInicialForm(request.POST)
		#Revisamos que el formulario sea valido
		if form.is_valid():
			link=form.cleaned_data['contenido']
			participacion=ParticipacionEst()
			participacion.estudiante_part=estudiante
			participacion.contenido=link
			participacion.save()
			defProbPreguntaQuery.trabajo_final=participacion
			defProbPreguntaQuery.save()
			#Si ya respondieron todos los integrantes, notificamos que el equipo ha terminado la investigación
			asunto = 'Tu equipo ha finalizado la investigación!'
			mensaje=f'Hola #$%#, tu equipo ha terminado la investigación. Ahora solo tienes que esperar la retroalimentación de tu profesor.'
			integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
			envia_correo(integrantesEquipo, asunto, mensaje)
			return redirect('AMCE:Final', id_tema=id_tema, id_grupo=id_grupo)
		else:
			print("Formulario invalido ")
	form = RespuestaTrabajoFinalForm()
	return render(request,"estudiante/paso4/TrabajoFinal.html", {'form':form,'id_tema':id_tema, 'id_grupo':id_grupo, 'entregable':entregable, 'current_user':current_user})

@student_required
@login_required
def Final(request, id_tema, id_grupo):
	# http://localhost:8000/estudiante/Grupo/56xjbvp/Tema/1/Final
	# http://localhost:8000/estudiante/Grupo/q995b68/Tema/2/Final
	# Obtenenmos información relevante
	current_user = get_object_or_404(User, pk=request.user.pk) 
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	nombreEquipo = equipo.nombre_equipo
	# Obtenemos al alumno que subio el trabajo final para mostrar su nombre en el HTML
	participacion=defProbPreguntaQuery.trabajo_final
	estudiante=participacion.estudiante_part
	nombreEstudiante=estudiante.user_estudiante.first_name

	# definirProb = DefinirProblema.objects.get(equipo_definirProb=id_equipo, tema_definirProb=id_tema)
	# paso = definirProb.paso
	# print("#####################")
	# print("paso",paso)
	# print("#####################")
	return render(request,"estudiante/paso4/Final.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'nombre_equipo':nombreEquipo, 'nombre_estudiante':nombreEstudiante, 'current_user':current_user})
	

@student_required
@login_required
def InstruccionesPaso4(request, id_tema, id_grupo):
	# Obtenemos información relevante
	current_user = get_object_or_404(User, pk=request.user.pk) 
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema)
	DefinirProblema.objects.filter(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = id_tema).update(paso=4)
	# Obtenemos el número de integrantes del equipo
	integrantesEquipo = Equipo.objects.filter(id_equipo=equipo.id_equipo).values_list('estudiantes', flat=True)
	respuestasUsuario = Respuesta.objects.filter(definirProb = defProbPreguntaQuery, tipo=3).values_list('id_respuesta', flat=True)
	# Obtenemos las participaciones del usuario actual
	idsUsuarioParticipacion = ParticipacionEst.objects.filter(estudiante_part=current_user.id).values_list('id_actividad', flat=True)
	# Revisamos si todos los integrantes ya respondieron la pregunta inicial
	if len(integrantesEquipo) == len(respuestasUsuario):
		#Si todos los integrantes ya la respondieron , redireccionamos a la pagina de votos de las respuestas a la pregunta inicial
		return redirect('AMCE:VotoRespuestaPI', id_tema=id_tema, id_grupo=id_grupo)
	#Si, aun no responden todos los integrantes, revisamos si el usuario ya respondio la pregunta inicial, si ya la respondió tiene que esperar 
	if bool(set(idsUsuarioParticipacion)&set(respuestasUsuario)):
		return redirect('AMCE:AvisoNoContinuarResponderPreguntaInicial', id_tema=id_tema, id_grupo=id_grupo)
	#Si nadie ha votado entonces mostramos el formulario para que el usuario responda la pregunta inicial
	return render(request,"estudiante/paso4/InstruccionesPaso4.html", {'id_tema':id_tema, 'id_grupo':id_grupo, 'current_user':current_user})


@student_required
@login_required
def generaInvestigacionPDF(request, id_tema, id_grupo):
	# Obtenemos información relevante
	current_user = get_object_or_404(User, pk=request.user.pk)
	tema = Tema.objects.get(id_tema=id_tema)
	equipo = Equipo.objects.get(estudiantes=current_user.id, grupo_equipo=id_grupo)
	integrantes = equipo.estudiantes.all()
	defProbPreguntaQuery = DefinirProblema.objects.get(equipo_definirProb_id = equipo.id_equipo, tema_definirProb_id = tema.id_tema)
	preguntaInicialP4 = Pregunta.objects.get(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=1)


	#Creamos una instancia de la clase Texto
	texto=Texto()
	texto.setTema(tema)
	texto.setGrupo(id_grupo)
	texto.setInformacionDelEquipo(equipo, integrantes)

	preguntaInicialGanadora = Pregunta.objects.get(definirProb_pregunta = defProbPreguntaQuery, tipo_pregunta=1, ganadora=True)

	#Obtenemos el _tipo de entregable_ asignado al equipo
	tipo_entregable = int(defProbPreguntaQuery.entregable)
	#Obtenemos la lista de tuplas (número, tipo_de_entregable) de los distintos tipos de entregables
	ent=[ c for c in DefinirProblema.entregable.field.choices]
	entregable=ent[tipo_entregable][1]
	texto.setEntregable(entregable)

	#Obtenemos del _paso 1_ los comentarios de la pregunta ganadora
	ComentariosPreguntaInicialGanadora = ComentariosPreguntaInicial.objects.filter(pregunta_id = preguntaInicialGanadora)	

	texto.setPreguntaInicialGanadora(preguntaInicialGanadora, ComentariosPreguntaInicialGanadora)

	#Obtenemos del _paso 3_ las preguntas secundarias ganadoras del equipo con sus respuestas sintetizadas ganadoras
	#Obtenemos las preguntas secundarias ganadoras 
	pregSecGanadoras = list(Pregunta.objects.filter(definirProb_pregunta = defProbPreguntaQuery, ganadora=True , tipo_pregunta=2))
	respuestasSintetizadasGanadoras = [] 
	for p in pregSecGanadoras:
		#Obtenemos las respuestas sintetizadas ganadoras de cada pregunta
		respuestasSintetizadasGanadoras.append(Respuesta.objects.filter(definirProb=defProbPreguntaQuery.id_definirProb, tipo = 2, pregunta = p, ganadora = True)[0])
	texto.setPreguntasSecundariasGanadoras(pregSecGanadoras, respuestasSintetizadasGanadoras)

	#Obtenemos del _paso 2_ las fuentes ganadoras del equipo y sus comentarios 
	fuentesEquipoGanadoras = Fuente.objects.filter(id_defproblema=defProbPreguntaQuery, ganadora = True)
	comentariosFuentes = EvaluacionFuentesSel.objects.filter(id_defproblema=defProbPreguntaQuery)
	texto.setFuentesGanadoras(fuentesEquipoGanadoras, comentariosFuentes)

	#Obtenemos del _paso 4_ las respuestas a la pregunta inicial ganadora 
	respuestasGanadoras=list(Respuesta.objects.filter(definirProb=defProbPreguntaQuery, pregunta=preguntaInicialP4,tipo=3,ganadora=True))
	texto.setRespuestasPreguntaInicialGanadora(respuestasGanadoras)
	
	#Creamos una instancia de la clase CreacionPDF
	pdfCreacion=CreacionPDF(texto)
	#Archivo pdf que se enviara como respuesta
	file=pdfCreacion.crearPDF()
	
	#Regresamos como respuesta el pdf creado
	return HttpResponse(file, content_type='application/pdf') 


class Texto:
	"""
		Clase que contiene la información toda la informacion referente para contruir el archivo pdf que contiene
		toda la informacion con respecto a la investigacion del tema asignado
	"""
	# Atributo donde guardamos la información del equipo (i.e. nombre del equipo, integrantes del equipo)
	informacionDelEquipo = dict()
	# Atributo donde guardamos la información de la pregunta inicial ganadora (i.e. la pregunta inicial ganadora, los comentarios hechos a la pregunta inicial)
	preguntaInicialGanadora = dict()	
	# Atributo donde guardamos las fuentes ganadoras (i.e. las fuentes ganadoras, los comentarios hechos por el equipo a c/u de las fuentes)
	fuentesGanadoras = dict()
	# Atributo donde guardamos la(s) respuesta(s) a la pregunta inicial ganadora 
	respuestasPreguntaInicialGanadoras = dict()
	# Atributo donde guardamos las preguntas secundarias ganadoras así como sus respuestas
	preguntasSecundariasGanadoras = dict()
	mensajeFinal=dict()
	entregable=""

	def __init__(self):
		# Inicializamos los atributos
		self.informacionDelEquipo["titulo"]= "Información del Equipo"
		self.preguntaInicialGanadora["titulo"]= "Pregunta Inicial Ganadora"
		self.fuentesGanadoras["titulo"] = "Fuentes Ganadoras"
		self.respuestasPreguntaInicialGanadoras["titulo"] = "Respuestas a la Pregunta Inicial Ganadora"
		self.preguntasSecundariasGanadoras["titulo"] = "Preguntas Secundarias Ganadoras"
		self.mensajeFinal["titulo"] = "Siguientes pasos"
		
		
	def setGrupo(self, grupo):
		"""
			Funcion que asigna el grupo al que pertenece el equipo
		"""
		self.grupo = grupo
	
	def setTema(self, tema):
		"""
			Funcion que asigna el tema al que pertenece el equipo
		"""
		self.tema = tema

	def setInformacionDelEquipo(self, equipo, integrantes):
		"""
			Funcion que asigna la informacion del equipo (i.e. nombre del equipo, integrantes del equipo)
		"""	
		self.informacionDelEquipo["nombreEquipo"] = equipo
		self.informacionDelEquipo["integrantes"] = integrantes
	
	def setEntregable(self, entregable):
		"""
			Funcion que asigna el tipo de trabajo que entregara el equipo
		"""
		self.entregable = entregable
		self.setMensajeFinal()

	def setPreguntaInicialGanadora(self, pregunta,comentarios):
		"""
			Funcion que asigna el contenido de la pregunta inicial ganadora y sus respectivos comentarios
		"""
		self.preguntaInicialGanadora["contenido"] = pregunta.id_pregunta.contenido
		self.preguntaInicialGanadora["comentarios"] = [com.participacionEst.contenido for com in comentarios]

	def setFuentesGanadoras(self, fuentes, comentarios):
		"""
			Funcion que asigna las fuentes ganadoras y sus respectivos comentarios
		"""
		self.fuentesGanadoras["fuentes"] = [f for f in fuentes]
		self.fuentesGanadoras["comentarios"] = []
		for f in fuentes:
			com=[c.comentario for c in comentarios if f.id == c.id_fuente.id]
			self.fuentesGanadoras["comentarios"].append(com)
	
	def setPreguntasSecundariasGanadoras(self, preguntas, respuestas):
		"""
			Funcion que asigna las preguntas secundarias ganadoras y sus respectivas respuestas
		"""
				
		self.preguntasSecundariasGanadoras["preguntas"] = [p.id_pregunta.contenido for p in preguntas]
		self.preguntasSecundariasGanadoras["respuestas"] = [r.id_respuesta.contenido for r in respuestas]
		
	
	def setRespuestasPreguntaInicialGanadora(self, respuestas):
		"""
			Funcion que asigna las respuestas a la pregunta inicial ganadora
		"""
		self.respuestasPreguntaInicialGanadoras["respuestas"] = [r.id_respuesta.contenido for r in respuestas]

	def setMensajeFinal(self):
		""""
			Mensaje final del pdf
		"""
		self.mensajeFinal["mensaje"] = f"Recuerda que debes organizarte con tus compañeros de equipo y en colaboración deberán generar un {self.entregable} (el tipo de trabajo anterior les fue asignado por su profesor) en donde demuestren todo lo aprendido. Por lo que es recomendable usar este pdf que contiene sus respuestas dadas en los pasos anteriores como material de apoyo. Es importante mencionar que para generar su producto, podrán usar cualquier herramienta externa que deseen, mientras únicamente anexen el link. ¡Éxito!. "
		
		
	def __str__(self) -> str:
		""""
			Método toString para cerciorarnos de que funciona la clase
		"""
		s= f'''
				{self.grupo}\n
				{self.tema}\n
			\n
			\n
			{self.informacionDelEquipo["titulo"]}
			{self.informacionDelEquipo["nombreEquipo"]}
			{self.informacionDelEquipo["integrantes"]}
			\n
			\n
			{self.preguntaInicialGanadora["titulo"]}
			{self.preguntaInicialGanadora["contenido"]}
			{self.preguntaInicialGanadora["comentarios"]}
			\n
			\n
			{self.fuentesGanadoras["titulo"]}
			{self.fuentesGanadoras["fuentes"]}
			{self.fuentesGanadoras["comentarios"]}
			\n
			\n
			{self.respuestasPreguntaInicialGanadoras["titulo"]}
			{self.respuestasPreguntaInicialGanadoras["respuestas"]}	
			\n
			\n
			{self.mensajeFinal["titulo"]}
			{self.mensajeFinal["mensaje"]}	
		'''
		return s



class CreacionPDF:
	"""
	Clase encargada de contruir el pdf
	Nota: El pdf se construye con base en la informacion que contiene su atibuto texto el cual se le pasa en el constructor
		El Pdf se divide en varias secciones las cuales son construidas individualmente por cada uno de los metodos de la clase,
		Las secciones ordenadas en orden de aparicion son:
			- Encabezado
			- Informacion del equipo
			- Pregunta inicial ganadora
			- Fuentes ganadoras
			- Preguntas secundarias ganadoras	
			- Respuestas a la pregunta inicial ganadora
			- Mensaje final 
	"""
	def __init__(self, texto):
		#Atributo de tipo Texto que contiene toda la informacion necesaria para contriur el pdf
		self.texto = texto
		#Atributo de la biblioteca fpdf para constriur el pdf
		self.pdf=FPDF()
		self.pdf.add_page()
		
	def setEncabezado(self):
		# Logo
		self.pdf.image('./static/assets/images/logo_busqueda.png', x = 85, y = 8, w= 40)
		self.pdf.ln(20)
		
		#Profesor
		self.pdf.set_font("Arial", size=13)
		profesor = self.texto.tema.profesor_tema	
		self.pdf.cell(w=0, h=8, txt = f"Profesor: {profesor} ", align = 'C')
		self.pdf.ln(8)

		#Grupo
		self.pdf.set_font("Arial", size=13)
		grupo = self.texto.grupo	
		self.pdf.cell(w=0, h=8, txt = f"Grupo: {grupo} ", align = 'C')
		self.pdf.ln(8)

		#Tema
		self.pdf.set_font("Arial", size=13)
		tema = self.texto.tema
		self.pdf.multi_cell(w=0, h=8, txt=f"Tema: \"{tema}\"", align="C")	

	def informacionDelEquipo(self):
		self.pdf.ln(9)
		titulo = self.texto.informacionDelEquipo["titulo"]
		nombreEquipo = self.texto.informacionDelEquipo["nombreEquipo"]
		integrantes = self.texto.informacionDelEquipo["integrantes"]
		self.pdf.set_font("Arial",style="B", size=14)
		self.pdf.cell(w=0, h=8, txt = f"1. {titulo}", align = 'L')
		self.pdf.ln(8)
		self.pdf.set_font("Arial",size=10)
		self.pdf.cell(w=32.5, h=8, txt = f"Nombre del equipo: ", align = 'L')
		self.pdf.set_font("Arial", style="I", size=10)
		self.pdf.cell(w=0, h=8, txt = f"{nombreEquipo}", align = 'L')
		self.pdf.ln(8)
		self.pdf.set_font("Arial", size=10)
		self.pdf.cell(w=0, h=8, txt = f"Integrantes del equipo: ", align = 'L')
		self.pdf.ln(8)
		for estudiante in integrantes:
			self.pdf.ln(1.5)
			self.pdf.set_font("Arial", size=10)
			self.pdf.cell(w=10, h=8, txt = f"", align = 'L')
			self.pdf.multi_cell(w=0, h=5, txt=f"- {estudiante}", align="L")

	def preguntaInicialGanadoraSubtema(self):
		self.pdf.ln(8)
		titulo = self.texto.preguntaInicialGanadora["titulo"]
		texto = "De todas la preguntas iniciales que realizaron cada uno del los integrantes del equipo, la pregunta que obtuvo más votos fue: "
		texto2 = "Comentarios de los estudiantes hacía la pregunta inicial seleccionada por el equipo:"
		comentarios=self.texto.preguntaInicialGanadora["comentarios"]
		preguntaGanadora= self.texto.preguntaInicialGanadora["contenido"]
		self.pdf.set_font("Arial",style="B", size=14)
		self.pdf.cell(w=0, h=8, txt = f"2. {titulo}", align = 'L')
		self.pdf.ln(9)
		self.pdf.set_font("Arial", size=10)
		self.pdf.multi_cell(w=0, h=5, txt=texto, align="L")
		self.pdf.ln(1.5)
		self.pdf.set_font("Arial",style="I", size=10)
		self.pdf.cell(w=0, h=8, txt = f"{preguntaGanadora}", align = 'C')
		self.pdf.set_font("Arial", size=10)
		self.pdf.ln(12)
		self.pdf.set_font("Arial", size=10)
		self.pdf.multi_cell(w=0, h=5, txt=texto2, align="L")
		for(comentario) in comentarios:
			self.pdf.ln(1.5)
			self.pdf.set_font("Arial", size=10)
			self.pdf.cell(w=10, h=8, txt = f"", align = 'C')
			self.pdf.multi_cell(w=0, h=5, txt=f"- {comentario}", align="L")

	def fuentesGanadoras(self):
		self.pdf.ln(8)
		titulo = self.texto.fuentesGanadoras["titulo"]
		texto = "Las fuentes seleccionadas por el equipo para la realización de la invertigación son las siguientes: "
		texto2 = "Comentarios de los estudiantes hacía las fuente seleccionada por el equipo:"
		fuentesGanadoras= self.texto.fuentesGanadoras["fuentes"]
		ComentariosFuentesGanadoras=self.texto.fuentesGanadoras["comentarios"]
		self.pdf.set_font("Arial",style="B", size=14)
		self.pdf.cell(w=0, h=8, txt = f"3. {titulo}", align = 'L')
		self.pdf.ln(9)
		self.pdf.set_font("Arial", size=10)
		self.pdf.multi_cell(w=0, h=8, txt = texto, align = 'L')
		self.pdf.ln(3)
		for (fuente,comentario) in zip(fuentesGanadoras, ComentariosFuentesGanadoras):
			self.pdf.set_font("Arial", size=10)
			self.pdf.cell(w=10, h=8, txt = f"", align = 'C')
			self.pdf.multi_cell(w=0, h=5, txt=f"- {fuente}", align="L")
			self.pdf.ln(1.5)
			self.pdf.cell(w=10, h=8, txt = f"", align = 'C')
			self.pdf.set_font("Arial",style="B", size=10)
			self.pdf.cell(w=0, h=8, txt = texto2, align = 'L')
			self.pdf.ln(5)
			for comen in comentario:
				self.pdf.ln(3)
				self.pdf.set_font("Arial", size=9)
				self.pdf.set_font("Arial",style="B", size=9)
				self.pdf.cell(w=20, h=8, txt = f"", align = 'C')
				self.pdf.cell(w=2, h=6.5, txt = f"*", align = 'L')
				self.pdf.set_font("Arial", size=9)
				self.pdf.multi_cell(w=0, h=5, txt=f"{comen}", align="L")
				self.pdf.ln(3)
	

	def PreguntasSecundariasGanadoras(self):
		self.pdf.ln(8)
		titulo = self.texto.preguntasSecundariasGanadoras["titulo"]
		texto = "A continuación se muestran las preguntas secundarias ganadoras, seguidas por su respectiva respuesta sintetizada ganadora:"
		preguntasSecundariasGanadoras=self.texto.preguntasSecundariasGanadoras["preguntas"]
		respuestasSintetizadasGanadoras=self.texto.preguntasSecundariasGanadoras["respuestas"]
		self.pdf.set_font("Arial",style="B", size=14)
		self.pdf.cell(w=0, h=8, txt = f"4. {titulo}", align = 'L')
		self.pdf.ln(9)
		self.pdf.set_font("Arial", size=10)
		self.pdf.multi_cell(w=0, h=5, txt=texto, align="L")
		self.pdf.ln(1.5)
		for (p,r) in zip(preguntasSecundariasGanadoras, respuestasSintetizadasGanadoras):
			self.pdf.set_font("Arial",style="I", size=10)	
			self.pdf.cell(w=0, h=8, txt = f"{p}", align = 'l')
			self.pdf.ln(9)
			self.pdf.set_font("Arial", size=10)
			self.pdf.cell(w=10, h=8, txt = f"", align = 'l')
			self.pdf.multi_cell(w=0, h=5, txt=f"- {r}", align="L")

	def respuestasPreguntaInicialGanadoras(self):
		self.pdf.ln(8)
		titulo = self.texto.respuestasPreguntaInicialGanadoras["titulo"]
		s= "la respuesta que obtuvo más votos fue: " if self.texto.respuestasPreguntaInicialGanadoras["respuestas"] == 1 else "las respuestas que obtuvieron más votos fueron: "
		texto = f"De todas las respuestas a la pregunta inicial que dieron cada uno del los integrantes del equipo, {s}"
		respuestas=self.texto.respuestasPreguntaInicialGanadoras["respuestas"]
		self.pdf.set_font("Arial",style="B", size=14)
		self.pdf.cell(w=0, h=8, txt = f"5. {titulo}", align = 'L')
		self.pdf.ln(9)
		self.pdf.set_font("Arial", size=10)
		self.pdf.multi_cell(w=0, h=5, txt=texto, align="L")
		self.pdf.ln(1.5)
		for r in  respuestas:
			self.pdf.ln(1.5)
			self.pdf.set_font("Arial", size=10)
			self.pdf.cell(w=10, h=8, txt = f"", align = 'C')
			self.pdf.multi_cell(w=0, h=5, txt=f"- {r}", align="L")


	def setMensajeFinal(self):
		self.pdf.ln(8)
		titulo = self.texto.mensajeFinal["titulo"]
		texto = self.texto.mensajeFinal["mensaje"]
		self.pdf.set_font("Arial",style="B", size=14)
		self.pdf.cell(w=0, h=8, txt = f"6. {titulo}", align = 'L')
		self.pdf.ln(9)
		self.pdf.set_font("Arial", size=10)
		self.pdf.multi_cell(w=0, h=5, txt=texto, align="L")

	def crearPDF(self):
		self.setEncabezado()
		self.informacionDelEquipo()
		self.preguntaInicialGanadoraSubtema()
		self.fuentesGanadoras()
		self.PreguntasSecundariasGanadoras()
		self.respuestasPreguntaInicialGanadoras()
		self.setMensajeFinal()
		return self.pdf.output(dest='S').encode('latin-1')
	
