from django.contrib import admin
from django.contrib import auth
from .models import User, Profesor, Estudiante, Grupo, Equipo, Tema, Pregunta, ComentariosPreguntaInicial, ParticipacionEst, DefinirProblema
from django.contrib.auth.admin import UserAdmin


class testUserAdmin(UserAdmin):
    """
    Clase administradorda de modelo: Usuario
    """


    """
    Campos que se muestran en el listado de usuario
    """
    list_display = (
        'username',
        'full_name',
        'email',
        'es_estudiante',
        'es_profesor',
        'is_active'
    )

    """
    Campos disponibles en el administrador
    *Los campos comentados no son necesarios
    """
    fieldsets = (
        (("Inicio de sesión"), {"fields": ("username", "password")}),
        (("Información personal"), {"fields": ("first_name", "last_name", "email")}),
        (
            ("Permisos"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                ),
            },
        )
    )

    """
    Campos que se mostraran al crear un usuario, no aparecera ya que esta deshabilitada
    la opcion de creacion
    """
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "password1", "password2"),
            },
        ),
    )

    def has_add_permission(self, request):
        """
        Deshabilita la opcion para crear un usuario
        """
        return False


    def full_name(self, obj):
        "Nombre completo para columna en listado de usuarios"
        return obj.last_name + ' ' +  obj.first_name

    full_name.admin_order_field  = 'Nombre Completo'  #Allows column order sorting
    full_name.short_description = 'Nombre Completo'  #Renames column head


class GrupoAdmin(admin.ModelAdmin):
    """
    Clase administradorda de modelo: Grupo
    """

    list_display = (
        'id_grupo',
        'nombre_grupo',
        'materia',
        'institucion',
        'profesor_grupo',
    )


class EquipoAdmin(admin.ModelAdmin):
    """
    Clase administradorda de modelo: Equipo
    """

    list_display = (
        'id_equipo',
        'nombre_equipo',
        'codigo_equipo'
    )

    def has_add_permission(self, request):
        """
        Deshabilita la opcion para crear un Equipo
        """
        return False

    def codigo_equipo(self, obj):
        return obj.grupo_equipo.id_grupo

    codigo_equipo.admin_order_field  = 'Código de equipo'  #Allows column order sorting
    codigo_equipo.short_description = 'Código de equipo'  #Renames column head

class TemaAdmin(admin.ModelAdmin):
    """
    Clase administradorda de modelo: Tema
    """

    list_display = (
        'ID',
        'nombre_tema',
        'owner'
    )

    def ID(self, obj):
        "Identificador para tema"
        return obj.id_tema

    ID.admin_order_field  = 'Identificador único'  #Allows column order sorting
    ID.short_description = 'Identificador único'  #Renames column head

    def owner(self, obj):
        "profesor propietario"
        return obj.profesor_tema

    owner.admin_order_field  = 'Profesor propietario'  #Allows column order sorting
    owner.short_description = 'Profesor propietario'  #Renames column head

class PreguntaAdmin(admin.ModelAdmin):

    list_display = (
        'id_pregunta',
        'tipo_pregunta',
        'votos', 
        'ganadora',
    )
class ParticipacionEstAdmin(admin.ModelAdmin):

    list_display = (
        'fecha',
        'short_content', 
        'student_owner',
    )

    def has_add_permission(self, request):
        """
        Deshabilita la opcion para crear una participación
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        Deshabilita la opcion para crear una participación
        """
        return False

    def short_content(self, obj):
        "Corta el contenido de una participación"
        return obj.contenido[0:40] + '...' if len(obj.contenido) > 40 else obj.contenido

    short_content.admin_order_field  = 'Contenido'  #Allows column order sorting
    short_content.short_description = 'Contenido'  #Renames column head

    def student_owner(self, obj):
        "Propietario de la participación"
        return obj.estudiante_part

    student_owner.admin_order_field  = 'Alumno que realizó la participación'  #Allows column order sorting
    student_owner.short_description = 'Alumno que realizó la participación'  #Renames column head


class ComentariosPreguntaInicialAdmin(admin.ModelAdmin):

    list_display = (
        'participacionEst',
        'pregunta',
    )

class DefinirProblemaAdmin(admin.ModelAdmin):

    list_display = (
        'assigned_team',
        'assigned_topic',
        'paso',
        'preguntas_secundarias',
        'fuentes',
    )

    def assigned_team(self, obj):
        "Propietario de la participación"
        return obj.equipo_definirProb

    assigned_team.admin_order_field  = 'Equipo asignado'  #Allows column order sorting
    assigned_team.short_description = 'Equipo asignado'  #Renames column head

    def assigned_topic(self, obj):
        "Propietario de la participación"
        return obj.tema_definirProb

    assigned_topic.admin_order_field  = 'Tema asignado'  #Allows column order sorting
    assigned_topic.short_description = 'Tema asignado'  #Renames column head

    def has_delete_permission(self, request, obj=None):
        """
        Deshabilita la opcion para crear un problem
        """
        return False

    def get_readonly_fields(self, request, obj=None):
        """
        Deshabilita la edición de los campos en la lista
        """
        if obj:
            return ["assigned_team", "equipo_definirProb", "tema_definirProb", "fuentes"]
        else:
            return []
    
    def has_add_permission(self, request):
        """
        Deshabilita la opcion para crear progresos de equipo
        """
        return False



admin.site.register(User,testUserAdmin)
admin.site.register(Grupo, GrupoAdmin)
admin.site.register(Equipo, EquipoAdmin)
admin.site.register(Tema, TemaAdmin)
admin.site.register(ParticipacionEst, ParticipacionEstAdmin)
#admin.site.register(ComentariosPreguntaInicial, ComentariosPreguntaInicialAdmin)  #se remueve por relación a otros modelos
#admin.site.register(Pregunta, PreguntaAdmin) #se remueve por relación a otros modelos, si se desea implementar tener cuidado con relación a modelo DefinirProblema
admin.site.register(DefinirProblema, DefinirProblemaAdmin)

admin.site.unregister(auth.models.Group) #Se remueven Elementos de Autenticacion y autorización
