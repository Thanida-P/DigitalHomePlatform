import os
import ZODB
import ZODB.FileStorage
import transaction
from persistent.mapping import PersistentMapping
from ZODB.blob import Blob, BlobStorage
from app_api.products.objectModels import *
import base64
import BTrees.OOBTree

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZODB_DIR = os.path.join(BASE_DIR, 'zodb_data')
BLOB_DIR = os.path.join(ZODB_DIR, 'blobs')
os.makedirs(ZODB_DIR, exist_ok=True)
os.makedirs(BLOB_DIR, exist_ok=True)
ZODB_FILE = os.path.join(ZODB_DIR, 'zodb.fs')

file_storage = ZODB.FileStorage.FileStorage(ZODB_FILE)
storage = BlobStorage(BLOB_DIR, file_storage)
db = ZODB.DB(storage)

def get_connection():
    """Get a fresh connection and ensure root is initialized"""
    connection = db.open()
    root = connection.root()
    
    # Initialize root attributes if they don't exist
    if not hasattr(root, "objectModels"):
        root.objectModels = BTrees.OOBTree.BTree()
    if not hasattr(root, "textures"):
        root.textures = BTrees.OOBTree.BTree()
    if not hasattr(root, "displayScenes"):
        root.displayScenes = BTrees.OOBTree.BTree()
    
    return connection, root

def direct_create_Texture(texture_file):
    connection, root = get_connection()
    try:
        texture_id = len(root.textures) + 1
        filename = getattr(texture_file, 'name', f'texture_{texture_id}.png')
        file_base64 = base64.b64encode(texture_file.read()).decode('utf-8')

        root.textures[f'texture_{texture_id}'] = Texture(
            texture_id=texture_id,
            filename=filename,
            file=file_base64
        )
        transaction.commit()
        return texture_id
    except Exception:
        # Ensure any joined transaction is aborted so the connection can be closed
        try:
            transaction.abort()
        except Exception:
            pass
        raise
    finally:
        connection.close()

def get_next_texture_id(root):
    if not root.textures:
        return 1
    existing_ids = [
        int(key.split('_')[-1]) 
        for key in root.textures.keys()
        if key.startswith('texture_')
    ]
    return max(existing_ids) + 1

def create_Texture(texture_file, root, texture_id=None):
    if texture_id is None:
        texture_id = get_next_texture_id(root)
    else:
        texture_id += 1

    filename = getattr(texture_file, 'name', f'texture_{texture_id}.png')
    file_base64 = base64.b64encode(texture_file.read()).decode('utf-8')

    root.textures[f'texture_{texture_id}'] = Texture(
        texture_id=texture_id,
        filename=filename,
        file=file_base64
    )

    return texture_id

def delete_texture(texture_id, root):
    textures = root.textures
    if not textures or f'texture_{texture_id}' not in textures:
        raise ValueError("Texture not found")
    
    del textures[f'texture_{texture_id}']
    
def get_model_id(root):
    if not root.objectModels:
        return 1
    existing_ids = [
        int(key.split('_')[-1]) 
        for key in root.objectModels.keys()
        if key.startswith('model_')
    ]
    return max(existing_ids) + 1

def create_3d_model(model_file, texture_files=None):
    connection, root = get_connection()
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

        root.objectModels[f'model_{model_id}'] = Model3D(
            model_id=model_id,
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
    finally:
        connection.close()

def update_3d_model(model_id, model_file=None, texture_files=None):
    connection, root = get_connection()
    try:
        object_models = root.objectModels
        if not object_models or f'model_{model_id}' not in object_models:
            raise ValueError("3D Model not found")

        model = object_models[f'model_{model_id}']

        if model_file:
            filename = getattr(model_file, 'name', f'model_{model_id}.glb')
            file_content = model_file.read()
            blob = Blob()
            with blob.open('w') as f:
                if isinstance(file_content, (bytes, bytearray)):
                    f.write(file_content)
                else:
                    f.write(file_content.encode('latin-1'))
            model.file = blob
            model.filename = filename

        if texture_files:
            for tex_id in model.get_textures():
                delete_texture(tex_id, root)
            
            model.textures = []
            for tex in texture_files:
                new_tex_id = create_Texture(tex, root)
                model.textures.append(new_tex_id)

        transaction.commit()
    except Exception:
        try:
            transaction.abort()
        except Exception:
            pass
        raise
    finally:
        connection.close()
        
def get_next_display_scene_id(root):
    if not root.displayScenes:
        return 1
    existing_ids = [
        int(key.split('_')[-1]) 
        for key in root.displayScenes.keys()
        if key.startswith('display_scene_')
    ]
    return max(existing_ids) + 1
        
def create_display_scene(model_file):
    connection, root = get_connection()
    try:
        display_scene_id = get_next_display_scene_id(root)
        filename = getattr(model_file, 'name', f'model_{display_scene_id}.glb')
        
        file_content = model_file.read()
        blob = Blob()
        with blob.open('w') as f:
            if isinstance(file_content, (bytes, bytearray)):
                f.write(file_content)
            else:
                f.write(file_content.encode('latin-1'))

        root.displayScenes[f'display_scene_{display_scene_id}'] = DisplayScene(
            scene_id=display_scene_id,
            file=blob,
            filename=filename
        )
        transaction.commit()
        return display_scene_id
    except Exception:
        try:
            transaction.abort()
        except Exception:
            pass
        raise
    finally:
        connection.close()
        
def delete_display_scene(display_scene_id, root):
    display_scenes = root.displayScenes
    if not display_scenes or f'display_scene_{display_scene_id}' not in display_scenes:
        raise ValueError("Display Scene not found")
    
    del display_scenes[f'display_scene_{display_scene_id}']
        
def update_display_scene(display_scene_ids, model_files):
    connection, root = get_connection()
    try:
        display_scenes = root.displayScenes
        if not display_scenes:
            raise ValueError("No Display Scenes found")
        
        for ds_id in display_scene_ids:
            if f'display_scene_{ds_id}' not in display_scenes:
                raise ValueError(f"Display Scene {ds_id} not found")
            delete_display_scene(ds_id, root)

        new_display_scene_ids = []
        for model_file in model_files:
            display_scene_id = get_next_display_scene_id(root)
            filename = getattr(model_file, 'name', f'model_{display_scene_id}.glb')
            
            file_content = model_file.read()
            blob = Blob()
            with blob.open('w') as f:
                if isinstance(file_content, (bytes, bytearray)):
                    f.write(file_content)
                else:
                    f.write(file_content.encode('latin-1'))

            root.displayScenes[f'display_scene_{display_scene_id}'] = DisplayScene(
                scene_id=display_scene_id,
                file=blob,
                filename=filename
            )
            new_display_scene_ids.append(display_scene_id)
        
        transaction.commit()
        return new_display_scene_ids
    except Exception:
        try:
            transaction.abort()
        except Exception:
            pass
        raise
    finally:
        connection.close()
        
def delete_product_3d_assets(model_id, display_scene_ids):
    connection, root = get_connection()
    try:
        object_models = root.objectModels
        if not object_models or f'model_{model_id}' not in object_models:
            return 

        model = object_models[f'model_{model_id}']
        
        for texture_id in model.get_textures():
            delete_texture(texture_id, root)
        
        del object_models[f'model_{model_id}']
        
        display_scenes = root.displayScenes
        if display_scenes:
            for ds_id in display_scene_ids:
                if f'display_scene_{ds_id}' in display_scenes:
                    delete_display_scene(ds_id, root)
        
        transaction.commit()
    except Exception:
        try:
            transaction.abort()
        except Exception:
            pass
        raise
    finally:
        connection.close()

def fetch_3d_model(model_id: int):
    connection, root = get_connection()
    object_models = root.objectModels
    if not object_models:
        return None
    return object_models[f"model_{model_id}"]

def fetch_display_scene(display_scene_id: int):
    connection, root = get_connection()
    display_scenes = root.displayScenes
    if not display_scenes:
        return None
    return display_scenes[f"display_scene_{display_scene_id}"]

def fetch_texture(texture_id: int):
    connection, root = get_connection()
    textures = root.textures
    if not textures:
        return None
    return textures[f"texture_{texture_id}"].get_file()

def close_zodb():
    db.close()
    storage.close()
    file_storage.close()