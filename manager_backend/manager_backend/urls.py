# manager_backend/urls.py - 
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Version avec préfixe API (recommandée)
    path('api/workflows/', include('workflows.urls')),
    path('api/tasks/', include('tasks.urls')),
    path('api/volunteers/', include('volunteers.urls')),
    
    # Version sans préfixe (pour compatibilité)
    path('workflows/', include('workflows.urls')),
    path('tasks/', include('tasks.urls')),
    path('volunteers/', include('volunteers.urls')),
]