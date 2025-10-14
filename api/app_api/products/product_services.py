from .models import Product, OwnedProducts, ContainerOwnedProducts, NonContainerOwnedProducts 
from .objectModels import *
from zodb.zodb_management import *
import base64

def create_product(name, description, digital_price, physical_price, category, image, stock, model_files, scene_files, texture_files=None):
    image_base64 = base64.b64encode(image.read()).decode('utf-8')
    model_id = create_3d_model(model_files, texture_files)
    display_scenes = []
    for scene_file in scene_files:
        scene_id = create_display_scene(scene_file)
        display_scenes.append(scene_id)
       
    product = Product(
        name=name,
        description=description,
        digital_price=digital_price,
        physical_price=physical_price,
        category=category,
        image=image_base64,
        stock=stock,
        model_id=model_id,
        display_scenes=display_scenes if display_scenes else []
    )
    product.save()
    return product