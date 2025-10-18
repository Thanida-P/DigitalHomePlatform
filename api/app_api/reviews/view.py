from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Review
from .funcHelper import *
import base64

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def add_review(request):
    customer = request.user.customer

    if not customer:
        return JsonResponse({'error': 'Only customers can manage reviews'}, status=403)

    product_id = request.POST.get('product_id')
    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '')
    image = request.FILES.get('image')

    if not product_id:
        return JsonResponse({'error': 'Product ID is required'}, status=400)
    
    if not rating:
        return JsonResponse({'error': 'Rating is required'}, status=400)
    
    if Review.objects.filter(product_id=product_id, customer=customer).first():
        return JsonResponse({'error': 'You have already reviewed this product'}, status=400)

    if image:
        image_base64 = base64.b64encode(image.read()).decode('utf-8')
    else:
        image_base64 = None

    review = Review.objects.create(
        product_id=product_id,
        customer=customer,
        rating=rating,
        comment=comment,
        image=image_base64
    )
    
    product = review.product
    product.reviews.append(review.id)
    update_average_rating(product)
    product.save()

    return JsonResponse({'message': 'Review added successfully'}, status=201)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def edit_review(request):
    customer = request.user.customer

    if not customer:
        return JsonResponse({'error': 'Only customers can manage reviews'}, status=403)

    review_id = request.POST.get('review_id')
    rating = request.POST.get('rating')
    comment = request.POST.get('comment')
    image_file = request.FILES.get('image')
    image_key_present = 'image' in request.POST
    
    if not review_id:
        return JsonResponse({'error': 'Review ID is required'}, status=400)
    
    try:
        review = Review.objects.get(id=review_id, customer=customer)
    except Review.DoesNotExist:
        return JsonResponse({'error': 'Review not found'}, status=404)
    
    product = review.product
    if rating:
        review.rating = rating
    if comment is not None:
        review.comment = comment

    if image_file:
        if hasattr(image_file, 'size') and image_file.size == 0:
            review.image = None
        else:
            image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
            review.image = image_base64
    elif image_key_present:
        review.image = None

    review.save()
    update_average_rating(product)
    
    return JsonResponse({'message': 'Review updated successfully'}, status=200)

@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def delete_review(request, review_id):
    customer = request.user.customer

    if not customer:
        return JsonResponse({'error': 'Only customers can manage reviews'}, status=403)
    
    if not review_id:
        return JsonResponse({'error': 'Review ID is required'}, status=400)
    
    try:
        review = Review.objects.get(id=review_id, customer=customer)
    except Review.DoesNotExist:
        return JsonResponse({'error': 'Review not found'}, status=404)
    
    product = review.product
    review.delete()
    
    if review_id in product.reviews:
        product.reviews.remove(review_id)
    
    update_average_rating(product)
    product.save()
    
    return JsonResponse({'message': 'Review deleted successfully'}, status=200)

@login_required
@require_http_methods(["GET"])
def get_reviews_for_product(request, product_id):
    try:
        reviews = Review.objects.filter(product_id=product_id)
        reviews_data = []
        for review in reviews:
            reviews_data.append({
                'id': review.id,
                'customer_id': review.customer.id,
                'rating': review.rating,
                'comment': review.comment,
                'image': review.image,
                'created_at': review.created_at,
                'updated_at': review.updated_at
            })
        return JsonResponse({'reviews': reviews_data}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@login_required
@require_http_methods(["GET"])
def get_reviews_by_customer(request):
    customer = request.user.customer

    if not customer:
        return JsonResponse({'error': 'Only customers can manage reviews'}, status=403)
    
    try:
        reviews = Review.objects.filter(customer=customer)
        reviews_data = []
        for review in reviews:
            reviews_data.append({
                'id': review.id,
                'product_id': review.product.id,
                'rating': review.rating,
                'comment': review.comment,
                'image': review.image,
                'created_at': review.created_at,
                'updated_at': review.updated_at
            })
        return JsonResponse({'reviews': reviews_data}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)