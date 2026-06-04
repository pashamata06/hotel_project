from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
import re
from datetime import date

def validate_phone(value):
    pattern = r'^\+375 \(29\) \d{3}-\d{2}-\d{2}$'
    if not re.match(pattern, value):
        raise ValidationError('Телефон должен быть в формате +375 (29) XXX-XX-XX')

def validate_age(value):
    today = date.today()
    age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    if age < 18:
        raise ValidationError('Возраст должен быть 18 лет или старше')

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50, default='')
    last_name = models.CharField(max_length=50, default='')
    patronymic = models.CharField(max_length=50, blank=True)
    birth_date = models.DateField(validators=[validate_age], null=True, blank=True)
    phone = models.CharField(max_length=20, validators=[validate_phone], default='+375 (29) 000-00-00')
    email = models.EmailField(default='')
    has_child = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

class Employee(models.Model):
    POSITION_CHOICES = [
        ('admin', 'Администратор'),
        ('manager', 'Менеджер'),
        ('cleaner', 'Горничная'),
        ('reception', 'Сотрудник ресепшн'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES)
    phone = models.CharField(max_length=20, validators=[validate_phone])
    email = models.EmailField()
    photo = models.ImageField(upload_to='employees/', null=True, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.last_name} {self.first_name} - {self.get_position_display()}"

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

class RoomCategory(models.Model):
    name = models.CharField(max_length=100)
    capacity = models.IntegerField(help_text='Максимум человек')
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='categories/', null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.price_per_night} руб."

    class Meta:
        verbose_name = 'Категория номера'
        verbose_name_plural = 'Категории номеров'

class Room(models.Model):
    room_number = models.CharField(max_length=10, unique=True)
    category = models.ForeignKey(RoomCategory, on_delete=models.CASCADE, related_name='rooms')
    is_available = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='rooms/', null=True, blank=True)

    def __str__(self):
        return f"Номер {self.room_number} - {self.category.name}"

    class Meta:
        verbose_name = 'Номер'
        verbose_name_plural = 'Номера'

class News(models.Model):
    title = models.CharField(max_length=200)
    short_description = models.CharField(max_length=300)
    full_text = models.TextField()
    image = models.ImageField(upload_to='news/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-published_at']

class GlossaryTerm(models.Model):
    term = models.CharField(max_length=100)
    definition = models.TextField()
    added_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.term

    class Meta:
        verbose_name = 'Термин'
        verbose_name_plural = 'Словарь терминов'

class Vacancy(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    salary = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'

class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.IntegerField()
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        return f"{self.code} - {self.discount_percent}%"

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('confirmed', 'Подтверждена'),
        ('cancelled', 'Отменена'),
        ('completed', 'Завершена'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    check_in = models.DateField()
    check_out = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    promo_code = models.ForeignKey(PromoCode, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Бронь {self.id} - {self.client.last_name}"

    class Meta:
        verbose_name = 'Бронь'
        verbose_name_plural = 'Брони'

class Review(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Отзыв от {self.client.last_name} - {self.rating}★"

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
