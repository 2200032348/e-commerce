from django.urls import path
from . import views
from .views import create_item
from django.contrib.auth.models import User
from .models import OrderItem
from .views import (HomeView, ItemDetailView, add_to_cart, remove_from_the_cart, OrderSummary,
                    remove_single_from_the_cart, CheckoutView, PaymentView, AddCouponView,
                    RequestRefundView, add_likes_to_product, CustomerProfileView, add_comment_to_item,
                    complete_payment, create_item,add_item,create_user,view_users,view_order_items,Comment,view_payment_details,add_category,success_page,all_comments,refund_approval,assign_status,navbar2,warehouse,transporation,delivery_status
                    )

app_name = 'core'

urlpatterns = [
     path('',
          HomeView.as_view(), name='item_list'),
     path('item_list/<category_name>/',
          HomeView.as_view(), name='item_list_by_category'),
     path('checkout/',
          CheckoutView.as_view(), name='checkout'),
     path('payment/<payment_option>/',
          PaymentView.as_view(), name="payment"),
     path('pr'
          'oducts/<slug>/',
          ItemDetailView.as_view(), name='products'),
     path('order_summary/',
          OrderSummary.as_view(), name='order_summary'),
     path('customer_profile/',
          CustomerProfileView.as_view(), name='customer_profile'),
     path('add_to_cart/<slug>/',
          add_to_cart, name='add_to_cart'),
     path('remove_from_the_cart/<slug>/',
          remove_from_the_cart, name='remove_from_the_cart'),
     path('remove_single_from_the_cart/<slug>/',
          remove_single_from_the_cart, name='remove_single_from_the_cart'),
     path('add_coupon/',
          AddCouponView.as_view(), name="add_coupon"),
     path('request_refund/',
          RequestRefundView.as_view(), name="request_refund"),
     path('add_likes_to_product/<slug>/',
          add_likes_to_product, name="likes"),
     path('add_comment_to_item/<slug>/',
          add_comment_to_item, name="comments"),
     path('complete_payment/<tran_id>/<payment_type>/',
          complete_payment, name='complete_payment'),
     path('customers_profile', views.customers_profile, name='customers_profile'),
path('create_item.html', create_item, name='create_item'),
path('admin_dashboard.html', create_item, name='create_item'),
path('create_user.html', create_user, name='create_user'),
path('view_users.html', view_users, name='view_users'),
path('view_order_items.html', view_order_items, name='view_order_items'),
path('view_payment_details.html', view_payment_details, name='view_payment_details'),
path('add_category.html', add_category, name='add_category'),
path('success.html', success_page, name='success'),
path('all_comments.html', all_comments, name='all_comments'),
path('refund_approval/', refund_approval, name='refund_approval'),
path('assign_status/', assign_status, name='assign_status'),
path('navbar2', navbar2, name='navbar2'),
path('warehouse.html', warehouse, name='warehouse'),
path('admin_dashboard.html', navbar2, name='navbar2'),
path('transporation.html', transporation, name='transporation'),
path('delivery_status.html', delivery_status, name='delivery_status'),
]
