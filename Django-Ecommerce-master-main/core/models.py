from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from django.shortcuts import reverse
from django_countries.fields import CountryField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum, F, FloatField, ExpressionWrapper
from django.db.models.functions import TruncDay, TruncMonth
LABEL_CHOICES = (
    ('S', 'sale'),
    ('N', 'new'),
    ('P', 'promotion')
)

ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return f'Profile của {self.user.username}'

class Category(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField()
    description = models.TextField()
    image = models.ImageField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:category", kwargs={
            'slug': self.slug
        })

class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.FloatField()
    discount_price = models.FloatField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1)
    slug = models.SlugField()
    #stock_no
    stock_no = models.IntegerField()
    description_short = models.CharField(max_length=50)
    description_long = models.TextField()
    image = models.ImageField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)  # Ngày tạo
    updated_at = models.DateTimeField(auto_now=True,null=True)  # Ngày cập nhật
    last_purchased_at = models.DateTimeField(blank=True, null=True)  # Ngày mua cuối cùng
    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:product", kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart", kwargs={
            'slug': self.slug
        })

    def get_remove_from_cart_url(self):
        return reverse("core:remove-from-cart", kwargs={
            'slug': self.slug
        })


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} of {self.item.title}"

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()

    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=20)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    shipping_address = models.ForeignKey(
        'BillingAddress', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    billing_address = models.ForeignKey(
        'BillingAddress', related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(
        'Payment', on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, blank=True, null=True)
    being_delivered = models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)

    '''
    1. Item added to cart
    2. Adding a BillingAddress
    (Failed Checkout)
    3. Payment
    4. Being delivered
    5. Received
    6. Refunds
    '''

    def __str__(self):
        return self.user.username

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        if self.coupon:
            total -= self.coupon.amount
        return total

    def update_stock_no(self):
        for order_item in self.items.all():
            item = order_item.item
            item.stock_no -= order_item.quantity
            item.last_purchased_at = self.ordered_date
            item.save()
    @staticmethod
    def get_daily_revenue():
        daily_revenue = Order.objects.filter(
            ordered=True
        ).annotate(
            day=TruncDay('ordered_date')
        ).values(
            'day'
        ).annotate(
            total_revenue=Sum(
                ExpressionWrapper(
                    F('items__quantity') * F('items__item__price'),
                    output_field=FloatField()
                )
            )
        ).order_by('day')
        return daily_revenue

    @staticmethod
    def get_monthly_revenue():
        monthly_revenue = Order.objects.filter(
            ordered=True
        ).annotate(
            month=TruncMonth('ordered_date')
        ).values(
            'month'
        ).annotate(
            total_revenue=Sum(
                ExpressionWrapper(
                    F('items__quantity') * F('items__item__price'),
                    output_field=FloatField()
                )
            )
        ).order_by('month')
        return monthly_revenue
    @staticmethod
    def get_item_monthly_revenue():
        item_monthly_revenue = OrderItem.objects.filter(
            order__ordered=True
        ).annotate(
            month=TruncMonth('order__ordered_date')
        ).values(
            'month', 'item__title'
        ).annotate(
            total_revenue=Sum(
                ExpressionWrapper(
                    F('quantity') * F('item__price'),
                    output_field=FloatField()
                )
            )
        ).order_by('month', 'item__title')
        return item_monthly_revenue

class BillingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = 'BillingAddresses'


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class Coupon(models.Model):
    code = models.CharField(max_length=15)
    amount = models.FloatField()
    def __str__(self):
        return self.code


class Refund(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()
    def __str__(self):
        return f"{self.pk}"

class Review(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL, blank=True, null=True)
    content = models.TextField()
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True)
    date_created = models.DateTimeField(auto_now_add=True, null=True)
    def __str__(self):
        return self.content
