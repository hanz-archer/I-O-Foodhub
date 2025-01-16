def super_admin_context(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return {'super_admin': request.user}
    return {'super_admin': None}
