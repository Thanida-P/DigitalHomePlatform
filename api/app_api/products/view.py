from django.http import JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .product_services import *
from django.http import FileResponse
from zodb.zodb_management import *

# Add product
@csrf_exempt
@require_http_methods(["POST"])
def add_product(request):
    try:
        name = request.POST.get('name')
        description = request.POST.get('description')
        digital_price = float(request.POST.get('digital_price', 0))
        physical_price = float(request.POST.get('physical_price', 0))
        category = request.POST.get('category')
        image = request.FILES.get('image')
        stock = int(request.POST.get('stock', 0))
        model_files = request.FILES.get('model_file')
        scene_files = request.FILES.getlist('scene_files')
        texture_files = request.FILES.getlist('texture_files') if 'texture_files' in request.FILES else None

        if not all([name, description, category, image]) or (digital_price <= 0 and physical_price <= 0) or stock < 0 or not model_files:
            return JsonResponse({'error': 'Invalid input data'}, status=400)

        product = create_product(name, description, digital_price, physical_price, category, image, stock, model_files, scene_files, texture_files)
    
        return JsonResponse({'message': 'Product created successfully', 'product_id': product.id}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# testing endpoints for ZODB operations
@csrf_exempt
@require_http_methods(["POST"])
def add_3d_model(request):
    try:
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
        scene_file = request.FILES.get('scene_file')
        
        if not scene_file:
            return JsonResponse({'error': 'Display scene file is required'}, status=400)
        
        display_scene_id = create_display_scene(scene_file)
        
        return JsonResponse({'message': 'Display scene added successfully', 'display_scene_id': display_scene_id}, status=201)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_3d_model(request, model_id):
    try:
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
def get_texture(request, texture_id):
    try:
        response = fetch_texture(texture_id)
        if not response:
            return JsonResponse({'error': 'Texture not found'}, status=404)

        return JsonResponse({'texture_file': response}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def get_display_scene(request, display_scene_id):
    try:
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