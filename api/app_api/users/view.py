from django.http import JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Staff, User, Customer
import json

@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    username = request.POST['username']
    password = request.POST['password']
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    email = request.POST['email'].lower()
    phone_no = request.POST['phone_no']


    with transaction.atomic():
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        Customer.objects.create(
            user=user,
            email=email,
            phone_no=phone_no,
            address=[],
            owned_digital_products=[],
            purchased_history=[],
            credit_cards=[],
            bank_accounts=[],
            cart_id=None
        )

    response = JsonResponse({'message': 'User registered successfully'}, status=201)
    response.set_cookie(
        'username', 
        username, 
        max_age=60*60*24*30, 
        httponly=True, 
        secure=True
    )
    return response

@csrf_exempt
@require_http_methods(["POST"])
def register_admin(request):
    username = request.POST['username']
    password = request.POST['password']
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']

    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'Username already exists'}, status=409)

    User.objects.create_superuser(
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name
    )

    return JsonResponse({'message': 'Admin user registered successfully'}, status=201)

@csrf_exempt
@require_http_methods(["POST"])
def register_staff(request):
    username = request.POST['username']
    password = request.POST['password']
    first_name = request.POST['first_name']
    last_name = request.POST['last_name']
    email = request.POST['email'].lower()

    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'Username already exists'}, status=409)

    with transaction.atomic():
        user = User.objects.create_staffuser(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        Staff.objects.create(
            user=user,
            email=email
        )

    return JsonResponse({'message': 'Staff user registered successfully'}, status=201)

@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    identifier = request.POST['identifier']
    password = request.POST['password']

    if not identifier or not password:
        return JsonResponse({'error': 'username/email and password required'}, status=400)

    user = authenticate(request, username=identifier, password=password)

    if user is None and '@' in identifier:
        user_object = None
        try:
            user_object = Customer.objects.get(email=identifier.lower())
        except Customer.DoesNotExist:
            try:
                user_object = Staff.objects.get(email=identifier.lower())
            except Staff.DoesNotExist:
                user_object = None
        if user_object is not None:
            user = authenticate(request, username=user_object.user.username, password=password)

    if user is not None:
        auth_login(request, user)
        response = JsonResponse({
            'message': 'Login successful',
            'is_admin': getattr(user, 'is_admin', False),
            'is_staff': getattr(user, 'is_staff', False)
        }, status=200)
        response.set_cookie(
            'username',
            getattr(user, 'username'),
            max_age=60*60*24*30,
            httponly=True,
            secure=True
        )
        return response
    else:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

@require_http_methods(["GET"])
def is_logged_in(request):
    if hasattr(request, 'user') and request.user.is_authenticated:
        return JsonResponse({'logged_in': True, 'username': getattr(request.user, 'username', None)})
    username = request.COOKIES.get('username')
    if username:
        return JsonResponse({'logged_in': False, 'username': username})
    return JsonResponse({'logged_in': False, 'username': None})

@csrf_exempt
@require_http_methods(["DELETE"])
def logout_view(request):
    auth_logout(request)
    response = JsonResponse({'message': 'Logged out successfully'}, status=200)
    response.delete_cookie('username')
    response.delete_cookie('sessionid')
    response.delete_cookie('csrftoken')
    return response
