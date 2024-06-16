from django.contrib import admin
from django.contrib import messages
from .models import Item, OrderItem, Order, Payment, Coupon, Refund, BillingAddress, Category, Review
from django.utils import timezone

# Register your models here.


def make_refund_accepted(modeladmin, request, queryset):
    queryset.update(refund_requested=False, refund_granted=True)


make_refund_accepted.short_description = 'Update orders to refund granted'


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user',
                    'ordered',
                    'being_delivered',
                    'received',
                    'refund_requested',
                    'refund_granted',
                    'shipping_address',
                    'billing_address',
                    'payment',
                    'coupon'
                    ]
    list_display_links = [
        'user',
        'shipping_address',
        'billing_address',
        'payment',
        'coupon'
    ]
    list_filter = ['user',
                   'ordered',
                   'being_delivered',
                   'received',
                   'refund_requested',
                   'refund_granted']
    search_fields = [
        'user__username',
        'ref_code'
    ]
    actions = [make_refund_accepted]


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'street_address',
        'apartment_address',
        'country',
        'zip',
        'address_type',
        'default'
    ]
    list_filter = ['default', 'address_type', 'country']
    search_fields = ['user', 'street_address', 'apartment_address', 'zip']


def copy_items(modeladmin, request, queryset):
    for object in queryset:
        object.id = None
        object.save()


copy_items.short_description = 'Copy Items'


class ItemAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'category',
        'label',
        'price',
        'stock_no',
        'created_at',
        'updated_at',
        'last_purchased_at'
    ]
    list_filter = ['title', 'category']
    search_fields = ['title', 'category']
    prepopulated_fields = {"slug": ("title",)}
    actions = [copy_items]

    def changelist_view(self, request, extra_context=None):
        # Gọi phương thức changelist_view gốc của Django
        response = super().changelist_view(request, extra_context)

        # Kiểm tra các mục có stock_no < 30
        low_stock_items = Item.objects.filter(stock_no__lt=30)
        if low_stock_items.exists():
            item_list = ", ".join([item.title for item in low_stock_items])
            self.message_user(request, f"Thông báo: Mặt hàng [{item_list}] sắp hết hàng trong kho, cần nhập thêm hàng", level=messages.WARNING)
        
        # Kiểm tra các item không được mua trong vòng 30 ngày
        a_month_ago = timezone.now() - timezone.timedelta(days=30)
        unsold_items = Item.objects.filter(last_purchased_at__lte=a_month_ago)
        if unsold_items.exists():
            unsold_item_list = ", ".join([item.title for item in unsold_items])
            self.message_user(request, f"Thông báo: Mặt hàng [{unsold_item_list}] không có người mua trong hơn 30 ngày qua", level=messages.WARNING)

        return response

class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'is_active'
    ]
    list_filter = ['title', 'is_active']
    search_fields = ['title', 'is_active']
    prepopulated_fields = {"slug": ("title",)}
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'user','item'
    ]
    list_filter = ['user','item']
    search_fields = ['user','item']

admin.site.register(Item, ItemAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(OrderItem)
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(Coupon)
admin.site.register(Refund)
admin.site.register(BillingAddress, AddressAdmin)
admin.site.register(Review)
