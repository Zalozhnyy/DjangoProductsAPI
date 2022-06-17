from django.urls import path


from . import views

urlpatterns = [
    path('imports', views.ItemAPIView.as_view()),
    path('tests', views.ItemAPIView.as_view()),
    # path('delete/<str:id>', views.delete_view),
    path('nodes/<str:id>', views.ItemAPIView.as_view()),
    path('sales', views.sales_view),
    path('node/<str:id>/statistic', views.node_statistic_view),
]
