from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem
from app_api.products.models import OwnedProducts, ContainerOwnedProducts, NonContainerOwnedProducts

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def checkout(request):
    customer = request.user.customer

    if not customer:
        return JsonResponse({'error': 'Only customers can manage carts'}, status=403)

    cart = customer.carts.first()

    if not cart:
        return JsonResponse({'error': 'Cart not found'}, status=404)

    if cart.cart_items.count() == 0:
        return JsonResponse({'error': 'Cart is empty'}, status=400)

    order = Order.objects.create(
        customer=customer,
        order_items=[],
        total_price=cart.total_price,
        status='pending'
    )
    
    items = []
    cart_items = cart.cart_items.all()
    for item in cart_items:
        order_item = OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            type=item.type
        )
        items.append(order_item.id)
    order.order_items = items
    order.save()
    
    cart.cart_items.all().delete()
    cart.total_price = 0.00
    cart.items = []
    cart.save()
    
    customer.purchased_history.append(order.id)
    customer.save()
    return JsonResponse({'message': 'Order created successfully', 'order_id': order.id}, status=201)

@login_required
@require_http_methods(["GET"])
def list_orders(request):
    customer = request.user.customer
    if not customer:
        return JsonResponse({'error': 'Only customers can view orders'}, status=403)
    orders_data = []
    for order in customer.orders.all().order_by('-created_at'):
        order_items = []
        for item in order.order_items_rel.all():
            order_items.append({
                'id': item.id,
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'type': item.type,
                'added_at': item.added_at.isoformat(),
            })
        orders_data.append({
            'order_id': order.id,
            'order_items': order_items,
            'total_price': str(order.total_price),
            'status': order.status,
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat(),
        })
    return JsonResponse({'orders': orders_data}, status=200)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def payment_completed(request, order_id):
    customer = request.user.customer
    if not customer:
        return JsonResponse({'error': 'Only customers can update orders'}, status=403)
    try:
        order = Order.objects.get(id=order_id, customer=customer)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    
    order.status = 'payment completed'
    order.save()
    return JsonResponse({'message': 'Order status updated to payment completed'}, status=200)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def cancel_order(request, order_id):
    customer = request.user.customer
    if not customer:
        return JsonResponse({'error': 'Only customers can update orders'}, status=403)
    try:
        order = Order.objects.get(id=order_id, customer=customer)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    
    order.status = 'cancelled'
    order.save()
    return JsonResponse({'message': 'Order status updated to cancelled'}, status=200)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def complete_order(request, order_id):
    customer = request.user.customer
    if not customer:
        return JsonResponse({'error': 'Only customers can update orders'}, status=403)
    try:
        order = Order.objects.get(id=order_id, customer=customer)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    
    order.status = 'complete'
    order.save()

    for item in order.order_items_rel.all():
        if item.type == 'digital':
            ownedProduct = OwnedProducts.objects.create(
                product=item.product,
                positions={'x': 0.0, 'y': 0.0, 'z': 0.0, 't': 0.0},
                rotation={'x': 0.0, 'y': 0.0, 'z': 0.0},
                scale={'x': 1.0, 'y': 1.0, 'z': 1.0},
                position_history=[],
                amount=item.quantity
            )
            if item.product.is_container:
                ContainerOwnedProducts.objects.create(product=ownedProduct)
            else:
                NonContainerOwnedProducts.objects.create(product=ownedProduct)

    return JsonResponse({'message': 'Order status updated to complete and products granted'}, status=200)
