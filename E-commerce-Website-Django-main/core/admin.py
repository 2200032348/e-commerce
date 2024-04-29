from django.contrib import admin
from django.contrib.auth.models import User

from .models import (Item, OrderItem, Cart, Address, Category, Comment,
                     Payment, Coupon, Refund, UserProfile)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    pass

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    pass

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["__str__", 'ordered']

    class Meta:
        model = OrderItem

def update_refund_request_to_true(model_admin, request, query_set):
    query_set.update(refund_requested=False, refund_granted=True)

update_refund_request_to_true.short_description = "Update orders to refund granted"

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['__str__',
                    'ordered',
                    'being_delivered',
                    'received',
                    'refund_requested',
                    'refund_granted',
                    'billing_address',
                    'shipping_address',
                    'payment',
                    'coupon'
                    ]
    list_display_links = ['__str__',
                          'ordered',
                          'billing_address',
                          'shipping_address',
                          'payment',
                          'coupon'
                          ]
    list_filter = ['ordered',
                   'being_delivered',
                   'received',
                   'refund_requested',
                   'refund_granted'
                   ]
    search_fields = ['user__username', 'reference_code']
    actions = [update_refund_request_to_true]

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    pass

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    pass

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    pass

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'order']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'user']
