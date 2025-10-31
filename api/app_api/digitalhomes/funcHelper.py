from django.db import connection
from zodb.zodb_management import *
from ZODB.blob import Blob
from app_api.digitalhomes.homeObject import Home3D
from app_api.digitalhomes.models import SRID_3D
from app_api.products.product_func import create_Texture, delete_texture
import trimesh
import transaction
import json


def load_mesh(file):
    try:
        mesh = trimesh.load(file, file_type='glb')
    except Exception:
        import tempfile, os
        with tempfile.NamedTemporaryFile(delete=False, suffix='.glb') as temp_file:
            for chunk in file.chunks():
                temp_file.write(chunk)
            temp_file.flush()
            mesh = trimesh.load(temp_file.name, file_type='glb')
        os.unlink(temp_file.name)

    if mesh.is_empty:
        raise ValueError("Loaded mesh is empty or invalid")

    # Apply scene graph transforms
    if isinstance(mesh, trimesh.Scene):
        mesh = mesh.dump(concatenate=True)

    return mesh

def getBoundaryFromMesh(file):
    mesh = load_mesh(file)
    bounding = {}
    bounding['min_x'] = float(mesh.bounds[0][0])
    bounding['max_x'] = float(mesh.bounds[1][0])
    bounding['min_y'] = float(mesh.bounds[0][1])
    bounding['max_y'] = float(mesh.bounds[1][1])
    bounding['min_z'] = float(mesh.bounds[0][2])
    bounding['max_z'] = float(mesh.bounds[1][2])
    return bounding

def create_spatial_instance(file):
    boundary = getBoundaryFromMesh(file)
    boundary_json = json.dumps(boundary)

    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO digitalhomes_spatialdata (positions, rotation, scale, boundary)
            VALUES (
                ST_GeomFromEWKT(%s),
                ST_GeomFromEWKT(%s),
                ST_GeomFromEWKT(%s),
                %s::jsonb
            )
            RETURNING id
        """, [
            f'SRID={SRID_3D};POINT ZM(0 0 0 0)',
            f'SRID={SRID_3D};POINT Z(0 0 0)',
            f'SRID={SRID_3D};POINT Z(1 1 1)',
            boundary_json
        ])
        spatial_id = cursor.fetchone()[0]
    return spatial_id

def get_home_object_id(root):
    if not root.digitalHomes:
        return 1
    existing_ids = [
        int(key)
        for key in root.digitalHomes.keys()
    ]
    return max(existing_ids) + 1

def get_model_id(root):
    if not root.homeObjectModels:
        return 1
    existing_ids = [
        int(key)
        for key in root.homeObjectModels.keys()
    ]
    return max(existing_ids) + 1

def create_3d_model(root, model_file, texture_files=None):
    try:
        model_id = get_model_id(root)
        filename = getattr(model_file, 'name', f'model_{model_id}.glb')
        
        file_content = model_file.read()
        blob = Blob()
        with blob.open('w') as f:
            if isinstance(file_content, (bytes, bytearray)):
                f.write(file_content)
            else:
                f.write(file_content.encode('latin-1'))

        texture_ids = []
        texture_id = None
        if texture_files:
            for tex in texture_files:
                if texture_id is None:
                    texture_id = create_Texture(tex, root)
                else:
                    texture_id = create_Texture(tex, root, texture_id)
                texture_ids.append(texture_id)

        root.homeObjectModels[model_id] = Home3D(
            id=model_id,
            file=blob,
            filename=filename,
            textures=texture_ids
        )
        transaction.commit()
        return model_id
    except Exception:
        try:
            transaction.abort()
        except Exception:
            pass
        raise
    
def fetch_home_model(home_id: int):
    _, root = get_connection()
    home_models = root.homeObjectModels
    if not home_models:
        return None
    if home_id not in home_models:
        return None
    return home_models[home_id]
        
def delete_home_3d_assets(root, home_id):
    try:
        home_models = root.homeObjectModels
        if not home_models or home_id not in home_models:
            return None

        model = home_models[home_id]

        for texture_id in model.get_textures():
            delete_texture(texture_id, root)

        del home_models[home_id]

    except Exception:
        try:
            transaction.abort()
        except Exception:
            pass
        raise
