from django.contrib import admin
from .models import Client, Employee, RoomCategory, Room, News, GlossaryTerm, Vacancy, PromoCode, Booking, Review

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'phone', 'email']
    search_fields = ['last_name', 'first_name', 'phone']

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'position', 'phone']
    search_fields = ['last_name', 'first_name']

@admin.register(RoomCategory)
class RoomCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity', 'price_per_night']

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'category', 'is_available']
    list_filter = ['category', 'is_available']

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'published_at']
    list_filter = ['published_at']

@admin.register(GlossaryTerm)
class GlossaryTermAdmin(admin.ModelAdmin):
    list_display = ['term', 'added_date']

@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ['title', 'salary', 'created_at']

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'is_active', 'start_date', 'end_date']
    list_filter = ['is_active']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'room', 'check_in', 'check_out', 'status']
    list_filter = ['status', 'check_in']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['client', 'rating', 'created_at']
    list_filter = ['rating']
