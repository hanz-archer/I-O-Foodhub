from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.contrib import messages

def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # First check if user is authenticated
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
        
        # Then check if user is superuser
        if not request.user.is_superuser:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('index')
        
        # If both checks pass, allow access to the view
        return view_func(request, *args, **kwargs)
    return _wrapped_view



def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check both admin_id and is_admin flag
        admin_id = request.session.get('admin_id')
        is_admin = request.session.get('is_admin')
        
        if not admin_id or not is_admin:
            # Clear any invalid session data
            request.session.flush()
            messages.error(request, 'Please log in as admin to access this page.')
            return redirect('login')
        
        # If both checks pass, allow access to the view
        return view_func(request, *args, **kwargs)
    return _wrapped_view



def employee_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_employee'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
