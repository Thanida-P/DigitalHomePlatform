from .models import Product, Item
from .objectModels import *
from zodb.zodb_management import *
import base64

def create_product(name, description, digital_price, physical_price, category, image, product_type, stock, model_files, scene_files, digital_available, physical_available, is_container, texture_files=None):
    image_base64 = base64.b64encode(image.read()).decode('utf-8')
    model_id = create_3d_model(model_files, texture_files)
    display_scenes = []
    for scene_file in scene_files:
        scene_id = create_display_scene(scene_file)
        display_scenes.append(scene_id)
        
    item = Item(
        name=name,
        description=description,
        model_id=model_id,
        category=category,
        type=product_type,
        is_container=is_container
    )
    
    item.save()
       
    product = Product(
        item=item,
        digital_price=digital_price,
        physical_price=physical_price,
        image=image_base64,
        stock=stock,
        digital_available=digital_available,
        physical_available=physical_available,
        display_scenes=display_scenes
    )
    product.save()
    return product

def update_existing_product(product_id, name, description, digital_price, physical_price, category, image, product_type, stock, model_files, scene_files, digital_available, physical_available, is_container, texture_files):
    try:
        product = Product.objects.get(id=product_id)
        item = product.item
    except Product.DoesNotExist:
        raise ValueError("Product not found")

    if name:
        item.name = name
    if description:
        item.description = description
    if digital_price is not None:
        product.digital_price = digital_price
    if physical_price is not None:
        product.physical_price = physical_price
    if category:
        item.category = category
    if image:
        image_base64 = base64.b64encode(image.read()).decode('utf-8')
        product.image = image_base64
    if product_type:
        item.type = product_type
    if stock is not None and stock >= 0:
        product.stock = stock
    if digital_available is not None:
        product.digital_available = digital_available
    if physical_available is not None:
        product.physical_available = physical_available
    if model_files:
        update_3d_model(item.model_id, model_files, texture_files)
    if is_container is not None:
        item.is_container = is_container

    if scene_files:
        display_scene_ids = update_display_scene(product.display_scenes, scene_files)
        product.display_scenes = display_scene_ids

    item.save()
    product.save()
    return product

def delete_existing_product(product_id):
    try:
        product = Product.objects.get(id=product_id)
        item = product.item
        model_id = item.model_id

        if model_id is not None:
            delete_product_3d_assets(model_id, product.display_scenes)
        
        item.delete()
        product.delete()
        return True
    except Product.DoesNotExist:
        return False