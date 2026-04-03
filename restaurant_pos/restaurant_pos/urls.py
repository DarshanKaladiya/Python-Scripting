from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("core.urls")),
    path("floor/", include("floor.urls")),
    path("pos/", include("orders.urls")),
    path("kitchen/", include("kitchen.urls")),
    path("customers/", include("customers.urls")),
    path("reports/", include("reporting.urls")),
    path("api/integrations/", include("integrations.urls")),
    path("api/sync/", include("sync.urls")),
]
