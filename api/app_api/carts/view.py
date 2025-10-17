from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from .models import CartItem
from .funcHelper import *

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def add_to_cart(request):
    customer = request.user.customer

    if not customer:
        return JsonResponse({'error': 'Only customers can manage carts'}, status=403)

    product_id = request.POST.get('product_id')
    item_type = request.POST.get('type')  # 'digital' or 'physical'
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Quantity must be an integer'}, status=400)

    if not product_id:
        return JsonResponse({'error': 'Product ID is required'}, status=400)
    if item_type not in ['digital', 'physical']:
        return JsonResponse({'error': 'Type must be either digital or physical'}, status=400)
    if quantity < 1:
        return JsonResponse({'error': 'Quantity must be at least 1'}, status=400)

    cart = customer.carts.first()

    if not cart:
        return JsonResponse({'error': 'Cart not found'}, status=404)

    items = cart.cart_items
    item = items.filter(product_id=product_id, type=item_type)

    if item.exists():
        cart_item = item.first()
        cart_item.quantity += quantity
        cart_item.save()
    else:
        cart_item = CartItem.objects.create(cart=cart, product_id=product_id, type=item_type, quantity=quantity)
        cart.items.append(cart_item.id)
    cart.total_price = calculate_total_price(cart.cart_items.all())
    cart.save()

    return JsonResponse({'message': 'Item added to cart successfully'}, status=201)

@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def remove_from_cart(request, cart_item_id):
    customer = request.user.customer

    if not customer:
        return JsonResponse({'error': 'Only customers can manage carts'}, status=403)

    cart = customer.carts.first()

    if not cart:
        return JsonResponse({'error': 'Cart not found'}, status=404)

    try:
        cart_item = CartItem.objects.get(id=cart_item_id, cart=cart)
    except CartItem.DoesNotExist:
        return JsonResponse({'error': 'Cart item not found'}, status=404)

    cart.items.remove(cart_item.id)
    cart_item.delete()
    cart.total_price = calculate_total_price(cart.cart_items.all())
    cart.save()

    return JsonResponse({'message': 'Item removed from cart successfully'}, status=200)

@csrf_exempt
@login_required
@require_http_methods(["GET"])
def view_cart(request):
    customer = request.user.customer

    if not customer:
        return JsonResponse({'error': 'Only customers can manage carts'}, status=403)

    cart = customer.carts.first()

    if not cart:
        return JsonResponse({'error': 'Cart not found'}, status=404)

    items = []
    for cart_item in cart.cart_items.all():
        items.append({
            'id': cart_item.id,
            'product_id': cart_item.product.id,
            'product_name': cart_item.product.name,
            'quantity': cart_item.quantity,
            'type': cart_item.type,
            'added_at': cart_item.added_at.isoformat(),
        })

    response_data = {
        'cart_id': cart.id,
        'items': items,
    }

    return JsonResponse(response_data, status=200)

@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def clear_cart(request):
    customer = request.user.customer

    if not customer:
        return JsonResponse({'error': 'Only customers can manage carts'}, status=403)

    cart = customer.carts.first()

    if not cart:
        return JsonResponse({'error': 'Cart not found'}, status=404)

    cart.cart_items.all().delete()
    cart.items = []
    cart.total_price = 0.00
    cart.save()

    return JsonResponse({'message': 'Cart cleared successfully'}, status=200)

@login_required
@require_http_methods(["GET"])
def get_cart_summary(request):
    data = parse_request_body(request) or request.GET.dict()

    customer = request.user.customer
    if not customer:
        return JsonResponse({'error': 'Only customers can manage carts'}, status=403)

    tax = to_decimal(data.get('tax', 0))
    shipping = to_decimal(data.get('shipping', 0))
    discount = to_decimal(data.get('discount', 0))

    cart = customer.carts.first()
    if not cart:
        return JsonResponse({'error': 'Cart not found'}, status=404)
    subtotal = calculate_total_price(cart.cart_items.all())
    if not isinstance(subtotal, Decimal):
        try:
            subtotal = Decimal(str(subtotal))
        except (InvalidOperation, ValueError, TypeError):
            subtotal = Decimal('0')

    total = subtotal + tax + shipping - discount
    response_data = {
        'subtotal': str(subtotal),
        'tax': str(tax),
        'shipping': str(shipping),
        'discount': str(discount),
        'total': str(total)
    }
    return JsonResponse(response_data, status=200)