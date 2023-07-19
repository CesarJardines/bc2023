from ast import For
from urllib.parse import urlencode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..forms import *
from django.contrib.auth import authenticate, login
from django.template import RequestContext
from django.contrib.auth.models import User
from django.views.generic import CreateView
from ..models import *
from ..decorators import teacher_required
from django.urls import reverse
import random
import string


class ProfSignup(CreateView):
	model = User
	form_class = ProfSignupForm
	template_name = 'registration/signup_form.html'
	
	def get_context_data(self, **kwargs):
		kwargs['user_type'] = 'Profesor'
		return super().get_context_data(**kwargs)

	def form_valid(self, form):
		user = form.save()
		login(self.request, user)
		return redirect('AMCE:ProfMisGrupos')
		
@teacher_required
def vistaProfesor(request):
	return render(request,"profesor/vistaProfesor.html")

@teacher_required
@login_required
def ProfMisGrupos(request):
	"""
		Función para la vista MisGrupos
		Se muestran los grupos asociados al profesor actual
	"""
	user = get_object_or_404(User, pk=request.user.pk)
	grupos = Grupo.objects.filter(profesor_grupo=user.pk)
	grupos = grupos[::-1]
	return render(request,"profesor/MisGrupos.html", {'grupos':grupos,'current_user':user})

@teacher_required
@login_required
def ProfCrearGrupo(request):
	"""
		Función para la vista CrearGrupo
		Se crea el grupo cuando se submite el formulario
	"""
	user = get_object_or_404(User, pk=request.user.pk)
	profesor = Profesor.objects.get(user_profesor=user.pk)
	if request.method == 'POST':
		form = FormGrupo(request.POST)
		# Mientras exista un grupo que tenga el id que generamos, generamos otro
		if form.is_valid():
			while True:
				id_grupo = random_string(7)
				ya_existe = Grupo.objects.filter(id_grupo=id_grupo)
				if not ya_existe.exists():
					break
			
			nuevo_grupo = Grupo(id_grupo=id_grupo,
								nombre_grupo=form.cleaned_data['nombre_grupo'], 
								materia=form.cleaned_data['materia'], 
								institucion=form.cleaned_data['institucion'], 
								profesor_grupo=profesor)

			messages.add_message(request, messages.INFO, 'Grupo creado exitosamente', extra_tags='alert-success')
			nuevo_grupo.save()
			form = FormGrupo()
			return redirect(reverse('AMCE:ProfPaginaGrupo',  args=[id_grupo]))
	else:
		form = FormGrupo()
	return render(request, 'profesor/CrearGrupo.html', {'form': form,'current_user':user})

@teacher_required
@login_required
def ProfEditarGrupo(request, id_grupo):
	"""
		Función para la vista EditarGrupo
		Se edita el grupo cuando se submite el formulario
	"""
	user = get_object_or_404(User, pk=request.user.pk)
	try:
		grupo = Grupo.objects.get(id_grupo = id_grupo)
	except Grupo.DoesNotExist:
		messages.add_message(request, messages.ERROR, 'El grupo que intentaste editar no existe', extra_tags='alert-danger')
		return redirect(reverse('AMCE:ProfMisGrupos'))
	if request.method == 'POST':
		form = FormGrupo(request.POST, instance=grupo)
		if form.is_valid():
			grupo.nombre_grupo = form.cleaned_data['nombre_grupo']
			grupo.materia = form.cleaned_data['materia']
			grupo.institucion = form.cleaned_data['institucion']
			grupo.save()

			messages.add_message(request, messages.INFO, 'Grupo editado exitosamente', extra_tags='alert-success')
			return redirect(reverse('AMCE:ProfMisGrupos'))
	else:
		form = FormGrupo(instance=grupo)
	return render(request, 'profesor/EditarGrupo.html', {'form': form, 'id_grupo': id_grupo,'current_user':user})

@teacher_required
@login_required
def ProfEliminarGrupo(request, id_grupo):
	"""
		Función para eliminar un grupo
	"""
	try:
		grupo = Grupo.objects.get(id_grupo = id_grupo)
	except Grupo.DoesNotExist:
		messages.add_message(request, messages.ERROR, 'El grupo que intentaste eliminar no existe', extra_tags='alert-danger')
		return redirect(reverse('AMCE:ProfMisGrupos'))
	nombre = str(grupo)
	grupo.delete()
	messages.add_message(request, messages.INFO, 'Grupo ' + nombre + ' eliminado exitosamente', extra_tags='alert-success')
	return redirect(reverse('AMCE:ProfMisGrupos'))

@teacher_required
@login_required
def ProfPaginaGrupo(request, id_grupo):
	user = get_object_or_404(User, pk=request.user.pk)
	grupo = Grupo.objects.get(id_grupo=id_grupo)
	equipos = Equipo.objects.filter(grupo_equipo=id_grupo)
	equipos = equipos[::-1]
	temas = []
	# Obtenemos todos los temas asignados a los equipos del grupo
	for e in equipos:
		for t in e.temas_asignados.all():
			if not t in temas:
				temas.append(t)
	map = { 'id_grupo': id_grupo,
			'grupo':grupo,
			'equipos':equipos,
			'temas':temas,
			'current_user':user,
			# variable para saber qué pestaña poner activa cuando se carga el template
			'redirect': True if request.GET.get('redirect') else False
		  }
	return render(request, 'profesor/PaginaGrupo.html', map)

@teacher_required
@login_required
def ProfCrearEquipo(request, id_grupo):
	user = get_object_or_404(User, pk=request.user.pk)
	grupo = Grupo.objects.get(id_grupo=id_grupo)
	if request.method == 'POST':
		form = FormCrearEquipo(request.POST)
		if form.is_valid():
			nuevo_equipo = Equipo(nombre_equipo=form.cleaned_data['nombre_equipo'],
								   grupo_equipo=grupo)
			nuevo_equipo.save()
			for integrante in form.cleaned_data['integrantes']:
				estudiante = Estudiante.objects.get(user_estudiante=integrante)
				nuevo_equipo.estudiantes.add(estudiante)
			messages.add_message(request, messages.SUCCESS, 'Equipo creado exitosamente', extra_tags='alert-success')
			form = FormCrearEquipo()
			base_url = reverse('AMCE:ProfPaginaGrupo', args=[id_grupo])
			query_string =  urlencode({'redirect':"True"})
			url = '{}?{}'.format(base_url, query_string)
			return redirect(url)
	else:
		form = FormCrearEquipo()
	# En la siguiente línea obtenemos los estudiantes que no tienen un equipo en el grupo y los agregamos a las opciones del form
	# este proceso antes se llevaba a cabo en el init del form pero estaba tirando errores raros, así que mejor hay que dejarlo aquí
	form.fields['integrantes'].queryset = Estudiante.objects.filter(grupos_inscritos__id_grupo=id_grupo).exclude(equipo__grupo_equipo=grupo)
	return render(request, 'profesor/CrearEquipo.html', {'id_grupo':id_grupo,'form': form,'current_user':user})

@teacher_required
@login_required
def ProfEditarEquipo(request, id_grupo,id_equipo):
	"""
		Función para la vista EditarEquipo
		Se encarga de editar el nombre del equipo cuando se manda el formulario
	"""
	try:
		grupo = Grupo.objects.get(id_grupo = id_grupo)
	except Grupo.DoesNotExist:
		messages.add_message(request, messages.ERROR, 'El grupo  no existe', extra_tags='alert-danger')
		return redirect(reverse('AMCE:ProfMisGrupos'))
	try:
		equipo = Equipo.objects.get(id_equipo = id_equipo)
	except Equipo.DoesNotExist:
		messages.add_message(request, messages.ERROR, 'El equipo no existe', extra_tags='alert-danger')
		return redirect(reverse('AMCE:ProfMisGrupos'))
	if request.method == 'POST':
		form = FormEditarEquipo(request.POST)
		if form.is_valid():
			nombre_equipo = form.cleaned_data['nombre_equipo']
			record = Equipo.objects.get(id_equipo=id_equipo)
			record.nombre_equipo = str(nombre_equipo)
			record.save()
			messages.add_message(request, messages.INFO, 'Grupo editado exitosamente', extra_tags='alert-success')
			return redirect(reverse('AMCE:ProfMisGrupos'))
	else:
		form = FormEditarEquipo()
		form.fields['nombre_equipo'].initial = equipo.nombre_equipo
	return render(request, 'profesor/EditarEquipo.html', {'form': form, 'id_grupo': id_grupo, 'id_equipo': id_equipo})

@teacher_required
@login_required
def ProfEliminaEquipo(request, id_grupo, id_equipo):
	"""
		Funcion que elimina un Equipo
	"""
	try:
		grupo = Grupo.objects.get(id_grupo = id_grupo)
	except Grupo.DoesNotExist:
		messages.add_message(request, messages.ERROR, 'El grupo  no existe', extra_tags='alert-danger')
		return redirect(reverse('AMCE:ProfMisGrupos'))
	try:
		equipo = Equipo.objects.get(id_equipo = id_equipo)
	except Equipo.DoesNotExist:
		messages.add_message(request, messages.ERROR, 'El equipo no existe', extra_tags='alert-danger')
		return redirect(reverse('AMCE:ProfMisGrupos'))
	Equipo.objects.get(id_equipo=id_equipo).delete()
	messages.add_message(request, messages.SUCCESS, 'Equipo eliminado exitosamente', extra_tags='alert-success')
	return redirect(reverse('AMCE:ProfPaginaGrupo', args=[id_grupo]))

@teacher_required
@login_required
def ProfPaginaEquipo(request, id_grupo, id_equipo):
	user = get_object_or_404(User, pk=request.user.pk)
	equipo = Equipo.objects.get(id_equipo=id_equipo)
	print(equipo)
	estudiantes = equipo.estudiantes.all()
	print(estudiantes)
	estudiantes_nombres = []
	for e in estudiantes:
		estudiantes_nombres.append(str(e))
	return render(request, 'profesor/PaginaEquipo.html', {'equipo_nombre':equipo.nombre_equipo, 'estudiantes_nombres':estudiantes_nombres,'current_user':user})

@teacher_required
@login_required
def ProfAsignarTemaGrupo(request, id_grupo):
	user = get_object_or_404(User, pk=request.user.pk)
	grupo = Grupo.objects.get(id_grupo=id_grupo)
	if request.method == 'POST':
		form = AsignarTemaGrupo(request.POST)
		if form.is_valid():
			tema = form.cleaned_data['tema']
			for equipo in form.cleaned_data['equipos']:
				try:
					definir_problema = DefinirProblema.objects.get(equipo_definirProb=equipo, tema_definirProb=tema)
				except DefinirProblema.DoesNotExist:
					equipo.temas_asignados.add(tema)
					definir_problema = DefinirProblema(equipo_definirProb=equipo, tema_definirProb=tema)
					definir_problema.preguntas_secundarias = form.cleaned_data['preguntas_secundarias']
					definir_problema.fuentes = form.cleaned_data['fuentes']
					definir_problema.entregable = form.cleaned_data['entregable']
					definir_problema.save()
			messages.add_message(request, messages.SUCCESS, 'Tema asignado exitosamente', extra_tags='alert-success')
			form = AsignarTemaGrupo()
			return redirect(reverse('AMCE:ProfPaginaGrupo', args=[id_grupo]))
	else:
		form = AsignarTemaGrupo()
	equipos = Equipo.objects.filter(grupo_equipo=id_grupo).annotate(temas_count=Count('temas_asignados')).filter(temas_count=0)
	
	if not equipos.exists():
		messages.add_message(request, messages.ERROR, 'Todos los equipos existentes ya tienen temas asignados.', extra_tags='alert-danger')
		return redirect(reverse('AMCE:ProfPaginaGrupo', args=[id_grupo]))
	form.fields['equipos'].queryset = equipos
	form.fields['tema'].queryset = Tema.objects.filter(profesor_tema=user.id)
	return render(request, 'profesor/AsignarTemaGrupo.html', {'id_grupo':id_grupo,'form': form,'current_user':user})

@teacher_required
@login_required
def ProfTemaAsignado(request, id_grupo, id_tema):
	current_user = get_object_or_404(User, pk=request.user.pk)
	tema = Tema.objects.filter(id_tema=id_tema)
	grupo = Grupo.objects.filter(id_grupo=id_grupo)
	equipos = Equipo.objects.filter(grupo_equipo=id_grupo,temas_asignados__id_tema=id_tema)

	for e in equipos:
		id_e = e.id_equipo
		definirProb = DefinirProblema.objects.get(equipo_definirProb=id_e, tema_definirProb=id_tema)
		e.paso = definirProb.paso

	return render(request, 'profesor/TemaAsignado.html', {'grupo':grupo[0], 'tema':tema[0], 'equipos':equipos,'current_user':current_user})


@teacher_required
@login_required
def ProfMisTemas(request):
	#Se muestran los Temas asignados al ID del usuario actual
	user = get_object_or_404(User, pk=request.user.pk)
	temas = Tema.objects.filter(profesor_tema=user.pk)
	temas = temas[::-1]
	return render(request,"profesor/MisTemas.html", {'temas':temas,'current_user':user})

@teacher_required
@login_required
def ProfCrearTema(request):
	user = get_object_or_404(User, pk=request.user.pk)
	profesor = Profesor.objects.get(user_profesor=user.pk)
	temas = Tema.objects.filter(profesor_tema=request.user.pk)
	if request.method == 'POST':
		form = FormTema(request.POST)
		if form.is_valid():
			nuevo_tema = Tema(nombre_tema=form.cleaned_data['nombre_tema'],
								profesor_tema=profesor)
			nuevo_tema.save()
			messages.add_message(request, messages.SUCCESS, 'Tema creado correctamente', extra_tags='alert-success')
			form = FormTema()
			return redirect(reverse('AMCE:ProfMisTemas'))
	else:
		form = FormTema()
	return render(request, 'profesor/CrearTema.html', {'form': form,'current_user':user})

#EDITAR TEMA
@teacher_required
@login_required
def ProfEditarTema(request, id_tema):
	"""
		Enpoint para editar un tema
	"""
	try:
		tema = Tema.objects.get(id_tema = id_tema)
	except  tema.DoesNotExist:
		messages.add_message(request, messages.ERROR, 'El tema no existe', extra_tags='alert-danger')
		return redirect(reverse('AMCE:ProfMisTemas'))
	if request.method == 'POST':
		form = FormTema(request.POST, instance=tema)
		if form.is_valid():
			tema.nombre_tema = form.cleaned_data['nombre_tema']
			tema.save()
			messages.add_message(request, messages.INFO, 'Tema editado exitosamente', extra_tags='alert-success')
			return redirect(reverse('AMCE:ProfMisTemas'))
	else:
		form = FormTema(instance=tema)
	return render(request, 'profesor/EditarTema.html', {'form': form, 'id_tema': id_tema})

#ELIMINAR TEMA
@teacher_required
@login_required
def ProfEliminarTema(request, id_tema):
	"""
		Función para eliminar un grupo
	"""
	try:
		tema= Tema.objects.get(id_tema= id_tema)
	except Tema.DoesNotExist:
		messages.add_message(request, messages.ERROR, 'El tema que intentaste eliminar no existe', extra_tags='alert-danger')
		return redirect(reverse('AMCE:ProfMisTemas'))
	nombre_tema = str(tema)
	tema.delete()
	messages.add_message(request, messages.INFO, 'Grupo ' + nombre_tema + ' eliminado exitosamente', extra_tags='alert-success')
	return redirect(reverse('AMCE:ProfMisTemas'))

@teacher_required
@login_required
def ProfProgresoEquipo(request, id_grupo, id_tema, id_equipo):
	user = get_object_or_404(User, pk=request.user.pk)
	
	equipo = Equipo.objects.get(id_equipo=id_equipo)
	tema = Tema.objects.get(id_tema=id_tema)
	definirProb = DefinirProblema.objects.get(equipo_definirProb=id_equipo, tema_definirProb=id_tema)
	paso = definirProb.paso

	"""
		RETROS.
	"""
	retros = [[]]
	retros.append(definirProb.retro1)
	retros.append(definirProb.retro2)
	retros.append(definirProb.retro3)
	retros.append(definirProb.retro4)
	retros.append(definirProb.retro5)
	retros.append(definirProb.retro6)

	"""
		PASO 1.
	"""
	if paso >= 1:
		preguntas = Pregunta.objects.filter(definirProb_pregunta=definirProb.id_definirProb)
		inicial = preguntas.filter(tipo_pregunta=1,ganadora=True)
		secundarias = preguntas.filter(tipo_pregunta=2,ganadora=True)
		print("segundarias: ",secundarias)
		#Todo esta en orden con el paso 1.

	"""
		PASO 2.
	"""
	fuentes = None
	if paso >= 2:
		fuentes = Fuente.objects.filter(id_defproblema=definirProb.id_definirProb,ganadora=1)
		dict = {
			'0': 'LIBRO',
			'1': 'REVISTA',
			'2': 'PERIODICO',
			'3': 'SITIO WEB',
			'4': 'VIDEO',
			'5': 'IMAGEN'
		}
		if fuentes.exists(): #si existe la fuente que fue votada
			for f in fuentes:
				print(f.tipo_fuente)
				f.tipo_fuente = dict[f.tipo_fuente]

	"""
		PASO 3.
	"""
	analisis_info = None
	paso_finalizado_3 = None
	if paso >= 4: #Se pone el 4 porque esto asegura que se ha ter,inado el paso
		analisis_info = []
		try:
			# Apartado: Pregunta
			preguntas = Pregunta.objects.filter(definirProb_pregunta=definirProb.id_definirProb)
			preguntas = preguntas.filter(tipo_pregunta=2)
			
			respuestas_tipo1 = Respuesta.objects.filter(tipo=1,definirProb=definirProb.id_definirProb)

			# Apartado: Fuente
			fnts = respuestas_tipo1
			

			# Apartado: Referencia de la fuente
			ref_fuente = respuestas_tipo1
			
			# Apartado: Respuesta de la fuente
			resp_fuente = respuestas_tipo1

			# Apartado: Sintesis
			respuestas_tipo2 = Respuesta.objects.filter(tipo=2,definirProb=definirProb.id_definirProb)
			sintesis_todas = respuestas_tipo2


			for prgnta, f, ref_f, resp_f, sntss in zip(preguntas, fnts, ref_fuente, resp_fuente, sintesis_todas):
				pregunta = prgnta.id_pregunta.contenido
				fuente = f.fuente.enlace
				referencia = ref_f.referencia
				respuesta = resp_f.id_respuesta.contenido
				sintesis = sntss.id_respuesta.contenido

				analisis_info.append([pregunta, fuente, referencia, respuesta, sintesis])
			paso_finalizado_3 = 'ok'
		except:
			print("Error en paso 3. Analisis Informacion")

	"""
		MAP.
	"""
	map = { 'id_grupo': id_grupo,
			'id_tema': id_tema,
			'tema': tema,
			'equipo': equipo,
			'paso': paso,
			'pasos': [None, inicial, secundarias],
			'retros': retros,
			'fuentes': fuentes,
			'current_user':user

		  }
	map['analisis_info'] = analisis_info
	map['paso_finalizado_3'] = paso_finalizado_3

	"""
		PASO 4.
	"""
	paso_finalizado_4 = None
	if paso >= 4:
		if definirProb.trabajo_final is not None:
			contenido = definirProb.trabajo_final.contenido
			map['contenido'] = contenido
			paso_finalizado_4 = 'ok'

	map['paso_finalizado_4'] = paso_finalizado_4
	
	return render(request, 'profesor/ProgresoEquipo.html', map)






@teacher_required
@login_required
def ProfProgresoGrupo(request, id_grupo, id_tema):
	user = get_object_or_404(User, pk=request.user.pk)
	grupo = Grupo.objects.get(id_grupo=id_grupo)
	tema = Tema.objects.get(id_tema=id_tema)
	equipos = Equipo.objects.filter(grupo_equipo=id_grupo,temas_asignados__id_tema=id_tema)
	equipo_paso_map = []
	for e in equipos:
		paso = 1
		definirProb = DefinirProblema.objects.get(equipo_definirProb=e.id_equipo, tema_definirProb=id_tema)
		if definirProb.pregunta_set.filter(tipo_pregunta=1,ganadora=True):
			paso = 2
		equipo_paso_map.append({'equipo':e,'paso':paso})
	map = { 'id_grupo': id_grupo,
			'id_tema': id_tema,
			'tema': tema,
			'grupo': grupo,
			'equipo_paso_map': equipo_paso_map
		  }
	return render(request, 'profesor/ProgresoGrupo.html', map)

@teacher_required
@login_required
def ProfRetro(request, id_grupo, id_tema, id_equipo, paso):
	user = get_object_or_404(User, pk=request.user.pk)
	tema = Tema.objects.get(id_tema=id_tema)
	equipo = Equipo.objects.get(id_equipo=id_equipo)
	if request.method == 'POST':
		form = FormRetro(request.POST)
		if form.is_valid():
			definirProb = DefinirProblema.objects.get(equipo_definirProb=id_equipo, tema_definirProb=id_tema)
			if paso == 1:
				definirProb.retro1 = form.cleaned_data['retro']
			elif paso == 2:
				definirProb.retro2 = form.cleaned_data['retro']
			elif paso == 3:
				definirProb.retro3 = form.cleaned_data['retro']
			elif paso == 4:
				definirProb.retro4 = form.cleaned_data['retro']
			elif paso == 5:
				definirProb.retro5 = form.cleaned_data['retro']
			elif paso == 6:
				definirProb.retro6 = form.cleaned_data['retro']
			definirProb.save()
			messages.add_message(request, messages.SUCCESS, 'Retroalimentación enviada correctamente', extra_tags='alert-success')
			form = FormRetro()
			return redirect(reverse('AMCE:ProfProgresoEquipo', kwargs={'id_grupo':id_grupo, 'id_tema':id_tema, 'id_equipo':id_equipo}))
	else:
		form = FormRetro()
		definirProb = DefinirProblema.objects.get(equipo_definirProb=id_equipo, tema_definirProb=id_tema)
		preguntas = Pregunta.objects.filter(definirProb_pregunta=definirProb.id_definirProb)
		if paso == 1:
			paso_ctxt = preguntas.filter(tipo_pregunta=1,ganadora=True)
		elif paso == 2:
			paso_ctxt = preguntas.filter(tipo_pregunta=2,ganadora=True)
		elif paso == 3:
			paso_ctxt = ""
		elif paso == 4:
			paso_ctxt = ""
		elif paso == 5:
			paso_ctxt = ""
		elif paso == 6:
			paso_ctxt = None
	map = { 'form': form,
			'id_grupo': id_grupo,
			'id_tema': id_tema,
			'tema': tema,
			'equipo': equipo,
			'paso': paso,
			'paso_ctxt': paso_ctxt,
			'current_user':user
		  }
	
	
	definirProb = DefinirProblema.objects.get(equipo_definirProb=id_equipo, tema_definirProb=id_tema)
	paso = definirProb.paso
	fuentes = None
	if paso >= 2:
		fuentes = Fuente.objects.filter(id_defproblema=definirProb.id_definirProb,ganadora=1)
		dict = {
			'0': 'LIBRO',
			'1': 'REVISTA',
			'2': 'PERIODICO',
			'3': 'SITIO WEB',
			'4': 'VIDEO',
			'5': 'IMAGEN'
		}
		if fuentes.exists(): #si existe la fuente que fue votada
			for f in fuentes:
				print(f.tipo_fuente)
				f.tipo_fuente = dict[f.tipo_fuente]
	map['fuentes'] = fuentes

	return render(request, 'profesor/Retroalimentacion.html', map)

#Función para generar el id de un Grupo cuando se crea
def random_string(char_num): 
	letter_count = random.randint(1, char_num-2)
	digit_count = char_num - letter_count
	str1 = ''.join((random.choice(string.ascii_lowercase) for x in range(letter_count)))  
	str1 += ''.join((random.choice(string.digits) for x in range(digit_count)))  

	sam_list = list(str1) # it converts the string to list.  
	random.shuffle(sam_list) # It uses a random.shuffle() function to shuffle the string.  
	final_string = ''.join(sam_list)  
	return final_string
	