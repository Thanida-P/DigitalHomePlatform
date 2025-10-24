from .models import Review
from django.db.models import Avg

def update_average_rating(product):
    avg = Review.objects.filter(product=product).aggregate(avg=Avg('rating'))['avg']
    if avg is None:
        product.rating = 0.0
    else:
        avg = round(max(0.0, min(5.0, float(avg))), 2)
        product.rating = avg
    product.save(update_fields=['rating'])
