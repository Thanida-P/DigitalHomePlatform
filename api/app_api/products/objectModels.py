import persistent

class Model3D(persistent.Persistent):
    def __init__(self, model_id, file, filename, textures=None):
        self.model_id = model_id
        self.file = file
        self.filename = filename
        self.textures = textures if textures else []
        
    def get_model_id(self):
        return self.model_id

    def get_filename(self):
        return self.filename

    def get_file(self):
        return self.file
    
    def get_textures(self):
        return self.textures

class Texture(persistent.Persistent):
    def __init__(self, texture_id, filename, file):
        self.texture_id = texture_id
        self.filename = filename
        self.file = file
        
    def get_filename(self):
        return self.filename
        
    def get_texture_id(self):
        return self.texture_id
    
    def get_file(self):
        return self.file
    
class DisplayScene(persistent.Persistent):
    def __init__(self, scene_id, file, filename):
        self.scene_id = scene_id
        self.file = file
        self.filename = filename
        
    def get_scene_id(self):
        return self.scene_id
    
    def get_file(self):
        return self.file
    
    def get_filename(self):
        return self.filename