from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..forms import *
from django.contrib.auth import authenticate, login
from django.template import RequestContext
from django.contrib.auth.models import User
from ..models import *
from django.urls import reverse

def index(request):
	if request.method == 'POST':
		form = CustomAuthForm(data=request.POST)
		if form.is_valid():
			user = authenticate(username=form.cleaned_data["username"], password=form.cleaned_data["password"])
			print(user)
			if user is not None:
				login(request,user)
				if user.es_estudiante:
					return redirect('AMCE:vistaAlumno')
				elif user.es_profesor:
					return redirect('AMCE:ProfMisGrupos')
	else:
		form = CustomAuthForm()
	return render(request,'index.html',{"form": form})

def signup(request):
	return render(request,"registration/signup.html")

def password_validation(request):
	return render(request,"registration/test_pass_validation.html")

@login_required#Si el usuario no inició sesińo, entonces se le manda a la vista para iniciar sesión
def custom_404_view(request, exception):
    '''
    Función que devuelve la vista personalizada de error 404
    '''
    #Obtenemos el usuario actual
    usuario = request.user
    #Accedemos a los datos del usuario en la base de datos para poder cargar su nombre en el front
    current_user = get_object_or_404(User, pk=usuario.pk)

	#dependiendo del tipo de usuario mandamos una determinada vista para el error 404
    if usuario.es_estudiante:
        return render(request, 'estudiante/404.html', {'current_user':current_user},status=404)
    elif usuario.es_profesor:
        return render(request, 'profesor/404.html', {'current_user':current_user}, status=404)
    
    #En otro caso el usuario no inició sesión, así que se le manda a la pantalla para iniciar sesión (@loguin_required)

@login_required#Si el usuario no inició sesión, entonces se le manda a la vista para iniciar sesión
def custom_500_view(request):
    '''
    Función que devuelve la vista personalizada de error interno 500
    '''
    #Obtenemos el usuario actual
    usuario = request.user
    #Accedemos a los datos del usuario en la base de datos para poder cargar su nombre en el front
    current_user = get_object_or_404(User, pk=usuario.pk)

	#dependiendo del tipo de usuario mandamos una determinada vista para el error 500
    if usuario.es_estudiante:
        return render(request, 'estudiante/500.html', {'current_user':current_user},status=500)
    elif usuario.es_profesor:
        return render(request, 'profesor/500.html', {'current_user':current_user}, status=500)
    
    #En otro caso el usuario no inició sesión, así que se le manda a la pantalla para iniciar sesión (@loguin_required)


"""
@csrf_exempt
def password_validation(request):
 
    valid = False
    min_strength = settings.PASSWORD_MINIMUM_ENTROPY
 
    if request.method == 'GET':
        password = request.GET["password"]
        results = password_strength(password)
 
        if results['entropy'] > min_strength:
            valid = True
 
        return JsonResponse({
            'valid': valid,
            'min_strength': min_strength,
            'results': results}
            )
"""
	