from django.db import models
#se importan el modelo Usuario que viene por defecto en Django
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
#se importa la zona horaria 
from django.utils import timezone 

class User(AbstractUser): #agregar y eliminar (analizar)
	es_estudiante = models.BooleanField(default=False)
	es_profesor = models.BooleanField(default=False)

	def __str__(self):
		return '{} {}'.format(self.last_name, self.first_name)

class Profesor(models.Model):
	user_profesor = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

	class Meta:
		verbose_name = 'Profesor'
		verbose_name_plural = "Profesores"
		
	def __str__(self):
		return '{} {}'.format(self.user_profesor.last_name, self.user_profesor.first_name)

class Grupo(models.Model):  #agregar y eliminar
	id_grupo = models.CharField(max_length=10, primary_key=True, help_text="Código para inscripción a este grupo", unique=True)
	nombre_grupo = models.CharField(max_length=100, help_text="Nombre del grupo")
	materia = models.CharField(max_length=100, null=True, blank=True, help_text="Nombre de la materia a la que pertenece este grupo")
	institucion = models.CharField(max_length=100, null=True, blank=True, help_text="Nombre de la institución a la que pertenece este grupo")

	profesor_grupo = models.ForeignKey(Profesor, on_delete=models.CASCADE, help_text="Profesor encargado este grupo")

	def __str__(self):
		return f'{self.nombre_grupo} / {self.materia} / {self.institucion}'
	
	class Meta:
		verbose_name = 'Grupo'
		verbose_name_plural = "Grupos"

class Estudiante(models.Model):
	user_estudiante = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
	grupos_inscritos = models.ManyToManyField(Grupo, blank=True)

	def __str__(self):
		user = User.objects.get(id=self.user_estudiante.id)
		return '{} {}'.format(user.last_name, user.first_name)
	
	def __eq__(self, __o: object) -> bool:
		return supe
class Tema(models.Model):
	id_tema = models.AutoField(primary_key=True, help_text="Indetificador único del Tema")
	nombre_tema = models.CharField(max_length=100, help_text="Título del Tema")

	profesor_tema = models.ForeignKey(Profesor, on_delete=models.CASCADE, help_text="Profesor propietario del Tema")

	def __str__(self):
		return '{}'.format(self.nombre_tema)

class Equipo(models.Model):  #agregar y eliminar
	id_equipo = models.AutoField(primary_key=True)
	nombre_equipo = models.CharField(max_length=100, help_text="Nombre del Equipo")

	grupo_equipo = models.ForeignKey(Grupo, on_delete=models.CASCADE, help_text="Grupo al que pertenece el equipo")
	estudiantes = models.ManyToManyField(Estudiante, blank=True, help_text="Integrantes del Equipo")
	temas_asignados = models.ManyToManyField(Tema, blank=True, help_text="Tema asignado al Equipo")

	class Meta:
		"""
		Establece nombres singulares y plurales
		"""
		verbose_name = 'Equipo'
		verbose_name_plural = "Equipo"

	def __str__(self):
		return '{}'.format(self.nombre_equipo)
		
class ParticipacionEst(models.Model):
	id_actividad = models.AutoField(primary_key=True)
	fecha = models.DateTimeField(default = timezone.now, help_text="Fecha en que se realizó la participación")
	contenido = models.TextField(null=True, help_text="Contenido de la participación")
	estudiante_part = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='post', help_text="Estudiante que realizó la participación")

	class Meta:
		verbose_name = 'Participación'
		verbose_name_plural = "Participaciones"

	def __str__(self):
		return self.contenido[0:40] + '...' if len(self.contenido) > 40 else self.contenido


class DefinirProblema(models.Model):

	TIPO_ENTREGABLE = (
        ('0', 'Infografía'),
        ('1', 'Mapa conceptual'),
        ('2', 'Mapa mental'),
        ('3', 'Presentación'),
        ('4', 'Video'),
    )

	id_definirProb = models.AutoField(primary_key=True)
	preguntas_secundarias = models.IntegerField(default=1,  help_text="Número de preguntas secundarias")
	fuentes = models.IntegerField(default=1, help_text="Número de fuentes a seleccionar")
	paso = models.IntegerField(default=1, help_text="Paso en que se encuentra el progreso del equipo para este Problema")
	entregable = models.CharField(default='0', help_text="Tipo de Entregable'", max_length=1, choices=TIPO_ENTREGABLE)
	retro1 = models.TextField(null=True, help_text="Información de primera retrospectiva")
	retro2 = models.TextField(null=True, help_text="Información de segunda retrospectiva")
	retro3 = models.TextField(null=True, help_text="Información de tercera retrospectiva")
	retro4 = models.TextField(null=True, help_text="Información de cuarta retrospectiva")
	retro5 = models.TextField(null=True, help_text="Información de quinta retrospectiva")
	retro6 = models.TextField(null=True, help_text="Información de sexta retrospectiva")

	equipo_definirProb = models.ForeignKey(Equipo, on_delete=models.CASCADE, help_text="Equipo al que pertenece el Problema")
	tema_definirProb = models.ForeignKey(Tema, on_delete=models.CASCADE, help_text="Tema del Problema")
	trabajo_final=models.ForeignKey(ParticipacionEst, null=True, on_delete=models.CASCADE, help_text="Trabajo final del equipo")
	
	class Meta:
		verbose_name = 'Progreso de equipo'
		verbose_name_plural = "Progreso de equipos"
	
	def __str__(self):
		return ""



class Pregunta(models.Model):  #agregar y eliminar
	id_pregunta = models.OneToOneField(ParticipacionEst, on_delete=models.CASCADE, primary_key=True, help_text="Referencia a pregunta")
	INICIAL = 1
	SECUNDARIA = 2
	OTRO = 10
	TIPOS_PREGUNTA = (
		(INICIAL, 'inicial'),
		(SECUNDARIA, 'secundaria'),
		(OTRO, 'otro')
	)
	tipo_pregunta = models.PositiveSmallIntegerField(choices=TIPOS_PREGUNTA, default=10, help_text="Tipo de pregunta")
	votos = models.IntegerField(default=0, help_text="Número de votos")
	ganadora = models.BooleanField(default=False, help_text="¿La pregunta es ganadora?")
	
	votadores = models.ManyToManyField(Estudiante, blank=True)
	definirProb_pregunta = models.ForeignKey(DefinirProblema, on_delete=models.CASCADE)

	class Meta:
		verbose_name = 'Pregunta'
		verbose_name_plural = "Preguntas"
	


# class RespuestaPreguntaInicial(models.Model):
# 	id_respuesta_pregunta_inicial = models.AutoField(primary_key=True)
# 	id_participacion_estudiante = models.ForeignKey(ParticipacionEst, on_delete=models.CASCADE, help_text="Participacion que contiene la respuesta del estudiante")
# 	id_pregunta_ganadora= models.ForeignKey(Pregunta, on_delete=models.CASCADE, help_text="Pregunta inicial a la que se responde")
# 	id_defProblema= models.ForeignKey(DefinirProblema, on_delete=models.CASCADE, help_text="Problema al que se responde")


class ComentariosPreguntaInicial(models.Model):  #agregar y eliminar
	participacionEst = models.ForeignKey(ParticipacionEst, on_delete=models.CASCADE,null=True)
	pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE,null=True)

	class Meta:
		"""
		Establece nombres singulares y plurales
		"""
		verbose_name = 'Comentario de pregunta Inicial'
		verbose_name_plural = "Comentarios Iniciales"

	def __str__(self):
		return ""


class EvaPreguntaSecundarias(models.Model):
	estudiante = models.ForeignKey(User,  on_delete=models.CASCADE)
	id_definirProb_pregunta = models.ForeignKey(DefinirProblema, on_delete=models.CASCADE)
	PASO1 = 1
	PASO3 = 3
	PASO4 = 4
	OTRO = 10
	TIPOS_VOTO = (
		(PASO1, 'paso1'),
		(PASO3, 'paso3'),
		(PASO4, 'paso4'),
		(OTRO, 'otro')
	)
	tipo = models.PositiveSmallIntegerField(choices=TIPOS_VOTO, default=10)
	pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, null=True)


class Fuente(models.Model):
	""" Modelo para la tabla fuente """

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

	titulo = models.CharField('Título', max_length=60)
	autor = models.CharField('Autor', max_length=60,null=True)
	fecha_publicacion = models.DateField(null=True)
	lugar = models.CharField('Lugar de Publicación', max_length=60,null=True)
	tipo_fuente = models.CharField('Tipo de Fuente', max_length=1, choices=TIPO_FUENTE_CHOISES)
	tipo_recurso = models.CharField('Tipo de Recurso', max_length=1, choices=TIPO_RECURSO_CHOISES)
	enlace = models.CharField('Enlace', max_length=120)
	id_defproblema = models.ForeignKey(DefinirProblema, on_delete=models.CASCADE,null=True)
	votos = models.IntegerField(default=0)
	ganadora = models.BooleanField(default=False)
	def __str__(self):
		return str(self.titulo) + ' - ' + self.autor

class FuentesSeleccionadas(models.Model):
	id_estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='estudiante')
	id_defproblema = models.ForeignKey(DefinirProblema, on_delete=models.CASCADE, related_name='definirproblema')
	id_fuente = models.ForeignKey(Fuente, on_delete=models.CASCADE, related_name='fuente')

class EvaluacionFuentesSel(models.Model):
	comentario = models.TextField(null=True)
	id_fuente = models.ForeignKey(Fuente, on_delete=models.CASCADE,null=True)
	id_estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name='estudianteEvFuente', null=True)
	id_defproblema = models.ForeignKey(DefinirProblema, on_delete=models.CASCADE, related_name='definirproblemaEvFuente',null=True)

class Respuesta(models.Model):
	id_respuesta = models.OneToOneField(ParticipacionEst, on_delete=models.CASCADE, primary_key=True)
	FUENTE = 1
	SINTETIZADA = 2
	INICIAL = 3
	OTRO = 10
	TIPOS_RESPUESTA = (
		(FUENTE, 'fuente'),
		(SINTETIZADA, 'sintetizada'),
		(INICIAL, 'inicial'),
		(OTRO, 'otro')
	)
	tipo = models.PositiveSmallIntegerField(choices=TIPOS_RESPUESTA, default=10)
	votos = models.IntegerField(default=0)
	ganadora = models.BooleanField(default=False)
	fuente = models.ForeignKey(Fuente, on_delete=models.CASCADE,null=True)
	referencia = models.TextField(null=True)
	pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
	definirProb = models.ForeignKey(DefinirProblema, on_delete=models.CASCADE)

