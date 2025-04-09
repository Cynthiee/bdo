from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from bdounibank.views import landing_page_view


urlpatterns = [
    path('admin/', admin.site.urls),
    path("__reload__/", include("django_browser_reload.urls")),
    path('', landing_page_view, name='landing_page'),
    path('banking/', include('bdounibank.urls')),
    path('dashboard/', include('accounts.urls')),
    path('transactions/', include('transactions.urls')),
    path('loans/', include('loans.urls')),
    path('admin-portal/', include('admin_portal.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

