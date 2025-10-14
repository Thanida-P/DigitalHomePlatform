from django.db import models
from django.contrib.gis.db import models as gis_models

SRID_3D = 4979

class PointZMField(gis_models.GeometryField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('srid', SRID_3D)
        kwargs.setdefault('dim', 4)
        super().__init__(*args, **kwargs)
    
    @property
    def geom_type(self):
        return 'POINTZM'

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    digital_price = models.DecimalField(max_digits=10, decimal_places=2)
    physical_price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50)
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
    positions = PointZMField()
    rotation = gis_models.PointField(srid=SRID_3D, dim=3)
    scale = models.FloatField(default=1.0)
    texture_id = models.IntegerField(null=True, blank=True)
    position_history = models.JSONField(default=list)
    
class ContainerOwnedProducts(models.Model):
    products = models.ManyToManyField(OwnedProducts, related_name="containers")
    contained_product = models.JSONField(default=list)  # List of product IDs contained

class NonContainerOwnedProducts(models.Model):
    product = models.OneToOneField(OwnedProducts, on_delete=models.CASCADE, related_name="non_container")
    composition = models.JSONField(default=list)  # List of product IDs that make up the composite