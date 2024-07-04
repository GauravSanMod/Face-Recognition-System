from django.contrib import messages
from django.shortcuts import redirect


def AdminDeco(view_func):
    def wrapper(request, *args, **kwargs):
        if 'ID' not in request.session:
            messages.error(request, 'Please log in to your Admin account to access this page.')
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper
