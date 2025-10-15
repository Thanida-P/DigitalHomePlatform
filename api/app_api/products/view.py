from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import QueryDict
from django.http import FileResponse

from .product_func import *

# Add product
@csrf_exempt
@require_http_methods(["POST"])
def add_product(request):
    try:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)

        name = request.POST.get('name')
        description = request.POST.get('description')
        digital_price = float(request.POST.get('digital_price', 0))
        physical_price = float(request.POST.get('physical_price', 0))
        category = request.POST.get('category')
        image = request.FILES.get('image')
        product_type = request.POST.get('product_type')
        stock = int(request.POST.get('stock', 0))
        model_files = request.FILES.get('model_file')
        scene_files = request.FILES.getlist('scene_files')
        texture_files = request.FILES.getlist('texture_files')

        if not all([name, description, category, product_type, image]) or stock < 0 or not model_files:
            return JsonResponse({'error': 'Invalid input data'}, status=400)

        product = create_product(name, description, digital_price, physical_price, category, image, product_type, stock, model_files, scene_files, texture_files)

        return JsonResponse({'message': 'Product created successfully', 'product_id': product.id}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def update_product(request):
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    product_id = request.POST.get('product_id')
    name = request.POST.get('name')
    description = request.POST.get('description')
    digital_price = float(request.POST.get('digital_price', 0))
    physical_price = float(request.POST.get('physical_price', 0))
    category = request.POST.get('category')
    image = request.FILES.get('image')
    product_type = request.POST.get('product_type')
    stock = int(request.POST.get('stock', 0))
    model_files = request.FILES.get('model_file')
    scene_files = request.FILES.getlist('scene_files')
    texture_files = request.FILES.getlist('texture_files')

    if not all([name, description, category, product_type, image]) or stock < 0 or not model_files:
        return JsonResponse({'error': 'Invalid input data'}, status=400)

    product = update_existing_product(product_id, name, description, digital_price, physical_price, category, image, product_type, stock, model_files, scene_files, texture_files)
    return JsonResponse({'message': 'Product updated successfully', 'product_id': product.id}, status=200)

# @require_http_methods(["GET"])
# def get_products(request, search_query=None, category=None):
#     try:
#         products = Product.objects.all()
#         product_list = []
#         for product in products:
#             product_data = {
#                 'id': product.id,
#                 'name': product.name,
#                 'digital_price': str(product.digital_price),
#                 'physical_price': str(product.physical_price),
#                 'category': product.category,
#                 'image': product.image,
#                 'stock': product.stock,
#                 'reviews': product.reviews,
#                 'created_at': product.created_at,
#                 'updated_at': product.updated_at,
#                 'model_id': product.model_id,
#                 'display_scenes_ids': product.display_scenes,
#                 'texture_id': product.texture_id if hasattr(product, 'texture_id') else None
#             }
#             product_list.append(product_data)
#         return JsonResponse({'products': product_list}, status=200)
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_product_detail(request, product_id):
    try:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        if not product_id:
            return JsonResponse({'error': 'Product ID is required'}, status=400)
        product = Product.objects.get(id=product_id)
        
        product_data = {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'digital_price': str(product.digital_price),
            'physical_price': str(product.physical_price),
            'category': product.category,
            'type': product.type,
            'image': product.image,
            'stock': product.stock,
            'reviews': product.reviews,
            'created_at': product.created_at,
            'updated_at': product.updated_at,
            'model_id': product.model_id,
            'display_scenes_ids': product.display_scenes,
            'texture_id': product.texture_id if hasattr(product, 'texture_id') else None
        }
        return JsonResponse({'product': product_data}, status=200)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_product(request, product_id):
    try:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        if not product_id:
            return JsonResponse({'error': 'Product ID is required'}, status=400)
        
        delete_existing_product(product_id)
        
        return JsonResponse({'message': 'Product deleted successfully'}, status=200)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
    
@require_http_methods(["GET"])
def get_3d_model(request, model_id):
    try:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        model = fetch_3d_model(model_id)
        if not model:
            return JsonResponse({'error': 'Model not found'}, status=404)

        blob = model.get_file()
        if blob is None:
            return JsonResponse({'error': 'Model file not found'}, status=404)

        response = FileResponse(blob.open('r'), as_attachment=True, filename=model.get_filename())
        return response
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@require_http_methods(["GET"])
def get_display_scene(request, display_scene_id):
    try:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        scene = fetch_display_scene(display_scene_id)
        if not scene:
            return JsonResponse({'error': 'Scene not found'}, status=404)

        blob = scene.get_file()
        if blob is None:
            return JsonResponse({'error': 'Scene file not found'}, status=404)

        response = FileResponse(blob.open('r'), as_attachment=True, filename=scene.get_filename())
        return response
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@require_http_methods(["GET"])
def get_textures(request, model_id):
    try:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        model = fetch_3d_model(model_id)
        if not model:
            return JsonResponse({'error': 'Model not found'}, status=404)

        texture_files = []
        for tex_id in model.get_textures():
            texture = fetch_texture(tex_id)
            texture_files.append({'texture_id': tex_id, 'file': texture})

        return JsonResponse({'textures': texture_files}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
# testing endpoints for ZODB operations
@csrf_exempt
@require_http_methods(["POST"])
def add_3d_model(request):
    try:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        model_file = request.FILES.get('model_file')
        texture_files = request.FILES.getlist('texture_files')
        
        if not model_file:
            return JsonResponse({'error': 'Model file is required'}, status=400)
        
        model_id = create_3d_model(model_file, texture_files)
        
        return JsonResponse({'message': '3D model added successfully', 'model_id': model_id}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@require_http_methods(["POST"])
def add_texture(request):
    try:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        texture_file = request.FILES.get('texture_file')
        
        if not texture_file:
            return JsonResponse({'error': 'Texture file is required'}, status=400)
        
        texture_id = direct_create_Texture(texture_file)
        
        return JsonResponse({'message': 'Texture added successfully', 'texture_id': texture_id}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@require_http_methods(["POST"])
def add_display_scene(request):
    try:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        scene_file = request.FILES.get('scene_file')
        
        if not scene_file:
            return JsonResponse({'error': 'Display scene file is required'}, status=400)
        
        display_scene_id = create_display_scene(scene_file)
        
        return JsonResponse({'message': 'Display scene added successfully', 'display_scene_id': display_scene_id}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@require_http_methods(["GET"])
def get_texture(request, texture_id):
    try:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        response = fetch_texture(texture_id)
        if not response:
            return JsonResponse({'error': 'Texture not found'}, status=404)

        return JsonResponse({'texture_file': response}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@require_http_methods(["GET"])
def get_display_scenes(request, product_id):
    try:
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        product = Product.objects.get(id=product_id)
        if not product:
            return JsonResponse({'error': 'Product not found'}, status=404)

        scenes = []
        for scene_id in product.display_scenes:
            scene = fetch_display_scene(scene_id)
            if scene:
                scenes.append({
                    'scene_id': scene_id,
                    'filename': scene.get_filename()
                })
        return JsonResponse({'display_scenes': scenes}, status=200)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)