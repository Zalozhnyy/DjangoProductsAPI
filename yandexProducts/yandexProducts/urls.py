from django.urls import include, path

urlpatterns = [
    path('', include('myapi.urls'))
]
