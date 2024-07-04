from django.contrib import messages
from django.shortcuts import redirect


def student_authenticated(view_func):
    def wrapper(request, *args, **kwargs):
        if 'roll_no' not in request.session:
            messages.error(request, 'Please log in to your student account to access this page.')
            return redirect('Student_login')
        return view_func(request, *args, **kwargs)

    return wrapper
