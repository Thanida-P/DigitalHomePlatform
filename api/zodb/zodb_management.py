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
    finally:
        connection.close()

def create_Texture(texture_file, root):
    texture_id = len(root.textures) + 1
    filename = getattr(texture_file, 'name', f'texture_{texture_id}.png')
    file_base64 = base64.b64encode(texture_file.read()).decode('utf-8')

    root.textures[f'texture_{texture_id}'] = Texture(
        texture_id=texture_id,
        filename=filename,
        file=file_base64
    )
    return texture_id

def create_3d_model(model_file, texture_files=None):
    connection, root = get_connection()
    try:
        model_id = len(root.objectModels) + 1
        filename = getattr(model_file, 'name', f'model_{model_id}.glb')
        
        file_content = model_file.read()
        blob = Blob()
        with blob.open('w') as f:
            if isinstance(file_content, (bytes, bytearray)):
                f.write(file_content)
            else:
                f.write(file_content.encode('latin-1'))

        texture_ids = []
        if texture_files:
            for tex in texture_files:
                texture_ids.append(create_Texture(tex, root))

        root.objectModels[f'model_{model_id}'] = Model3D(
            model_id=model_id,
            file=blob,
            filename=filename,
            textures=texture_ids
        )
        transaction.commit()
        return model_id
    finally:
        connection.close()
        
def create_display_scene(model_file):
    connection, root = get_connection()
    try:
        display_scene_id = len(root.displayScenes) + 1
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