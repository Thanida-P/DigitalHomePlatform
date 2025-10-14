from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Address
from django.http import JsonResponse
from .funcHelper import *

# Address Management
# Add Address
@csrf_exempt
@require_http_methods(["POST"])
def add_address(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    user = request.user
    
    if not hasattr(user, 'customer'):
        return JsonResponse({'error': 'Only customers can manage addresses'}, status=403)
    
    address = request.POST.get('address')
    is_default = request.POST.get('is_default', 'false').lower() == 'true'
    if not address:
        return JsonResponse({'error': 'Address is required'}, status=400)

    new_address = Address.objects.create(customer=user.customer, address=address, is_default=is_default)
    user.customer.address.append(new_address.id)
    user.customer.save()
    return JsonResponse({'message': 'Address added successfully'}, status=201)

# Edit Address
@csrf_exempt
@require_http_methods(["PUT"])
def edit_address(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    user = request.user
    
    if not hasattr(user, 'customer'):
        return JsonResponse({'error': 'Only customers can manage addresses'}, status=403)
    
    put_data = parse_request_body(request)
    new_address = put_data.get('address')
    address_id = put_data.get('address_id')
    
    if not address_id:
        return JsonResponse({'error': 'Address ID is required'}, status=400)
    
    try:
        address = Address.objects.get(id=address_id, customer=user.customer)
    except Address.DoesNotExist:
        return JsonResponse({'error': 'Address not found'}, status=404)

    if new_address:
        address.address = new_address
    
    address.save()
    return JsonResponse({'message': 'Address updated successfully'}, status=200)

# Set Default Address
@csrf_exempt
@require_http_methods(["PUT"])
def set_default_address(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    user = request.user
    
    if not hasattr(user, 'customer'):
        return JsonResponse({'error': 'Only customers can manage addresses'}, status=403)
    
    put_data = parse_request_body(request)
    address_id = put_data.get('address_id')
    
    if not address_id:
        return JsonResponse({'error': 'Address ID is required'}, status=400)
    
    try:
        new_default_address = Address.objects.get(id=address_id, customer=user.customer)
    except Address.DoesNotExist:
        return JsonResponse({'error': 'Address not found'}, status=404)

    with transaction.atomic():
        Address.objects.filter(customer=user.customer, is_default=True).update(is_default=False)
        new_default_address.is_default = True
        new_default_address.save()
    
    return JsonResponse({'message': 'Default address set successfully'}, status=200)

# Remove Address
@csrf_exempt
@require_http_methods(["DELETE"])
def remove_address(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    user = request.user
    
    if not hasattr(user, 'customer'):
        return JsonResponse({'error': 'Only customers can manage addresses'}, status=403)
    
    delete_data = parse_request_body(request)
    address_id = delete_data.get('address_id')
    
    if not address_id:
        return JsonResponse({'error': 'Address ID is required'}, status=400)
    
    try:
        address = Address.objects.get(id=address_id, customer=user.customer)
    except Address.DoesNotExist:
        return JsonResponse({'error': 'Address not found'}, status=404)

    user.customer.address.remove(address.id)
    user.customer.save()
    address.delete()
    return JsonResponse({'message': 'Address removed successfully'}, status=200)

# Get Addresses
@csrf_exempt
@require_http_methods(["GET"])
def get_addresses(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    user = request.user
    
    if not hasattr(user, 'customer'):
        return JsonResponse({'error': 'Only customers can manage addresses'}, status=403)
    
    addresses = Address.objects.filter(customer=user.customer)
    address_list = [{'id': addr.id, 'address': addr.address, 'is_default': addr.is_default} for addr in addresses]
    
    return JsonResponse({'addresses': address_list}, status=200)

