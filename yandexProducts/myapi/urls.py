from django.urls import path
from django.views.decorators.csrf import csrf_exempt


from . import views

urlpatterns = [
    path('imports', views.import_view),
    path('delete/<str:id>', views.delete_view),
    path('nodes/<str:id>', views.nodes_view),
]
