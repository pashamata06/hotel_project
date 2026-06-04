import os
import django
from datetime import date, timedelta
import random

def run():
    from django.contrib.auth.models import User
    from hotel.models import RoomCategory, Room, News, Client, Employee, Booking, Review
    
    print('Создание базы данных...')
    
    # Категории
    cat1, _ = RoomCategory.objects.get_or_create(name='Эконом', defaults={'capacity': 2, 'price_per_night': 100})
    cat2, _ = RoomCategory.objects.get_or_create(name='Стандарт', defaults={'capacity': 2, 'price_per_night': 180})
    cat3, _ = RoomCategory.objects.get_or_create(name='Люкс', defaults={'capacity': 4, 'price_per_night': 350})
    
    # Номера
    rooms_data = [('101', cat1), ('102', cat1), ('201', cat2), ('202', cat2), ('301', cat3), ('302', cat3)]
    for num, cat in rooms_data:
        Room.objects.get_or_create(room_number=num, defaults={'category': cat, 'is_available': True})
    
    # Админ
    admin, _ = User.objects.get_or_create(username='admin')
    admin.set_password('admin123')
    admin.is_superuser = True
    admin.is_staff = True
    admin.save()
    
    # Менеджер
    manager, _ = User.objects.get_or_create(username='manager')
    manager.set_password('manager123')
    manager.save()
    Employee.objects.get_or_create(
        user=manager,
        defaults={
            'first_name': 'Анна', 'last_name': 'Менеджер',
            'position': 'manager', 'phone': '+375 (29) 999-99-99',
            'email': 'manager@hotel.com'
        }
    )
    
    # Клиент
    client_user, _ = User.objects.get_or_create(username='client')
    client_user.set_password('client123')
    client_user.save()
    client, _ = Client.objects.get_or_create(
        user=client_user,
        defaults={
            'first_name': 'Тестовый', 'last_name': 'Клиент',
            'phone': '+375 (29) 111-11-11', 'email': 'client@test.com',
            'birth_date': date(1990, 1, 1)
        }
    )
    
    # Новости
    for i in range(1, 6):
        News.objects.get_or_create(
            title=f'Новость {i}',
            defaults={
                'short_description': f'Краткое описание новости {i}',
                'full_text': f'Полный текст новости {i}'
            }
        )
    
    # Бронирования
    rooms = list(Room.objects.all())
    months = [6,7,8,9,10,11]
    for month in months:
        for _ in range(random.randint(5, 10)):
            room = random.choice(rooms)
            day = random.randint(1, 25)
            check_in = date(2026, month, day)
            check_out = check_in + timedelta(days=random.randint(1, 5))
            days = (check_out - check_in).days
            total = days * room.category.price_per_night
            Booking.objects.get_or_create(
                client=client, room=room, check_in=check_in, check_out=check_out,
                defaults={'total_price': total, 'status': 'confirmed'}
            )
    
    print('Готово! Логин: admin, пароль: admin123')
