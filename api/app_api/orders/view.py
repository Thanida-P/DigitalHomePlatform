from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem
from app_api.products.objectModels import OwnedItem, ContainerOwnedItem, NonContainerOwnedItem
from zodb.zodb_management import *
from app_api.orders.funcHelper import *
import datetime
import transaction

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
            product_id=item.product_id,
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
    connection, root = get_connection()
    try:
        customer = request.user.customer
        if not customer:
            return JsonResponse({'error': 'Only customers can view orders'}, status=403)
        orders_data = []
        for order in customer.orders.all().order_by('-created_at'):
            order_items = []
            for order_item in order.order_items_rel.all():
                product = root.products[order_item.product_id]
                item = product.item
                order_items.append({
                    'id': order_item.id,
                    'product_id': product.get_id(),
                    'product_name': item.get_name(),
                    'quantity': order_item.quantity,
                    'type': order_item.type,
                    'added_at': order_item.added_at.isoformat(),
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
    finally:
        connection.close()

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
    connection, root = get_connection()
    try:
        customer = request.user.customer
        if not customer:
            return JsonResponse({'error': 'Only customers can update orders'}, status=403)
        try:
            order = Order.objects.get(id=order_id, customer=customer)
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
        
        order.status = 'complete'
        order.save()

        for order_item in order.order_items_rel.all():
            if order_item.type == 'digital':
                for _ in range(order_item.quantity):
                    product = root.products[order_item.product_id]
                    item = product.item
                    spatial_id = create_spatial_instance()
                    current_time = datetime.datetime.utcnow()
                    if item.is_container:
                        container_id = get_container_owned_item_id(root)
                        categorizedItem = ContainerOwnedItem(
                            id=container_id,
                            name=item.get_name(),
                            description=item.get_description(),
                            model_id=item.get_model_id(),
                            category=item.get_category(),
                            type=item.get_type(),
                            is_container=item.is_container,
                            spatial_id=spatial_id,
                            texture_id=None,
                            contained_item=[],
                            created_at=current_time
                        )
                        root.containerOwnedItems[container_id] = categorizedItem
                    else:
                        noncontainer_id = get_noncontainer_owned_item_id(root)
                        categorizedItem = NonContainerOwnedItem(
                            id=noncontainer_id,
                            name=item.get_name(),
                            description=item.get_description(),
                            model_id=item.get_model_id(),
                            category=item.get_category(),
                            type=item.get_type(),
                            is_container=item.is_container,
                            spatial_id=spatial_id,
                            texture_id=None,
                            composition=[],
                            created_at=current_time
                        )
                        root.nonContainerOwnedItems[noncontainer_id] = categorizedItem
                    transaction.commit()
                    customer.owned_digital_products.append(categorizedItem.get_id())
        customer.save()

        return JsonResponse({'message': 'Order status updated to complete and products granted'}, status=200)
    finally:
        connection.close()
