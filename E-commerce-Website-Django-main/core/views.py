import random
import string
import socket

import stripe
from django.conf import settings
from django.http import JsonResponse

from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import UserProfile
from django.http import JsonResponse

from django.http import JsonResponse
from .models import Item
from .models import Item, Category
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import Item, Category
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Item, Category

from django.views.decorators.csrf import csrf_exempt
from .models import Item
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DeleteView, View
from django.shortcuts import render, get_object_or_404, redirect, reverse, HttpResponseRedirect

import requests
from decimal import Decimal

from .forms import CheckoutForm, CouponForm, RefundForm, CommentForm
from .models import (Item, Cart, OrderItem, Address, Comment, Payment, Coupon,
                     Refund, Category, UserProfile)

stripe.api_key = settings.STRIPE_SECRET_KEY


class HomeView(ListView):
    model = Item
    template_name = "home-page.html"
    paginate_by = 8
    ordering = '-id'

    def get_queryset(self):
        queryset = Item.objects.all()
        category = self.kwargs.get('category_name')
        search_by = self.request.GET.get('key')
        # Return queryset filtered by the category
        if category:
            queryset = queryset.filter(item_category__category=category)
        if search_by:
            queryset = queryset.filter(
                Q(item_category__category__icontains=search_by) |
                Q(item_name__icontains=search_by)
            )
        return queryset.order_by('id')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        host = self.request.get_host()
        categories = Category.objects.all()
        context['categories'] = categories
        context['host'] = host
        return context


class ItemDetailView(DeleteView):
    model = Item
    template_name = "product-page.html"

    def get_context_data(self, **kwargs):
        slug = self.kwargs.get(self.slug_url_kwarg)
        comments = Comment.objects.filter(item__slug=slug)
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = comments
        return context


@login_required
def add_comment_to_item(request, slug):
    item = get_object_or_404(Item, slug=slug)
    comment = request.POST['comment']
    Comment(
        user=request.user,
        item=item,
        comment=comment
    ).save()
    return redirect("core:products", slug=slug)


class OrderSummary(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Cart.objects.get(user=self.request.user, ordered=False)
            if order.items.count() == 0:
                return redirect("core:item_list")
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        except ObjectDoesNotExist:
            return redirect('/')


@login_required
def add_likes_to_product(request, slug):
    product = get_object_or_404(Item, slug=slug)
    try:
        liked_by_user = product.likes.get(pk=request.user.pk)
        product.likes.remove(liked_by_user)
        return redirect("core:products", slug=slug)
    except ObjectDoesNotExist:
        product.likes.add(request.user)
        return redirect("core:products", slug=slug)


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    """
    Get the instance of the ordered item from the OrderItem model if it exists otherwise create the instance 
    get_or_create() returns a tuple of (object, created), where object is the retrieved or created object and created 
    is a boolean specifying whether a new object was created.
    """
    ordered_item, is_created = OrderItem.objects.get_or_create(
        user=request.user,
        item=item,
        ordered=False
    )
    user_cart = Cart.objects.filter(user=request.user, ordered=False)
    if user_cart.exists():
        user_order = user_cart[0]
        filtered_user_cart_by_the_ordered_item = user_order.items.filter(item__slug=item.slug)
        """
        If the item is already in the user cart list just increase the item quantity in the OrderItem model
        And you don't have to worry about the update of quantity in the user items field in the Cart model
        As items field in the Cart model has ManyToMany relation to the item field of the OrderItem
        It will automatically update the value in the Cart model in the user item field
        """
        if filtered_user_cart_by_the_ordered_item.exists():
            ordered_item.quantity += 1
            ordered_item.save()
            messages.info(request, "The quantity was updated")
        else:
            user_order.items.add(ordered_item)
    # If user does not have any item in the cart create the new instance in the Order model
    else:
        new_order = Cart.objects.create(
            user=request.user,
            ordered_date=timezone.now(),
        )
        new_order.items.add(ordered_item)
        messages.info(request, "The item was added to the cart")
    return redirect("core:order_summary")


@login_required
def remove_from_the_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Cart.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "This item was removed from your cart")
        else:
            messages.info(request, "This item is not in your cart")
            return redirect("core:products", slug=slug)
    else:
        messages.info(request, "You have no order existed")
        return redirect("core:products", slug=slug)
    return redirect("core:order_summary")


@login_required
def remove_single_from_the_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Cart.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity == 1:
                order.items.remove(order_item)
                order_item.delete()
            else:
                order_item.quantity -= 1
                order_item.save()
            messages.info(request, "This quantity was updated")
        else:
            messages.info(request, "This item is not in your cart")
    else:
        messages.info(request, "You have no order existed")
        return redirect("core:order_summary")
    return redirect("core:order_summary")


def is_valid_form(list_of_values):
    valid = True
    for value in list_of_values:
        if value == "":
            return False
    return valid


class CheckoutView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        form = CheckoutForm()
        try:
            order_items = Cart.objects.get(user=self.request.user, ordered=False)
            if order_items.items.count() == 0:
                messages.info(self.request, "No item in your cart")
                return redirect("core:item_list")
            context = {
                'form': form,
                "orders": order_items,
                'coupon_form': CouponForm(),
                'DISPLAY_COUPON_FORM': True
            }
            shipping_address_qs = Address.objects.filter(user=self.request.user,
                                                         address_type="S", is_default=True)
            if shipping_address_qs.exists():
                context.update({"default_shipping_address": shipping_address_qs[0]})

            billing_address_qs = Address.objects.filter(user=self.request.user,
                                                        address_type="B", is_default=True)
            if billing_address_qs.exists():
                context.update({"default_billing_address": billing_address_qs[0]})
            return render(self.request, 'checkout-page.html', context)
        except ObjectDoesNotExist:
            messages.info(self.request, "you dont have any order")
            return redirect("/")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Cart.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                # Shipping Address Handling
                set_default_shipping = form.cleaned_data.get('set_default_shipping')
                use_default_shipping = form.cleaned_data.get('use_default_shipping')
                if use_default_shipping:
                    shipping_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type="S",
                        is_default=True
                    )
                    if shipping_qs.exists():
                        shipping = shipping_qs[0]
                        order.shipping_address = shipping
                        order.save()
                    else:
                        messages.info(self.request, "No default shipping")
                        return redirect("core:checkout")
                else:
                    shipping_address = form.cleaned_data.get('shipping_address')
                    shipping_address2 = form.cleaned_data.get('shipping_address2')
                    shipping_country = form.cleaned_data.get('shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')
                    if is_valid_form([shipping_address, shipping_address2, shipping_country]):
                        shipping = Address(
                            user=self.request.user,
                            street_address=shipping_address,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip_code=shipping_zip,
                            address_type="S"
                        )
                        if set_default_shipping:
                            shipping.is_default = True
                        shipping.save()
                        order.shipping_address = shipping
                        order.save()
                    else:
                        messages.info(self.request, "Please fill in the shipping form properly")
                        return redirect("core:checkout")
                # Billing Address Handling
                same_billing_address = form.cleaned_data.get('same_billing_address')
                use_default_billing = form.cleaned_data.get('use_default_billing')
                set_default_billing = form.cleaned_data.get('set_default_billing')
                if same_billing_address:
                    billing_address = shipping
                    billing_address.pk = None
                    billing_address.address_type = "B"
                    if not set_default_billing:
                        billing_address.is_default = False
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()
                elif use_default_billing:
                    billing_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type="B",
                        is_default=True
                    )
                    if billing_qs.exists():
                        billing = billing_qs[0]
                        order.billing_address = billing
                        order.save()
                    else:
                        messages.info(self.request, "No default shipping")
                        return redirect("core:checkout")
                else:
                    billing_address = form.cleaned_data.get('billing_address')
                    billing_address2 = form.cleaned_data.get('billing_address2')
                    billing_country = form.cleaned_data.get('billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')
                    if is_valid_form([billing_address, billing_address2, billing_country]):
                        billing = Address(
                            user=self.request.user,
                            street_address=billing_address,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip_code=billing_zip,
                            address_type="B"
                        )
                        if set_default_billing:
                            billing.is_default = True
                        billing.save()
                        order.billing_address = billing
                        order.save()
                    else:
                        messages.info(self.request, "Please fill the in billing form properly")
                        return redirect("core:checkout")
                # Payment Handling
                payment_option = form.cleaned_data.get('payment_option')
                if payment_option == "S":
                    return redirect("core:payment", payment_option="Stripe")
                elif payment_option == "P":
                    return redirect("core:payment", payment_option="Paypal")
                else:
                    # add redirect to selected payment method
                    return redirect("core:checkout")
        except ObjectDoesNotExist:
            messages.error(self.request, "Error ")
            return redirect("core:checkout")


class AddCouponView(LoginRequiredMixin, View):
    def post(self, *args, **kwargs):
        order = Cart.objects.get(user=self.request.user, ordered=False)
        coupon_code = self.request.POST['coupon_code']
        available_coupons = Coupon.objects.filter(coupon=coupon_code)
        if available_coupons.exists():
            coupon = Coupon.objects.get(coupon=coupon_code)
            order.coupon = coupon
            order.save()
            messages.info(self.request, "coupon added")
            return redirect('core:checkout')
        else:
            messages.error(self.request, "There is no such coupon")
            return redirect('core:checkout')


def generate_reference_code():
    return "".join(random.choices(string.ascii_lowercase
                                  + string.ascii_uppercase
                                  + string.digits, k=20))


class PaymentView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        payment_option = kwargs.get('payment_option')
        if payment_option == "SSL":
            return redirect('core:ssl_payment')
        try:
            order = Cart.objects.get(user=self.request.user, ordered=False)
            user_profile = self.request.user.userprofile
            if order.items.count() == 0:
                messages.info(self.request, "No item in your cart")
                return redirect("core:item_list")
            if order.billing_address:
                context = {
                    "orders": order,
                    'coupon_form': CouponForm(),
                    'DISPLAY_COUPON_FORM': False
                }
                
                if user_profile.on_click_purchasing:
                    card_list = stripe.Customer.list_sources(
                        user_profile.stripe_customer_id,
                        limit=3,
                        object="card"
                    )
                    cards = card_list['data']
                    if len(cards) > 0:
                        context.update({
                            "card": cards[0]
                        })
                return render(self.request, 'payment.html', context)
            else:
                messages.warning(self.request, "You have not added a billing address")
                return redirect("core:checkout")
        except ObjectDoesNotExist:
            messages.error(self.request, "You have no active order")
            return redirect("core:item_list")

    def post(self, *args, **kwargs):
        order = Cart.objects.get(user=self.request.user, ordered=False)
        userprofile = UserProfile.objects.get(user=self.request.user)
        amount = int(order.get_total())
        stripe_charge_token = self.request.POST.get('stripeToken')
        save = self.request.POST.get('save')
        user_default = self.request.POST.get('use_default')

        # To do for if the user wants to save card information for future purpose or not
        if save:
            """
            If user is not registered with stripe_customer_id Create the new customer instance
            and store information to the UserProfile model
            Otherwise retrieve the user information from the UserProfile model
            Pass the already stored stripe_customer_id as the source value
            To create a new source in the stripe db
            """
            if not userprofile.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=str(self.request.user.email),
                    name=self.request.user.username
                )
                customer.create(source=stripe_charge_token)
                userprofile.stripe_customer_id = customer['id']
                userprofile.on_click_purchasing = True
                userprofile.save()
            else:
                customer = stripe.Customer.retrieve(
                    userprofile.stripe_customer_id)
                
                customer.create(source=stripe_charge_token)

        # To do for saving payment information
        try:
            """
            If the user wants to use the previous default card retrieve the stripe_customer_id
            from the UserProfile model and pass that to stripe api source to create charges
            Otherwise create the charges using the token generated by stripe
            """
            if user_default or save:
                charge = stripe.Charge.create(
                    amount=amount*100,
                    currency="usd",
                    customer=userprofile.stripe_customer_id
                )
            else:
                charge = stripe.Charge.create(
                    amount=amount*100,
                    currency="usd",
                    source=stripe_charge_token
                )
            messages.success(self.request, "Stripe Payment Successful")
            return redirect('core:complete_payment', tran_id=charge['id'], payment_type="S")

        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            messages.warning(self.request, f"{err.get('message')}")
            return redirect("core:payment", payment_option="Stripe")

        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.warning(self.request, "Rate limit error")
            return redirect("core:payment", payment_option="Stripe")

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.warning(self.request, "Invalid parameters")
            return redirect("core:payment", payment_option="Stripe")

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.warning(self.request, "Not authenticated")
            return redirect("core:payment", payment_option="Stripe")

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.warning(self.request, "Network error")
            return redirect("core:payment", payment_option="Stripe")

        except stripe.error.StripeError as e:
            messages.warning(
                self.request, "Something went wrong. You were not charged. Please try again.")
            return redirect("core:payment", payment_option="Stripe")

        except Exception as e:
            # Send an email to ourselves
            messages.warning(
                self.request, "A serious error occurred. We have been notified.")
            return redirect("core:payment", payment_option="Stripe")


class RequestRefundView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        orders = Cart.objects.filter(user=self.request.user, ordered=True)
        if not orders.exists():
            messages.info(self.request, "You have no orders yet, happy shopping !!")
            return redirect('/')
        refund_form = RefundForm()
        context = {
            "form": refund_form
        }
        return render(self.request, 'request_refund.html', context)

    def post(self, *args, **kwargs):
        refund_form = RefundForm(self.request.POST)
        if refund_form.is_valid():
            reference_code = refund_form.cleaned_data['reference_code']
            try:
                is_refund_already_granted = Cart.objects.filter(reference_code=reference_code, refund_granted=True)
                is_refund_already_requested = Refund.objects.filter(reference_code=reference_code)
                if is_refund_already_granted.exists():
                    messages.info(self.request, "Already Refunded")
                    return redirect('core:customer_profile')
                elif is_refund_already_requested.exists():
                    messages.info(self.request, "Refund already requested for this order")
                    return redirect('core:customer_profile')
                else:
                    order = Cart.objects.get(reference_code=reference_code)
                    order.refund_requested = True
                    order.save()
                    refund = Refund.objects.create(order=order, **refund_form.cleaned_data)

                    # Add status to the refund object
                    refund.status = 'pending'  # You can set the initial status as 'pending'
                    refund.save()

                    messages.info(self.request, "Your request was successful")
                    return redirect("core:customer_profile")
            except ObjectDoesNotExist:
                messages.info(self.request, "No such order with that reference code")
                return redirect("core:customer_profile")


class CustomerProfileView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Fetching orders for the current user
        orders = Cart.objects.filter(user=request.user, ordered=True)
        if orders.exists():
            context = {
                "orders": orders
            }
            return render(request, 'customer_profile.html', context)
        else:
            # If the user has not ordered anything, redirect with a message
            messages.info(request, "You have not yet ordered anything from our site")
            return redirect("/")

        # Fetching todos for the current user
        all_user_profiles = UserProfiles.objects.filter(user=request.user)
        context = {
            "user_profiles": all_user_profiles
        }
        return render(request, 'api/item.html', context)


@login_required
def complete_payment(request, tran_id, payment_type):
    order = Cart.objects.get(user=request.user, ordered=False)
    amount = int(order.get_total())
    payment = Payment()
    payment.user = request.user
    payment.amount = amount
    payment.stripe_charge_id = tran_id
    payment.save()

    order.ordered = True
    order.payment = payment
    order.reference_code = generate_reference_code()
    order.save()
    users_order = OrderItem.objects.filter(user=request.user, ordered=False)
    for order in users_order:
        order.ordered = True
        order.save()
    return HttpResponseRedirect(reverse('core:item_list'))

def customers_profile(request):
    if request.method == 'GET':
        users = User.objects.all()
        data = [{'id': user.id, 'username': user.username, 'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name} for user in users]
        return render(request, 'customer_profile.html', {'users': data})
    elif request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            data = {'id': user.id, 'username': user.username, 'email': user.email, 'first_name': user.first_name, 'last_name': user.last_name}
            return JsonResponse(data)
        else:
             return JsonResponse({'error': form.errors})

def add_item(request):
    if request.method == 'POST':
        # Get form data
        item_name = request.POST.get('item_name')
        item_category = request.POST.get('item_category')
        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price')
        item_image = request.FILES.get('item_image')
        labels = request.POST.get('labels')
        slug = request.POST.get('slug')
        likes = request.POST.get('likes')
        description = request.POST.get('description')

        # Save the new item
        item = Item(
            item_name=item_name,
            item_category=item_category,
            price=price,
            discount_price=discount_price,
            item_image=item_image,
            labels=labels,
            slug=slug,
            likes=likes,
            description=description
        )
        item.save()

        # Redirect to the item list page
        return redirect('item_list')

    return render(request, 'add_item.html')

@csrf_exempt
def create_item(request):
    if request.method == 'POST':
        # Extract data from the form
        item_name = request.POST.get('item_name')
        item_category_name = request.POST.get('item_category')
        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price')
        item_image = request.FILES.get('item_image')
        labels = request.POST.get('labels')
        slug = request.POST.get('slug')
        description = request.POST.get('description')

        try:
            # Retrieve the Category instance based on the provided category name
            item_category = Category.objects.get(category=item_category_name)
        except Category.DoesNotExist:
            # Handle the case when the category does not exist
            return JsonResponse({'error': f'Category "{item_category_name}" does not exist'}, status=400)

        # Create a new item in the database
        new_item = Item.objects.create(
            item_name=item_name,
            item_category=item_category,
            price=price,
            discount_price=discount_price,
            item_image=item_image,
            labels=labels,
            slug=slug,
            description=description
        )

    # Retrieve all items
    items = Item.objects.all()

    # Render the template with the items
    return render(request, 'create_item.html', {'items': items})


def create_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(username=username, email=email, password=password)
            return JsonResponse({'success': f'User {username} created successfully'})
        else:
            return JsonResponse({'error': f'Username {username} already exists'}, status=400)
    return render(request, 'create_user.html')


def view_users(request):
    users = User.objects.all()
    return render(request, 'view_users.html', {'users': users})

def view_order_items(request):
    order_items = OrderItem.objects.all()
    return render(request, 'view_order_items.html', {'order_items': order_items})


#
# def view_comment(request):
#     comments = comments.objects.all()
#     return render(request, 'view_comment.html', {'comments': comments})


def view_payment_details(request):
    payments = Payment.objects.all()
    return render(request, 'view_payment_details.html', {'payments': payments})

def add_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        # Check if category already exists
        category, created = Category.objects.get_or_create(category=category_name)
        # If category doesn't exist, create it
        if created:
            # Assuming you're associating category directly with a product
            product_id = request.POST.get('product_id')
            product = get_object_or_404(Product, pk=product_id)
            product.categories.add(category)
            product.save()
        return HttpResponseRedirect('/success.html')  # Redirect to success page after adding category
    return render(request, 'add_category.html')


def success_page(request):
    return render(request, 'success.html')

def all_comments(request):
    comments = Comment.objects.all()
    return render(request, 'all_comments.html', {'comments': comments})


def refund_approval(request):
    if not request.user.is_superuser:
        return redirect('home')  # Redirect non-admin users to home page

    pending_refunds = Refund.objects.filter(status='pending')
    approved_refunds = Refund.objects.filter(status='approved')
    rejected_refunds = Refund.objects.filter(status='rejected')

    return render(request, 'refund_approval.html', {'pending_refunds': pending_refunds,
                                                     'approved_refunds': approved_refunds,
                                                     'rejected_refunds': rejected_refunds})

def assign_status(request, refund_id=None):
    if not request.user.is_superuser:
        return redirect('home')  # Redirect non-admin users to home page

    if refund_id is not None:
        refund = get_object_or_404(Refund, id=refund_id)
    else:
        refund = None

    if request.method == 'POST':
        if refund is not None:
            status = request.POST.get('status')
            refund.status = status
            refund.save()
            return redirect('refund_approval')

    return render(request, 'assign_status.html', {'refund': refund})


def navbar2(request):
    return render(request, 'navbar2.html')

def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

def warehouse(request):
    return render(request, 'warehouse.html')


def transporation(request):
    return render(request, 'transporation.html')

def delivery_status(request):
    # Retrieve cart data from the database
    carts = Cart.objects.all()
    return render(request, 'delivery_status.html', {'carts': carts})
