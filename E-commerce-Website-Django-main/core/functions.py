from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin  # Use LoginRequiredMixin
from django.db.models import CharField, Q
from django.core.paginator import Paginator
from django.contrib import messages

import os
from datetime import datetime, timedelta

from .admin import ADMIN_REGISTER
from data.config import COOKIE, get_env_var  # Use get_env_var function


LOGIN_URL = "dashboard:login"


# Page function with improved clarity and error handling
def get_paginated_data(request, model, page_size=30):
    """
    Retrieves paginated data for the specified model.

    Args:
        request (HttpRequest): The Django request object.
        model (Model): The Django model to paginate.
        page_size (int, optional): The number of items per page. Defaults to 30.

    Returns:
        Paginator: The paginator object containing the paginated data.
        int: The current page number.
    """

    try:
        page_size = int(request.GET.get('page_size', page_size))
        if page_size <= 0:
            raise ValueError("Page size must be a positive integer")
    except ValueError:
        messages.error(request, "Invalid page size. Using default (30).")
        page_size = 30

    paginator = Paginator(model, page_size)
    page_num = request.GET.get('page', 1)
    try:
        page = paginator.get_page(page_num)
    except (ValueError, InvalidPage):  # Handle potential pagination errors
        messages.error(request, "Invalid page number. Redirecting to first page.")
        return paginator.page(1)

    return paginator, page


# Admin register using a dictionary for clarity
def get_admin_data(unique_name):
    """
    Retrieves data for the specified model from the ADMIN_REGISTER dictionary.

    Args:
        unique_name (str): The unique name of the model.

    Returns:
        dict, None: A dictionary containing model information or None if not found.
    """

    for data in ADMIN_REGISTER:
        if data['model']._meta.verbose_name == unique_name:
            return data
    return None


# IsAdmin class using LoginRequiredMixin for authentication
class IsAdminMixin(LoginRequiredMixin):
    """
    Mixin class for admin user authentication. Redirects to login if not authenticated.
    """

    def dispatch(self, request, *args, **kwargs):
        cookie = request.COOKIES.get(COOKIE)
        if cookie != get_env_var('PASSWORD'):
            return redirect(LOGIN_URL)

        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            print(e)
            messages.error(request, "Error occurred. Redirecting to dashboard home.")
            return redirect("dashboard:home")


# Object filter function with type checking
def get_object(model, id):
    """
    Retrieves an object from the specified model by its ID.

    Args:
        model (Model): The Django model to query.
        id (int, str): The ID of the object to retrieve.

    Returns:
        Model, None: The retrieved object or None if not found.
    """

    try:
        if isinstance(id, int):
            return model.objects.get(id=id)
        elif isinstance(id, str):
            try:
                return model.objects.get(id=int(id))
            except ValueError:
                pass
    except model.DoesNotExist:
        pass
    return None


# Model delete function with error handling
def delete_model(model, ids):
    """
    Deletes the specified model object(s).

    Args:
        model (Model): The Django model to delete from.
        ids (int, str, list): The ID(s) of the object(s) to delete.

    Returns:
        bool: True if deletion was successful, False otherwise.
    """

    try:
        if isinstance(ids, (int, str)):
            obj = get_object(model, ids)
            if obj:
                obj.delete()
                return True
        elif isinstance(ids, list):
            for
