'''
se importa signals que ayuda a crear acciones después de haber registrado un usuario, en este caso cada que alguién inicia sesión se crea un perfil de ese usuario
'''
'''
from django.db.models.signals import post_save
#se importan el modelo Usuario que viene por defecto en Django
from django.contrib.auth.models import User
from .models import Profile
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_profile(sender, instance, created,**kwargs):
	if created:
		Profile.objects.create(user=instance)

post_save.connect(create_profile, sender=User)
'''