from django.db import models
from django.contrib.gis.db import models as gis_models

SRID_3D = 4979

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    digital_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None)
    physical_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None)
    digital_available = models.BooleanField(default=False)
    physical_available = models.BooleanField(default=False)
    category = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    image = models.TextField()
    stock = models.IntegerField()
    reviews = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    model_id = models.IntegerField(null=True, blank=True)  # Link to 3D model
    display_scenes = models.JSONField(default=list)  # List of room scene IDs

    def __str__(self):
        return self.name
    
class OwnedProducts(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="owned_products")
    positions = models.JSONField(default=dict)  # {'x': float, 'y': float, 'z': float, 't': float}
    rotation = models.JSONField(default=dict)  # {'x': float, 'y': float, 'z': float}
    scale = models.JSONField(default=dict)     # {'x': float, 'y': float, 'z': float}
    texture_id = models.IntegerField(null=True, blank=True)
    position_history = models.JSONField(default=list)
    
class ContainerOwnedProducts(models.Model):
    products = models.ManyToManyField(OwnedProducts, related_name="containers")
    contained_product = models.JSONField(default=list)  # List of product IDs contained

class NonContainerOwnedProducts(models.Model):
    product = models.OneToOneField(OwnedProducts, on_delete=models.CASCADE, related_name="non_container")
    composition = models.JSONField(default=list)  # List of product IDs that make up the composite