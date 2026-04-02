from django.contrib.auth.views import LoginView, LogoutView


class POSLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True


class POSLogoutView(LogoutView):
    pass

# Create your views here.
