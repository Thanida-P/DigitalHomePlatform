import reflex as rx 
from ...template import template 
from reflex.components.component import NoSSRComponent 
from typing import Any, Dict, List 
import urllib.parse 
from ...state import ModelState, RoomSceneState, ModalState
from ...config import API_BASE_URL
from ...state import AuthState

class ThreeFiberCanvas(NoSSRComponent):
    library = "@react-three/fiber" 
    tag = "Canvas"


class ModelViewer3D(rx.Component):
   
    tag = "ModelViewer3DComponent"

    url: rx.Var[str] = ""
    position: rx.Var[List[float]] = [0, 0, 0]
    scale: rx.Var[float] = 1.0
    rotation: rx.Var[List[float]] = [0, 0, 0]
    color: rx.Var[str] = "#ff69b4"  # default chair color

    def add_imports(self) -> Dict[str, Any]:
        return {"react": ["useRef", "useEffect", "useState"]}

    def add_custom_code(self) -> List[str]:
        return [
            """
            function ModelViewer3DComponent({ url, color="#ff69b4", position=[0,0,0], scale=1, rotation=[0,0,0] }) {
                const [model, setModel] = useState(null);
                const modelRef = useRef();

                useEffect(() => {
                    if (!url) return;
                    let cancelled = false;

                    (async () => {
                        const mod = await import('three/examples/jsm/loaders/GLTFLoader.js');
                        const { GLTFLoader } = mod;
                        const loader = new GLTFLoader();

                        loader.load(
                            url,
                            (gltf) => {
                                if (!cancelled) {
                                    // Traverse only the chair meshes
                                    gltf.scene.traverse((child) => {
                                        if (child.isMesh && child.name.toLowerCase().includes("chair")) {
                                            child.material.color.set(color);
                                        }
                                    });
                                    setModel(gltf.scene);
                                }
                            },
                            undefined,
                            (err) => console.error("Error loading model:", err)
                        );
                    })();

                    return () => { cancelled = true; };
                }, [url, color]);

                if (!model) {
                    return (
                        <mesh position={position}>
                            <boxGeometry args={[1, 1, 1]} />
                            <meshStandardMaterial wireframe color="gray" />
                        </mesh>
                    );
                }

                return (
                    <primitive
                        ref={modelRef}
                        object={model}
                        position={position}
                        scale={scale}
                        rotation={rotation}
                        dispose={null}
                    />
                );
            }
            """
        ]

    
class SceneWithLighting(rx.Component):
    tag = "SceneWithLightingComponent"

    def add_custom_code(self) -> List[str]:
        return [
            """
            function SceneWithLightingComponent({ children }) {
                return (
                    <>
                        <ambientLight intensity={0.5} />
                        <directionalLight position={[5, 5, 5]} intensity={1} />
                        {children}
                    </>
                );
            }
            """
        ]
    
class CameraControls(rx.Component):
    tag = "CameraControls3DComponent"

    def add_imports(self) -> Dict[str, Any]:
        return {"react": ["useRef", "useEffect"], "@react-three/fiber": ["useThree"]}

    def add_custom_code(self) -> List[str]:
        return [
            """
            function CameraControls3DComponent() {
                const { camera, gl } = useThree();
                const controlsRef = useRef();

                useEffect(() => {
                    let controls;
                    (async () => {
                        const mod = await import('three/examples/jsm/controls/OrbitControls.js');
                        const { OrbitControls } = mod;
                        controls = new OrbitControls(camera, gl.domElement);
                    })();
                    return () => controls && controls.dispose();
                }, [camera, gl]);

                return null;
            }
            """
        ]

class ProductDetailState(rx.State):
    model_file: bytes = ""
    model_filename: str = ""       
    scene_file: bytes = b""      
    scene_filename: str = ""

    product_id: str = ""
    product_data: dict = {}
    model_url: str = ""

    display_scene_urls: list[str] = []
    display_scenes_loaded: bool = False

    is_loading: bool = False
    has_loaded: bool = False

    async def on_load(self):
        """This runs when the page loads"""

        if self.is_loading or self.has_loaded:
            print("⏭️ Already loading or loaded, skipping...")
            return
        
        self.is_loading = True

        self.product_id = self.router.page.params.get("product_Id", "")

        print(f"🔍 Product ID from URL: {self.product_id}")  
        
        if self.product_id:
            await self.fetch_product_data(self.product_id)

        self.is_loading = False
        self.has_loaded = True

    async def fetch_product_data(self, product_id: str):
        """Fetch product data using the ID"""
        import httpx
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        
        try:
         
            url = f"{API_BASE_URL}/products/get_product_detail/{product_id}/"
            print(f"📡 Fetching from: {url}")  
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, cookies=cookies_dict)
            
            print(f"📊 Response status: {response.status_code}")  
            
            if response.status_code == 200:
                data = response.json()
                self.product_data = data.get('product', {})
                print(f"✅ Fetched product: {self.product_data.get('name', 'N/A')}")

                model_id = self.product_data.get('model_id')
                if model_id:
                    await self.fetch_3d_model(model_id)

                display_scenes_ids = self.product_data.get('display_scenes_ids', [])
                if display_scenes_ids:
                    await self.fetch_display_scenes(display_scenes_ids)

                
            else:
                print(f"❌ Product not found: {response.status_code}")
                print(f"❌ Response: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

    
    async def fetch_3d_model(self, model_id: int):
        """Fetch 3D model and save it to assets"""
        import httpx
        import os
        
       
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/products/get_3d_model/{model_id}/",
                                            cookies=cookies_dict )

            if response.status_code == 200:
                self.model_file = response.content
                self.model_filename = response.headers.get(
                    "Content-Disposition", 
                    f"{model_id}.glb"
                ).split("filename=")[-1].strip('"')
                
                public_path = "assets/models"
                os.makedirs(public_path, exist_ok=True)
                
                file_path = os.path.join(public_path, self.model_filename)
                with open(file_path, "wb") as f:
                    f.write(self.model_file)
                
                self.model_url = f"/models/{self.model_filename}"
                
                print(f"✅ Fetched 3D model: {self.model_filename}")
                print(f"✅ Saved to: {file_path}")
                print(f"✅ Model URL: {self.model_url}")
            else:
                print(f"❌ Model not found: {response.status_code}")
                self.model_url = ""
        except Exception as e:
            print(f"❌ Error fetching 3D model: {e}")
            import traceback
            traceback.print_exc()
            self.model_url = ""

            
    async def fetch_display_scenes(self, scene_ids: list):
        """Fetch all display scenes for the product"""
        import httpx
        
        self.display_scene_urls = []
        
        try:
            print(f"🎬 Fetching {len(scene_ids)} display scenes...")
            
            for scene_id in scene_ids:
                # Build the URL for each scene
                scene_url = f"{API_BASE_URL}/products/get_display_scene/{scene_id}/"
                self.display_scene_urls.append(scene_url)
                print(f"✅ Added scene URL: {scene_url}")
            
            self.display_scenes_loaded = True
            print(f"✅ Total scenes loaded: {len(self.display_scene_urls)}")
            
        except Exception as e:
            print(f"❌ Error fetching display scenes: {e}")
            import traceback
            traceback.print_exc()
            self.display_scene_urls = []

def model_detail_modal() -> rx.Component:
   
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
              
                rx.hstack(
                    rx.text(
                        "Gaming Chair - Pink Edition",
                        font_size="24px",
                        font_weight="bold",
                        color="#22282c"
                    ),
                    rx.button(
                        rx.icon("x", size=20),
                        on_click=ModalState.close_demo_modal,
                        variant="ghost",
                        size="2",
                        color_scheme="red",
                        cursor="pointer"
                    ),
                    justify="between",
                    width="100%",
                    margin_bottom="20px"
                ),

               
                rx.hstack(
                   
                    rx.box(
                        ThreeFiberCanvas.create(
                            SceneWithLighting.create(
                                ModelViewer3D.create(
                                    url=ModalState.demo_model_url,
                                    scale=3.0,
                                    position=[0, 0, 0],
                                    rotation=[0, 0, 0]
                                ),
                                CameraControls.create()
                            ),
                            camera={"position": [3, 3, 3], "fov": 50},
                            style={
                                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                                "border_radius": "12px",
                                
                            }
                        ),
                        width="55%",
                        height = "500px"
                    
                    ),

                    rx.vstack(
                        rx.text(
                            "Product Details",
                            font_size="18px",
                            font_weight="bold",
                            color="#22282c",
                            margin_bottom="10px"
                        ),

                        rx.hstack(
                            rx.image(
                                src="/images/room.jpg",
                                width="160px",
                                height="160px",
                                border_radius="8px",
                                border="2px solid #929FA7",
                                object_fit="cover"
                            ),
                            rx.image(
                                src="/images/room.jpg",
                                width="160px",
                                height="160px",
                                border_radius="8px",
                                border="2px solid #e0e0e0",
                                object_fit="cover"
                            ),
                            rx.image(
                                src="/images/room.jpg",
                                width="160px",
                                height="160px",
                                border_radius="8px",
                                border="2px solid #e0e0e0",
                                object_fit="cover"
                            ),
                            spacing="2",
                            margin_bottom="15px",
                            justify="between",
                            width="100%"
                        ),

               
                        rx.text(
                            "Premium gaming chair with ergonomic design and adjustable features. Perfect for long gaming sessions.",
                            font_size="14px",
                            color="#666",
                            margin_bottom="15px"
                        ),

                  
                        rx.vstack(
                            rx.text("Price", font_size="28px", font_weight="bold", color="#22282c"),
                            rx.hstack(
                            rx.text("Physical:", font_size="16px", color="#22282c"),
                            rx.text("$1299", font_size="18px", color="#22282c", font_weight="bold"),
                            rx.divider(),
                            rx.button(rx.icon("shopping-cart"), "Add", style=cart_button),
                            rx.button("Buy Now", bg="black", color="white"),
                            width="100%",
                        ),
                            rx.hstack(
                                rx.text("Digital:", font_size="16px", color="#22282c"),
                                rx.text("$99", font_size="18px", color="#22282c", font_weight="bold"),
                                rx.divider(),
                                rx.button(rx.icon("zap"), "Add", style=cart_button),
                                rx.button("Buy Now", bg="black", color="white"),
                                width="100%",
                                margin_bottom="30px"
                            ),
                            rx.button(
                                "View Demo",
                                width="100%",
                                size="3",
                                
                                style={
                                    "border": "1px solid #929FA7",
                                    "color": "#22282c",
                                    "border_radius": "8px",
                                    "background_color": "white",
                                    "cursor":"pointer"
                                }  ,
                                _hover={
                                    "background_color": "#22282c",
                                    "color": "white",
                                }, 
                            ),
                            spacing="2",
                            width="100%",
                            
                        ),

                        width="45%",
                        align_items="start",
                        spacing="2"
                    ),

                    spacing="4",
                    width="100%",
                    align="start"
                ),

                width="100%",
                spacing="4"
            ),
            max_width="1200px",
            padding="30px",
            style={
                "background": "white",
                "border_radius": "16px",
                "box_shadow": "0 20px 60px rgba(0,0,0,0.3)"
            }
        ),
        open=ModalState.demo_modal_open,
    )


def simple_3d_viewer() -> rx.Component:
    return rx.box(
        ThreeFiberCanvas.create(
            SceneWithLighting.create(
                ModelViewer3D.create(
                    url=RoomSceneState.selected_room_model,
                    scale=3.0,
                    position=[0,0,0]
                ),
                ModelViewer3D.create(
                    url=ProductDetailState.model_url,
                    scale=ModelState.model_scale,
                    position=[ModelState.model_x, ModelState.model_y, ModelState.model_z],
                    rotation=[0, ModelState.model_rotation_y, 0]  
                ),
                CameraControls.create()
            ),
            camera={"position": [3, 3, 3], "fov": 50},
            style={"background": "white","border_radius":"12px","border":"0.5px solid #929FA7"}     
        ),
        
        rx.vstack(
            rx.text("Furniture Controls", font_weight="bold", font_size="14px", color="white"),
         
            rx.hstack(
                rx.text("Size:", font_size="12px", color="white"),
                rx.button(
                    rx.icon("minus", size=16),
                    on_click=ModelState.decrease_scale,
                    size="1",
                    variant="soft"
                ),
                rx.text(f"{ModelState.model_scale:.1f}", font_size="12px", color="white"),
                rx.button(
                    rx.icon("plus", size=16),
                    on_click=ModelState.increase_scale,
                    size="1",
                    variant="soft"
                ),
                spacing="2"
            ),
      
            rx.hstack(
                rx.text("Left/Right:", font_size="12px", color="white"),
                rx.button(
                    rx.icon("arrow-left", size=16),
                    on_click=ModelState.move_left,
                    size="1",
                    variant="soft"
                ),
                rx.button(
                    rx.icon("arrow-right", size=16),
                    on_click=ModelState.move_right,
                    size="1",
                    variant="soft"
                ),
                spacing="2"
            ),
            
            rx.hstack(
                rx.text("Up/Down:", font_size="12px", color="white"),
                rx.button(
                    rx.icon("arrow-up", size=16),
                    on_click=ModelState.move_up,
                    size="1",
                    variant="soft"
                ),
                rx.button(
                    rx.icon("arrow-down", size=16),
                    on_click=ModelState.move_down,
                    size="1",
                    variant="soft"
                ),
                spacing="2"
            ),
          
            rx.hstack(
                rx.text("Forward/Back:", font_size="12px", color="white"),
                rx.button(
                    rx.icon("move-up", size=16),
                    on_click=ModelState.move_forward,
                    size="1",
                    variant="soft"
                ),
                rx.button(
                    rx.icon("move-down", size=16),
                    on_click=ModelState.move_back,
                    size="1",
                    variant="soft"
                ),
                spacing="2"
            ),
            
            rx.hstack(
                rx.text("Rotate:", font_size="12px", color="white"),
                rx.button(
                    rx.icon("rotate-ccw", size=16),
                    on_click=ModelState.rotate_left,
                    size="1",
                    variant="soft"
                ),
                rx.button(
                    rx.icon("rotate-cw", size=16),
                    on_click=ModelState.rotate_right,
                    size="1",
                    variant="soft"
                ),
                spacing="2"
            ),
            
            rx.button(
                "Reset Position",
                on_click=ModelState.reset_position,
                size="1",
                variant="outline",
                color_scheme="gray"
            ),
            
            position="absolute",
            bottom="20px",
            left="20px",
            z_index="10",
            background="rgba(0,0,0,0.7)",
            padding="10px",
            border_radius="8px",
            spacing="2"
        ),
        
        rx.button(
            "View Detail",
            size="2", 
            on_click=lambda: go_to_demo("/models/gaming_chair_pink.glb"),
            position="absolute",
            top="20px",
            right="10px",
            z_index="10",
            color_scheme="teal",
            cursor = "pointer",
            font_weight= "bold"
        ),
        
        style={
            "position": "relative", 
            "width": "100%", 
            "height": "600px", 
            "margin": "auto",
        
        }, 
    )


def vertical_3d_scenes(model_urls: list[str], scene_height: int = 200) -> rx.Component:
    scenes = []
    for i, url in enumerate(model_urls):
        scenes.append(
            rx.box(
                ThreeFiberCanvas.create(
                    SceneWithLighting.create(
                        ModelViewer3D.create(
                            url=url,
                            scale=3.0,
                            position=[0, 0, 0]
                        ),
                        CameraControls.create()
                    ),
                    camera={"position": [3, 3, 3], "fov": 50},
                    style={
                        "background": "black",
                        "border_radius": "10px",
                        "height": f"{scene_height}px"
                    }
                ),
                on_click=lambda u=url: RoomSceneState.select_room(url),  
                cursor="pointer",  
                border_radius="12px",
                border=rx.cond(
                    RoomSceneState.selected_room_model == url,
                    "3px solid teal",
                    "3px solid transparent"
                ),
                _hover={
                  
                    "opacity": "0.8",
        
                },
                margin_bottom="10px"  
            )
        )
    return rx.vstack(*scenes)


@rx.event 
def go_to_demo(model: str): 
    return ModalState.open_demo_modal(model)


def product_detail_content() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                rx.hstack(
                    rx.box(
                        vertical_3d_scenes([
                            "/models/gamingRoom.glb",
                            "/models/livingroom_scene.glb",
                            "/models/livingroom_scene2.glb"
                        ]),
                    ),
                    simple_3d_viewer(),
                    align="start",
                    width="100%"
                ),
                width="100%",
                padding="20px"
            ),

            rx.box(
                rx.vstack(
                    rx.text(ProductDetailState.product_data.get('name', 'Loading...'), font_size="24px", font_weight="bold", color="#22282c"),

                    rx.text("Colors", font_size="16px", margin_top="10px", color="#22282c", font_weight="bold"),
                    rx.hstack(
                            rx.hstack(
                                rx.box(style={"width": "30px", "height": "30px", "border_radius": "50%", "background_color": "beige"}),
                                rx.text("Beige", font_size="14px", color="gray"),
                                spacing="2",
                                align_items="center"
                            ),
                            rx.hstack(
                                rx.box(style={"width": "30px", "height": "30px", "border_radius": "50%", "background_color": "wooden"}),
                                rx.text("Dark Blue", font_size="14px", color="gray"),
                                spacing="2",
                                align_items="center"
                            ),
                            rx.hstack(
                                rx.box(style={"width": "30px", "height": "30px", "border_radius": "50%", "background_color": "brown"}),
                                rx.text("Brown", font_size="14px", color="gray"),
                                spacing="2",
                                align_items="center"
                            ),
                            spacing="4",  # spacing between color items
                        ),
                    
                    rx.text("Price", font_size="18px", font_weight="bold", margin_top="15px", color="#22282c"),
                    rx.hstack(
                        rx.text("Physical:", font_size="16px", color="#22282c"),
                        rx.text(f"${ProductDetailState.product_data.get('physical_price', '0')}", font_size="18px", color="#22282c", font_weight="bold"),
                        rx.divider(),
                        rx.button(rx.icon("shopping-cart"), "Add", style=cart_button),
                        rx.button("Buy Now", bg="black", color="white"),
                        width="100%",
                    ),
                    rx.hstack(
                        rx.text("Digital:", font_size="16px", color="#22282c"),
                        rx.text(f"${ProductDetailState.product_data.get('digital_price', '0')}", font_size="18px", color="#22282c", font_weight="bold"),
                        rx.divider(),
                        rx.button(rx.icon("zap"), "Add", style=cart_button),
                        rx.button("Buy Now", bg="black", color="white"),
                        width="100%",
                    ),

                    rx.button("Browse More Products", margin_top="20px", border="1px solid #929FA7", background_color="white", style=button_style, on_click=lambda: ProductDetailState.fetch_3d_model(3),
                     _hover={
                            "background_color": "#22282c",
                            "border": "1px solid #22282C",
                            "color": "white"
                            
                        },),
                    rx.button("Preview in AR", bg="black", color="white", style=button_style,
                    _hover={
                            "background_color": "white",
                            "border": "1px solid #22282C",
                            "color": "#22282c"
                          
                        },),
                ),
                width="40%",
                padding="20px",
                border="1px solid #ddd",
                border_radius="12px",
                margin_top="20px"
            ),
            width="100%",
            justify="between"
        ),
        
    
        model_detail_modal(),
        
        position="relative"
    )

@rx.page(route="/details/[product_Id]",on_load=ProductDetailState.on_load )
def product_detail_page() -> rx.Component:
    return template(product_detail_content)


filter_style = {
    "background_color": "white",
    "border": "1px solid #22282C",
    "border_radius": "12px"
}

button_style = {
    "color": "#22282c", 
    "margin_top": "10px",
    "width": "100%",
    "padding": "25px 0px",
    "border_radius": "12px",
    "font_weight": "bold",
    "cursor":"pointer",
}

cart_button = {
    "color": "#22282C",
    "border": "1px solid #929FA7",
    "background_color": "white",
    "border_radius": "8px",
}