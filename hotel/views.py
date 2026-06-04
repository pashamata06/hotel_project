from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from .models import News, GlossaryTerm, Employee, Vacancy, Review, PromoCode, Client, Booking, Room, RoomCategory
from datetime import date, datetime, timedelta
from django.utils import timezone
import requests
import logging
import calendar
import pytz
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
from collections import defaultdict
import random
import os
from statistics import mean, median, mode, StatisticsError

logger = logging.getLogger(__name__)

def is_admin(user):
    return user.is_superuser

def is_manager(user):
    return user.is_superuser or (hasattr(user, 'employee') and user.employee.position == 'manager')

def is_admin_only(user):
    return user.is_superuser

def home(request):
    latest_news = News.objects.first()
    
    # API погоды - только для авторизованных
    weather_data = {}
    if request.user.is_authenticated:
        try:
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?q=Minsk&appid=bd5e378503939ddaee76f12ad7a97608&units=metric&lang=ru"
            response = requests.get(weather_url, timeout=5)
            if response.status_code == 200:
                weather_data = response.json()
        except:
            weather_data = {}
    else:
        weather_data = {'error': 'Требуется авторизация'}
    
    now = datetime.now()
    cal = calendar.monthcalendar(now.year, now.month)
    
    chart_base64 = None
    statistics = None
    
    if request.user.is_authenticated and (request.user.is_superuser or (hasattr(request.user, 'employee'))):
        # График загруженности
        months_data = []
        bookings_count = []
        
        for month_num in range(6, 12):
            month_name = ['Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь'][month_num - 6]
            year = 2026
            start_date = date(year, month_num, 1)
            if month_num == 11:
                end_date = date(year, 11, 30)
            else:
                end_date = date(year, month_num + 1, 1) - timedelta(days=1)
            
            count = Booking.objects.filter(
                status='confirmed',
                check_in__lte=end_date,
                check_out__gte=start_date
            ).count()
            
            months_data.append(month_name)
            bookings_count.append(count)
        
        if bookings_count:
            plt.figure(figsize=(12, 6))
            bars = plt.bar(months_data, bookings_count, color=['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6', '#1abc9c'])
            plt.title('Загруженность отеля (июнь - ноябрь 2026)', fontsize=16, fontweight='bold')
            plt.xlabel('Месяц', fontsize=12)
            plt.ylabel('Количество броней', fontsize=12)
            plt.ylim(0, max(bookings_count) + 10 if bookings_count else 50)
            
            for bar, count in zip(bars, bookings_count):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, str(count), ha='center', fontsize=10)
            
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100)
            buf.seek(0)
            chart_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()
        
        # Статистические показатели по броням
        all_bookings = Booking.objects.filter(status='confirmed')
        if all_bookings.exists():
            # Список сумм броней
            booking_amounts = [float(b.total_price) for b in all_bookings]
            
            # Среднее
            avg_amount = mean(booking_amounts)
            
            # Медиана
            median_amount = median(booking_amounts)
            
            # Мода (если есть)
            try:
                mode_amount = mode(booking_amounts)
                mode_str = f"{mode_amount:.2f}"
            except StatisticsError:
                mode_str = "Нет уникальной моды"
            
            # Статистика по месяцам
            stats_by_month = []
            for month_num in range(6, 12):
                month_name = ['Июнь', 'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь'][month_num - 6]
                month_bookings = Booking.objects.filter(
                    status='confirmed',
                    check_in__month=month_num,
                    check_in__year=2026
                )
                if month_bookings.exists():
                    amounts = [float(b.total_price) for b in month_bookings]
                    stats_by_month.append({
                        'month': month_name,
                        'count': month_bookings.count(),
                        'avg': mean(amounts),
                        'total': sum(amounts)
                    })
                else:
                    stats_by_month.append({'month': month_name, 'count': 0, 'avg': 0, 'total': 0})
            
            statistics = {
                'total_bookings': all_bookings.count(),
                'total_revenue': sum(booking_amounts),
                'avg_amount': avg_amount,
                'median_amount': median_amount,
                'mode_amount': mode_str,
                'min_amount': min(booking_amounts),
                'max_amount': max(booking_amounts),
                'by_month': stats_by_month
            }
    
    context = {
        'latest_news': latest_news,
        'weather_data': weather_data,
        'calendar': cal,
        'current_month': now.strftime('%B %Y'),
        'chart_base64': chart_base64,
        'statistics': statistics,
        'is_admin_or_manager': request.user.is_authenticated and (request.user.is_superuser or (hasattr(request.user, 'employee'))),
    }
    return render(request, 'hotel/home.html', context)

def about(request):
    # API курса валют - только для авторизованных
    if request.user.is_authenticated:
        return render(request, 'hotel/about.html', {'exchange_available': True})
    return render(request, 'hotel/about.html', {'exchange_available': False})

def api_exchange_rates(request):
    """API endpoint для курсов валют - только для авторизованных"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD', timeout=5)
        if response.status_code == 200:
            data = response.json()
            usd_to_byn = data['rates']['BYN']
            eur_to_byn = usd_to_byn / data['rates']['EUR']
            rub_to_byn = usd_to_byn / data['rates']['RUB']
            return JsonResponse({
                'USD': round(usd_to_byn, 2),
                'EUR': round(eur_to_byn, 2),
                'RUB': round(rub_to_byn, 2),
                'updated': datetime.now().strftime('%d.%m.%Y %H:%M')
            })
    except:
        pass
    return JsonResponse({'error': 'Service unavailable'}, status=503)

def api_weather(request):
    """API endpoint для погоды - только для авторизованных"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    try:
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q=Minsk&appid=bd5e378503939ddaee76f12ad7a97608&units=metric&lang=ru"
        response = requests.get(weather_url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return JsonResponse({
                'city': data['name'],
                'temp': data['main']['temp'],
                'wind': data['wind']['speed'],
                'description': data['weather'][0]['description']
            })
    except:
        pass
    return JsonResponse({'error': 'Service unavailable'}, status=503)

def news_list(request):
    query = request.GET.get('q', '')
    sort = request.GET.get('sort', '-published_at')
    
    news_list = News.objects.all()
    if query:
        news_list = news_list.filter(title__icontains=query)
    news_list = news_list.order_by(sort)
    
    return render(request, 'hotel/news_list.html', {'news_list': news_list, 'query': query})

def news_detail(request, news_id):
    news = get_object_or_404(News, id=news_id)
    return render(request, 'hotel/news_detail.html', {'news': news})

def glossary(request):
    terms = GlossaryTerm.objects.all()
    return render(request, 'hotel/glossary.html', {'terms': terms})

def contacts(request):
    employees = Employee.objects.all()
    return render(request, 'hotel/contacts.html', {'employees': employees})

def vacancies(request):
    vacancies_list = Vacancy.objects.all()
    return render(request, 'hotel/vacancies.html', {'vacancies_list': vacancies_list})

def reviews(request):
    reviews_list = Review.objects.all()
    return render(request, 'hotel/reviews.html', {'reviews_list': reviews_list})

def promocodes(request):
    promocodes_list = PromoCode.objects.all()
    return render(request, 'hotel/promocodes.html', {'promocodes_list': promocodes_list})

def privacy(request):
    return render(request, 'hotel/privacy.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        if len(username) < 4:
            messages.error(request, 'Логин должен содержать минимум 4 символа')
            return redirect('register')
        
        if len(password) < 4:
            messages.error(request, 'Пароль должен содержать минимум 4 символа')
            return redirect('register')
        
        if password != password2:
            messages.error(request, 'Пароли не совпадают')
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким логином уже существует')
            return redirect('register')
        
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        messages.success(request, 'Регистрация успешна!')
        return redirect('home')
    
    return render(request, 'hotel/register.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Неверный логин или пароль')
    return render(request, 'hotel/login.html')

def user_logout(request):
    logout(request)
    messages.success(request, 'Вы вышли из системы')
    return redirect('home')

@login_required
def profile(request):
    try:
        client = Client.objects.get(user=request.user)
        bookings = Booking.objects.filter(client=client).order_by('-check_in')
    except:
        client = None
        bookings = []
    return render(request, 'hotel/profile.html', {'client': client, 'bookings': bookings})

@login_required
def all_bookings(request):
    if request.user.is_superuser or (hasattr(request.user, 'employee')):
        bookings = Booking.objects.all().order_by('-created_at')
    else:
        try:
            client = Client.objects.get(user=request.user)
            bookings = Booking.objects.filter(client=client).order_by('-created_at')
        except:
            bookings = []
    return render(request, 'hotel/all_bookings.html', {'bookings': bookings, 'is_manager': hasattr(request.user, 'employee')})

@login_required
def booking_create(request):
    rooms = Room.objects.filter(is_available=True)
    
    if request.method == 'POST':
        room_id = request.POST.get('room_id')
        check_in = request.POST.get('check_in')
        check_out = request.POST.get('check_out')
        
        room = get_object_or_404(Room, id=room_id)
        client, created = Client.objects.get_or_create(
            user=request.user,
            defaults={
                'first_name': request.user.first_name or 'Пользователь',
                'last_name': request.user.last_name or request.user.username,
                'phone': '+375 (29) 000-00-00',
                'email': request.user.email or 'user@example.com',
                'birth_date': date(1990, 1, 1)
            }
        )
        
        days = (date.fromisoformat(check_out) - date.fromisoformat(check_in)).days
        total_price = days * room.category.price_per_night
        
        booking = Booking.objects.create(
            client=client,
            room=room,
            check_in=check_in,
            check_out=check_out,
            total_price=total_price,
            status='confirmed'
        )
        
        messages.success(request, f'✅ Оплата прошла успешно! Номер {room.room_number} забронирован. Сумма: {total_price} руб.')
        return redirect('all_bookings')
    
    return render(request, 'hotel/booking_form.html', {'rooms': rooms})

@login_required
@user_passes_test(is_manager)
def booking_update(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        status = request.POST.get('status')
        booking.status = status
        booking.save()
        messages.success(request, 'Статус брони обновлён')
        return redirect('all_bookings')
    return render(request, 'hotel/booking_update.html', {'booking': booking})

@login_required
@user_passes_test(is_manager)
def booking_delete(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if request.method == 'POST':
        booking.delete()
        messages.success(request, 'Бронь удалена')
        return redirect('all_bookings')
    return render(request, 'hotel/booking_confirm_delete.html', {'booking': booking})

@login_required
def review_create(request):
    if request.method == 'POST':
        rating = request.POST.get('rating')
        text = request.POST.get('text')
        
        client, created = Client.objects.get_or_create(
            user=request.user,
            defaults={
                'first_name': request.user.first_name or 'Пользователь',
                'last_name': request.user.last_name or request.user.username,
                'phone': '+375 (29) 000-00-00',
                'email': request.user.email or 'user@example.com',
                'birth_date': date(1990, 1, 1)
            }
        )
        
        Review.objects.create(client=client, rating=rating, text=text)
        messages.success(request, 'Спасибо за ваш отзыв!')
        return redirect('reviews')
    
    return render(request, 'hotel/review_form.html')

@login_required
@user_passes_test(is_manager)
def review_delete(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Отзыв удалён')
        return redirect('reviews')
    return render(request, 'hotel/review_confirm_delete.html', {'review': review})

# ==================== CRUD НОВОСТИ (ТОЛЬКО АДМИН) ====================
@login_required
@user_passes_test(is_admin_only)
def news_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        short_description = request.POST.get('short_description')
        full_text = request.POST.get('full_text')
        image = request.FILES.get('image')
        
        news = News.objects.create(
            title=title,
            short_description=short_description,
            full_text=full_text,
            image=image
        )
        messages.success(request, 'Новость добавлена')
        return redirect('news_list')
    return render(request, 'hotel/news_form.html')

@login_required
@user_passes_test(is_admin_only)
def news_update(request, news_id):
    news = get_object_or_404(News, id=news_id)
    if request.method == 'POST':
        news.title = request.POST.get('title')
        news.short_description = request.POST.get('short_description')
        news.full_text = request.POST.get('full_text')
        if request.FILES.get('image'):
            news.image = request.FILES.get('image')
        news.save()
        messages.success(request, 'Новость обновлена')
        return redirect('news_list')
    return render(request, 'hotel/news_form.html', {'news': news})

@login_required
@user_passes_test(is_admin_only)
def news_delete(request, news_id):
    news = get_object_or_404(News, id=news_id)
    if request.method == 'POST':
        news.delete()
        messages.success(request, 'Новость удалена')
        return redirect('news_list')
    return render(request, 'hotel/news_confirm_delete.html', {'news': news})

# ==================== CRUD ВАКАНСИИ (ТОЛЬКО АДМИН) ====================
@login_required
@user_passes_test(is_admin_only)
def vacancy_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        salary = request.POST.get('salary')
        Vacancy.objects.create(title=title, description=description, salary=salary)
        messages.success(request, 'Вакансия добавлена')
        return redirect('vacancies')
    return render(request, 'hotel/vacancy_form.html')

@login_required
@user_passes_test(is_admin_only)
def vacancy_update(request, vacancy_id):
    vacancy = get_object_or_404(Vacancy, id=vacancy_id)
    if request.method == 'POST':
        vacancy.title = request.POST.get('title')
        vacancy.description = request.POST.get('description')
        vacancy.salary = request.POST.get('salary')
        vacancy.save()
        messages.success(request, 'Вакансия обновлена')
        return redirect('vacancies')
    return render(request, 'hotel/vacancy_form.html', {'vacancy': vacancy})

@login_required
@user_passes_test(is_admin_only)
def vacancy_delete(request, vacancy_id):
    vacancy = get_object_or_404(Vacancy, id=vacancy_id)
    if request.method == 'POST':
        vacancy.delete()
        messages.success(request, 'Вакансия удалена')
        return redirect('vacancies')
    return render(request, 'hotel/vacancy_confirm_delete.html', {'vacancy': vacancy})

# ==================== CRUD СОТРУДНИКИ (ТОЛЬКО АДМИН) ====================
@login_required
@user_passes_test(is_admin_only)
def employee_create(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        position = request.POST.get('position')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        bio = request.POST.get('bio', '')
        photo = request.FILES.get('photo')
        
        Employee.objects.create(
            first_name=first_name,
            last_name=last_name,
            position=position,
            phone=phone,
            email=email,
            bio=bio,
            photo=photo
        )
        messages.success(request, 'Сотрудник добавлен')
        return redirect('contacts')
    return render(request, 'hotel/employee_form.html')

@login_required
@user_passes_test(is_admin_only)
def employee_update(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    if request.method == 'POST':
        employee.first_name = request.POST.get('first_name')
        employee.last_name = request.POST.get('last_name')
        employee.position = request.POST.get('position')
        employee.phone = request.POST.get('phone')
        employee.email = request.POST.get('email')
        employee.bio = request.POST.get('bio', '')
        if request.FILES.get('photo'):
            employee.photo = request.FILES.get('photo')
        employee.save()
        messages.success(request, 'Сотрудник обновлён')
        return redirect('contacts')
    return render(request, 'hotel/employee_form.html', {'employee': employee})

@login_required
@user_passes_test(is_admin_only)
def employee_delete(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Сотрудник удалён')
        return redirect('contacts')
    return render(request, 'hotel/employee_confirm_delete.html', {'employee': employee})

# ==================== CRUD ПРОМОКОДЫ (ТОЛЬКО АДМИН) ====================
@login_required
@user_passes_test(is_admin_only)
def promocode_create(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        discount_percent = request.POST.get('discount_percent')
        is_active = request.POST.get('is_active') == 'on'
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        PromoCode.objects.create(
            code=code,
            discount_percent=discount_percent,
            is_active=is_active,
            start_date=start_date,
            end_date=end_date
        )
        messages.success(request, 'Промокод добавлен')
        return redirect('promocodes')
    return render(request, 'hotel/promocode_form.html')

@login_required
@user_passes_test(is_admin_only)
def promocode_update(request, promocode_id):
    promocode = get_object_or_404(PromoCode, id=promocode_id)
    if request.method == 'POST':
        promocode.code = request.POST.get('code')
        promocode.discount_percent = request.POST.get('discount_percent')
        promocode.is_active = request.POST.get('is_active') == 'on'
        promocode.start_date = request.POST.get('start_date')
        promocode.end_date = request.POST.get('end_date')
        promocode.save()
        messages.success(request, 'Промокод обновлён')
        return redirect('promocodes')
    return render(request, 'hotel/promocode_form.html', {'promocode': promocode})

@login_required
@user_passes_test(is_admin_only)
def promocode_delete(request, promocode_id):
    promocode = get_object_or_404(PromoCode, id=promocode_id)
    if request.method == 'POST':
        promocode.delete()
        messages.success(request, 'Промокод удалён')
        return redirect('promocodes')
    return render(request, 'hotel/promocode_confirm_delete.html', {'promocode': promocode})

# ==================== CRUD ТЕРМИНЫ (ТОЛЬКО АДМИН) ====================
@login_required
@user_passes_test(is_admin_only)
def term_create(request):
    if request.method == 'POST':
        term = request.POST.get('term')
        definition = request.POST.get('definition')
        GlossaryTerm.objects.create(term=term, definition=definition)
        messages.success(request, 'Термин добавлен')
        return redirect('glossary')
    return render(request, 'hotel/term_form.html')

@login_required
@user_passes_test(is_admin_only)
def term_update(request, term_id):
    term = get_object_or_404(GlossaryTerm, id=term_id)
    if request.method == 'POST':
        term.term = request.POST.get('term')
        term.definition = request.POST.get('definition')
        term.save()
        messages.success(request, 'Термин обновлён')
        return redirect('glossary')
    return render(request, 'hotel/term_form.html', {'term': term})

@login_required
@user_passes_test(is_admin_only)
def term_delete(request, term_id):
    term = get_object_or_404(GlossaryTerm, id=term_id)
    if request.method == 'POST':
        term.delete()
        messages.success(request, 'Термин удалён')
        return redirect('glossary')
    return render(request, 'hotel/term_confirm_delete.html', {'term': term})
