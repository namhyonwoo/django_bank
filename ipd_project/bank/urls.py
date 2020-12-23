from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),

    path('transfer/', views.transter, name='transfer'),

    path('validateAccount/', views.validateAccount, name='validateAccount'),
    
    path('amount/<account_id>', views.getAmount, name='amount'),

    path('fee/', views.getFee, name='fee'),

]
