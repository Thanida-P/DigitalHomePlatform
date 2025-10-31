from django.http import FileResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from zodb.zodb_management import *
from app_api.digitalhomes.homeObject import HomeObject
from app_api.digitalhomes.models import SpatialData
from app_api.digitalhomes.funcHelper import *
from app_api.products.product_func import fetch_texture
from datetime import datetime
import transaction

@login_required
@require_http_methods(["GET"])
def list_available_items(request):
    connection, root = get_connection()
    try:
        customer = request.user.customer
        available_items = []
        for entry in customer.owned_digital_products:
            item_id = entry.get('id')
            is_container = entry.get('is_container', False)
            if not item_id:
                continue
            try:
                if is_container:
                    item = root.containerOwnedItems[item_id]
                else:
                    item = root.nonContainerOwnedItems[item_id]
                available_items.append({
                    'id': item.get_id(),
                    'name': item.get_name(),
                    'description': item.get_description(),
                    'model_id': item.get_model_id(),
                    'category': item.get_category(),
                    'type': item.get_type(),
                    'is_container': is_container,
                    'created_at': item.created_at.isoformat(),
                    
                })
            except (KeyError, TypeError):
                continue
        return JsonResponse({'available_items': available_items}, status=200)
    finally:
        connection.close()

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def get_specific_item(request):
    connection, root = get_connection()
    try:
        customer = request.user.customer
        
        # Retrieve values from query parameters
        item_id = request.POST.get('item_id')
        is_container = request.POST.get('is_container', 'false').lower() == 'true'

        if not item_id:
            return JsonResponse({'error': 'item_id is required'}, status=400)

        if int(item_id) not in [item.get('id') for item in customer.owned_digital_products]:
            return JsonResponse({'error': 'You do not own this item'}, status=403)
        
        try:
            if is_container:
                item = root.containerOwnedItems[int(item_id)]
            else:
                item = root.nonContainerOwnedItems[int(item_id)]
        except (KeyError, TypeError):
            return JsonResponse({'error': 'Item not found'}, status=404)
        
        item_data = {
            'id': item.get_id(),
            'name': item.get_name(),
            'description': item.get_description(),
            'model_id': item.get_model_id(),
            'category': item.get_category(),
            'type': item.get_type(),
            'is_container': is_container,
            'created_at': item.created_at.isoformat(),
        }
        return JsonResponse({'item': item_data}, status=200)
    finally:
        connection.close()
        
@csrf_exempt
@login_required
@require_http_methods(["POST"])
def add_digital_home(request):
    connection, root = get_connection()
    try:
        customer = request.user.customer

        if not customer:
            return JsonResponse({'error': 'Only customers can manage digital homes'}, status=403)

        name = request.POST.get('name')
        model_files = request.FILES.get('model_file')
        texture_files = request.FILES.getlist('texture_files')

        if not name or not model_files:
            return JsonResponse({'error': 'Name and model_file are required'}, status=400)
        
        home_id = get_home_object_id(root)
        model_id = create_3d_model(root, model_files, texture_files)
        spatialData_id = create_spatial_instance(model_files)
        deployedItems = []
        created_at = datetime.now()
        root.digitalHomes[home_id] = HomeObject(
            id=home_id,
            name=name,
            home_id=model_id,
            deployedItems=deployedItems,
            spatialData_id=spatialData_id,
            created_at=created_at
        )
        customer.digital_home.append(home_id)
        customer.save()
        transaction.commit()
        return JsonResponse({'message': 'Digital home added successfully'}, status=201)
    finally:
        connection.close()
        
@login_required
@require_http_methods(["GET"])
def get_digital_homes(request):
    connection, root = get_connection()
    try:
        customer = request.user.customer

        if not customer:
            return JsonResponse({'error': 'Only customers can view digital homes'}, status=403)

        digital_homes = []
        for home_id in customer.digital_home:
            try:
                home = root.digitalHomes[home_id]
                digital_homes.append({
                    'id': home.get_id(),
                    'name': home.get_name(),
                    'home_id': home.get_home_id(),
                    'deployedItems': home.get_deployedItems(),
                    'spatialData_id': home.spatialData_id,
                    'created_at': home.get_created_at().isoformat(),
                    'updated_at': home.get_updated_at().isoformat(),
                })
            except (KeyError, TypeError):
                continue
        return JsonResponse({'digital_homes': digital_homes}, status=200)
    finally:
        connection.close()
        
@login_required
@require_http_methods(["GET"])
def get_digital_home(request, id):
    connection, root = get_connection()
    try:
        customer = request.user.customer

        if not customer:
            return JsonResponse({'error': 'Only customers can view digital homes'}, status=403)

        if int(id) not in customer.digital_home:
            return JsonResponse({'error': 'You do not own this digital home'}, status=403)

        try:
            home = root.digitalHomes[int(id)]
            home_data = {
                'id': home.get_id(),
                'name': home.get_name(),
                'home_id': home.get_home_id(),
                'deployedItems': home.get_deployedItems(),
                'spatialData_id': home.spatialData_id,
                'created_at': home.get_created_at().isoformat(),
                'updated_at': home.get_updated_at().isoformat(),
            }
            return JsonResponse({'digital_home': home_data}, status=200)
        except (KeyError, TypeError):
            return JsonResponse({'error': 'Digital home not found'}, status=404)
    finally:
        connection.close()
        
@require_http_methods(["GET"])
@login_required
def get_home_model(request, home_id):
    try:
        model = fetch_home_model(home_id)
        if not model:
            print("Model not found")
            return JsonResponse({'error': 'Model not found'}, status=404)

        blob = model.get_file()
        if blob is None:
            return JsonResponse({'error': 'Model file not found'}, status=404)

        response = FileResponse(blob.open('r'), as_attachment=True, filename=model.get_filename())
        return response
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@require_http_methods(["GET"])
@login_required
def get_textures(request, home_id):
    try:
        model = fetch_home_model(home_id)
        if not model:
            return JsonResponse({'error': 'Model not found'}, status=404)

        texture_files = []
        for tex_id in model.get_textures():
            texture = fetch_texture(tex_id)
            texture_files.append({'texture_id': tex_id, 'file': texture})

        return JsonResponse({'textures': texture_files}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def delete_digital_home(request, id):
    connection, root = get_connection()
    try:
        customer = request.user.customer

        if not customer:
            return JsonResponse({'error': 'Only customers can manage digital homes'}, status=403)

        if int(id) not in customer.digital_home:
            return JsonResponse({'error': 'You do not own this digital home'}, status=403)

        try:
            digital_home = root.digitalHomes[int(id)]
            home_id = digital_home.get_id()
            if home_id is not None:
                delete_home_3d_assets(root, home_id)
            
            del root.digitalHomes[int(id)]
            customer.digital_home.remove(int(id))
            customer.save()
            transaction.commit()
            return JsonResponse({'message': 'Digital home deleted successfully'}, status=200)
        except (KeyError, TypeError):
            return JsonResponse({'error': 'Digital home not found'}, status=404)
    finally:
        connection.close()