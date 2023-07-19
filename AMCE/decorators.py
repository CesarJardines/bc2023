from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import user_passes_test

def student_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=''):
    '''
    Se comprueba que el usuario que inicie sesión sea estudiante
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.es_estudiante,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def teacher_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=''):
    '''
    Se comprueba que el usuario que inicie sesión sea profesor
    '''
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.es_profesor,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator