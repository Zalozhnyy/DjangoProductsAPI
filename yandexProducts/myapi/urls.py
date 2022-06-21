from django.urls import path


from . import views

urlpatterns = [
    path('imports', views.ItemAPIView.as_view()),
    path('nodes/<str:id>', views.ItemAPIView.as_view()),

    path('delete/<str:id>', views.ItemDeleteAPIView.as_view()),

    path('sales', views.ItemSalesView.as_view()),

    path('node/<str:id>/statistic', views.ItemStatisticView.as_view()),
]
