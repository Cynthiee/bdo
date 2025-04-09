from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path("__reload__/", include("django_browser_reload.urls")),
    path('', include('accounts.urls')),
    path("bdounibank/", include("bdounibank.urls")),
    path('transactions/', include('transactions.urls')),
    path('loans/', include('loans.urls')),
    path('admin-portal/', include('admin_portal.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)