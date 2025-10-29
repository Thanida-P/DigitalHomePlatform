from django.db import models

class Item(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    model_id = models.IntegerField(null=True, blank=True)  # Link to 3D model
    is_container = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.CharField(max_length=50)
    type = models.CharField(max_length=50)

class Product(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="item_products")
    digital_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None)
    physical_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=None)
    digital_available = models.BooleanField(default=False)
    physical_available = models.BooleanField(default=False)
    image = models.TextField()
    stock = models.IntegerField()
    reviews = models.JSONField(default=list)
    rating = models.FloatField(default=0.0)
    display_scenes = models.JSONField(default=list)  # List of room scene IDs
    
class OwnedItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="owned_items")    
    positions = models.JSONField(default=dict)  # {'x': float, 'y': float, 'z': float, 't': float}
    rotation = models.JSONField(default=dict)  # {'x': float, 'y': float, 'z': float}
    scale = models.JSONField(default=dict)     # {'x': float, 'y': float, 'z': float}
    texture_id = models.IntegerField(null=True, blank=True)
    position_history = models.JSONField(default=list)
    
class ContainerOwnedItem(models.Model):
    item = models.OneToOneField(OwnedItem, related_name="containers", on_delete=models.CASCADE)
    contained_item = models.JSONField(default=list)  # List of item IDs contained

class NonContainerOwnedItem(models.Model):
    item = models.OneToOneField(OwnedItem, on_delete=models.CASCADE, related_name="non_container")
    composition = models.JSONField(default=list)  # List of item IDs that make up the composite