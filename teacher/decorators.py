from django.contrib import messages
from django.shortcuts import redirect


def teacher_authenticate(view_func):
    def wrapper(request, *args, **kwargs):
        if 'teacher_id' not in request.session:
            messages.error(request, 'Please log in to your teacher account to access this page.')
            return redirect('Teacher_login')
        return view_func(request, *args, **kwargs)

    return wrapper
