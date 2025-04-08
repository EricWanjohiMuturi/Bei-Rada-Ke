from django.contrib import admin
from .models import EcommerceShop, Brand, Category, Product, PriceHistory

#register models
class EcommerceShopAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    filter_horizontal = ('allowed_brands',)

class PriceHistoryInline(admin.TabularInline):
    model = PriceHistory
    extra = 0
    readonly_fields = ('price', 'date_recorded')
    can_delete = False

class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'ecommerce_shop', 'price', 'category', 'brand', 'review', 'created_at')
    list_filter = ('ecommerce_shop', 'category', 'brand', 'created_at')
    search_fields = ('title', 'ecommerce_shop__name', 'category__name', 'brand__name')
    autocomplete_fields = ('ecommerce_shop', 'category', 'brand')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PriceHistoryInline]
    readonly_fields = ('last_price_update', 'created_at', 'updated_at', 'days_since_price_update')
    fieldsets = (
        (None, {
            'fields': (
                'title', 'slug', 'image', 'ecommerce_shop', 'price', 'external_url',
                'category', 'brand', 'review'
            )
        }),
        ("Details", {
            'fields': ('description', 'attributes')
        }),
        ("Timestamps", {
            'fields': ('last_price_update', 'created_at', 'updated_at', 'days_since_price_update')
        }),
    )

admin.site.register(EcommerceShop, EcommerceShopAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
