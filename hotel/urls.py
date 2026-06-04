from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('news/', views.news_list, name='news_list'),
    path('news/<int:news_id>/', views.news_detail, name='news_detail'),
    path('glossary/', views.glossary, name='glossary'),
    path('contacts/', views.contacts, name='contacts'),
    path('vacancies/', views.vacancies, name='vacancies'),
    path('reviews/', views.reviews, name='reviews'),
    path('promocodes/', views.promocodes, name='promocodes'),
    path('privacy/', views.privacy, name='privacy'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('all-bookings/', views.all_bookings, name='all_bookings'),
    # API endpoints (требуют авторизацию)
    path('api/exchange-rates/', views.api_exchange_rates, name='api_exchange_rates'),
    path('api/weather/', views.api_weather, name='api_weather'),
    # Бронирование
    path('booking/create/', views.booking_create, name='booking_create'),
    path('booking/update/<int:booking_id>/', views.booking_update, name='booking_update'),
    path('booking/delete/<int:booking_id>/', views.booking_delete, name='booking_delete'),
    # Отзывы
    path('review/create/', views.review_create, name='review_create'),
    path('review/delete/<int:review_id>/', views.review_delete, name='review_delete'),
    # CRUD Новости
    path('news/create/', views.news_create, name='news_create'),
    path('news/update/<int:news_id>/', views.news_update, name='news_update'),
    path('news/delete/<int:news_id>/', views.news_delete, name='news_delete'),
    # CRUD Вакансии
    path('vacancies/create/', views.vacancy_create, name='vacancy_create'),
    path('vacancies/update/<int:vacancy_id>/', views.vacancy_update, name='vacancy_update'),
    path('vacancies/delete/<int:vacancy_id>/', views.vacancy_delete, name='vacancy_delete'),
    # CRUD Сотрудники
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/update/<int:employee_id>/', views.employee_update, name='employee_update'),
    path('employees/delete/<int:employee_id>/', views.employee_delete, name='employee_delete'),
    # CRUD Промокоды
    path('promocodes/create/', views.promocode_create, name='promocode_create'),
    path('promocodes/update/<int:promocode_id>/', views.promocode_update, name='promocode_update'),
    path('promocodes/delete/<int:promocode_id>/', views.promocode_delete, name='promocode_delete'),
    # CRUD Термины
    path('terms/create/', views.term_create, name='term_create'),
    path('terms/update/<int:term_id>/', views.term_update, name='term_update'),
    path('terms/delete/<int:term_id>/', views.term_delete, name='term_delete'),
]
