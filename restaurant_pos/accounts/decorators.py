from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def role_required(allowed_roles):
    def check_role(user):
        if user.is_authenticated and (user.role in allowed_roles or user.is_superuser):
            return True
        raise PermissionDenied
    return user_passes_test(check_role)

def admin_required(view_func):
    return role_required(['admin'])(view_func)

def chef_required(view_func):
    return role_required(['chef'])(view_func)

def customer_required(view_func):
    return role_required(['customer'])(view_func)

def staff_required(view_func):
    return role_required(['admin', 'cashier', 'captain', 'chef', 'waiter'])(view_func)

def pos_required(view_func):
    return role_required(['admin', 'cashier', 'captain', 'waiter'])(view_func)

