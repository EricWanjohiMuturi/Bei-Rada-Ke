from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from django_summernote.fields import SummernoteTextField

class EcommerceShop(models.Model):
    name = models.CharField(max_length=100, unique=True)
    thumbnail = models.ImageField(upload_to='ecommerce_thumbs/')
    slug = models.SlugField(max_length=100, unique=True)
    
    class Meta:
        verbose_name = "Ecommerce Shop"
        verbose_name_plural = "Ecommerce Shops"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='brand_images/')
    slug = models.SlugField(max_length=100, unique=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    thumbnail = models.ImageField(upload_to='category_thumbs/')
    slug = models.SlugField(max_length=100, unique=True)
    allowed_brands = models.ManyToManyField(
        Brand, 
        related_name='allowed_categories',
        blank=True,
        help_text="Brands that can be associated with this category"
    )
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Product(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='product_images/')
    ecommerce_shop = models.ForeignKey(
        EcommerceShop,
        on_delete=models.PROTECT,
        related_name='products'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    last_price_update = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When price was last updated"
    )
    description = SummernoteTextField()
    attributes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Key-value pairs of product attributes"
    )
    external_url = models.URLField(
        max_length=500,
        help_text="URL to product on the ecommerce site"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        related_name='products'
    )
    review = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Product rating (0-5 or 0-10 scale)"
    )
    slug = models.SlugField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['title', 'ecommerce_shop']
        indexes = [
            models.Index(fields=['last_price_update']),
            models.Index(fields=['price']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.ecommerce_shop.name}"
    
    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})
    
    def clean(self):
        """Validate that brand is allowed for this category"""
        if not self.category.allowed_brands.filter(pk=self.brand.pk).exists():
            raise ValidationError(
                f"{self.brand.name} is not an allowed brand for {self.category.name} category"
            )
    
    def save(self, *args, **kwargs):
        """Track price changes and update last_price_update"""
        if self.pk:
            original = Product.objects.get(pk=self.pk)
            if original.price != self.price:
                self.last_price_update = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def days_since_price_update(self):
        """Calculate days since last price update"""
        if not self.last_price_update:
            return None
        return (timezone.now() - self.last_price_update).days

class PriceHistory(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='price_history'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    date_recorded = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_recorded']
        verbose_name_plural = 'Price Histories'
        indexes = [
            models.Index(fields=['date_recorded']),
        ]
    
    def __str__(self):
        return f"{self.product.title} - ${self.price} on {self.date_recorded.strftime('%Y-%m-%d')}"

def create_price_history(sender, instance, created, **kwargs):
    """Signal to create price history record after Product save"""
    if not created and hasattr(instance, '_price_changed'):
        PriceHistory.objects.create(
            product=instance,
            price=instance.price
        )

# Connect the signal
from django.db.models.signals import post_save
post_save.connect(create_price_history, sender=Product)