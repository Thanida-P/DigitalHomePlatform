import reflex as rx 
from ..template import template 
from reflex.components.component import NoSSRComponent 
from ..components.product_card import product_list
from typing import Any, Dict, List 
import urllib.parse 
#from ..state import State
import httpx
from ..state import AuthState
from ..components.navbar import NavCartState
from ..config import API_BASE_URL



'''class ShopState(rx.State):

    products: List[Dict] = []
    

    async def load_products(self):
        API_BASE_URL = "http://localhost:8001"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{API_BASE_URL}/products/list/", json={})
            
            if response.status_code != 200:
                print(f"❌ Backend error: {response.status_code} {response.text}")
                return

            data = response.json()
            normalized = []
            for p in data.get("products", []):
                normalized.append({
                    "id": p.get("id"),
                    "title": p.get("name", "Untitled Product"),
                    "description": p.get("description", ""),
                    "category": p.get("category", "Uncategorized"),
                    "digital_price": p.get("digital_price", "0"),
                    "physical_price": p.get("physical_price", "0"),
                    "image": f"data:image/png;base64,{p['image']}" if p.get("image") else "/placeholder.png",
                })

            self.products = normalized
            print(f"✅ Loaded {len(normalized)} products")

        except Exception as e:
            print(f"❌ Error loading products: {e}")
'''

class ShopState(rx.State):


    products: List[Dict] = []
    search_query: str = ""
    category: str = "All Categories"
    price_sort: str = "All Prices"
    product_format: str = "All Products"
    sort_by: str = "Most Popular"
    model_file: bytes = ""
    model_filename: str = ""       
    scene_file: bytes = b""      
    scene_filename: str = ""


    def set_search_query(self, value: str):
        self.search_query = value
        return ShopState.load_products

    def set_category(self, value: str):
        self.category = value

    def set_price_sort(self, value: str):
        self.price_sort = value

    def set_product_format(self, value: str):
        self.product_format = value

    def set_sort_by(self, value: str):
        self.sort_by = value

    async def load_products(self):

        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
    
        
        sort_mapping = {
            "Most Popular": "popularity",
            "Newest": "newest",
            "Digital: Low to High": "digital_price_low_to_high",
            "Digital: High to Low": "digital_price_high_to_low",
            "Physical: Low to High": "physical_price_low_to_high",
            "Physical: High to Low": "physical_price_high_to_low"
        }
        
        format_mapping = {
            "All Products": None,
            "Physical": "physical",
            "Digital": "digital"
        }
        
        form_data = {}
        
        if self.search_query:
            form_data["search_query"] = self.search_query
        
        if self.category and self.category != "All Categories":
            form_data["category"] = self.category
        
        if self.product_format and self.product_format != "All Products":
            form_data["format"] = format_mapping[self.product_format]
        
        if self.sort_by:
            form_data["sort_by"] = sort_mapping.get(self.sort_by, "popularity")
        
        try:
            async with httpx.AsyncClient() as client:
        
                response = await client.post(
                    f"{API_BASE_URL}/products/list/", 
                    data=form_data,
                    cookies=cookies_dict,
                )
            
            if response.status_code != 200:
                print(f"❌ Backend error: {response.status_code} {response.text}")
                return
            
            data = response.json()
            self.products = [
                {
                    "id": p.get("id"),
                    "title": p.get("name", "Untitled Product"),
                    "description": p.get("description", ""),
                    "category": p.get("category", "Uncategorized"),
                    "digital_price": p.get("digital_price", "0"),
                    "physical_price": p.get("physical_price", "0"),
                    "image": f"data:image/png;base64,{p['image']}" if p.get("image") else "/placeholder.png",
                    "rating": str(p.get("rating", "4.6")), 
                    "hover_image": "/images/default_hover.png", 
                    "link": f"/details/{p.get('id')}",  
                }
                for p in data.get("products", [])
            ]
            print(f"✅ Loaded {len(self.products)} products with filters: {form_data}")
            print(self.products)
            
        except Exception as e:
            print(f"❌ Error loading products: {e}")



    async def add_to_cart(self, product_id: int, item_type: str, quantity: int = 1):
        NavCartState.increment_cart_quantity()
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        """Send request to backend to add item to cart."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/carts/add_item/",
                    data={
                        "product_id": product_id,
                        "type": item_type,
                        "quantity": quantity,
                        
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    cookies =cookies_dict,
                )

            print("🔍 Status:", response.status_code)
            print("🔍 Text:", response.text) 

            if response.status_code == 201:
                rx.toast.success("✅ Item added to cart successfully!")
                NavCartState.load_cart_quantity()
            else:
                error = response.json().get("error", response.text)
                rx.toast.error(f"❌ Failed: {error}")
                print(f"Error adding to cart: {response.status_code} {response.text}")
                

        except Exception as e:
            rx.toast.error(f"⚠️ Network error: {e}")
            print(f"❌ Exception in add_to_cart: {e}")



    product_detail: dict = {}
    async def fetch_product_detail(self, product_id:int):

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/products/get_product_detail/{product_id}/")

            if response.status_code == 200:
                data = response.json()
                self.product_detail = data.get("product", {})
                print(f"✅ Fetched product detail: {self.product_detail}")

            elif response.status_code == 404:
                print("❌ Product not found")
                self.product_detail = {}
            else:
                print(f"❌ Backend error: {response.status_code} {response.text}")
                self.product_detail = {}

        except Exception as e:
            print(f"❌ Error fetching product detail: {e}")
            self.product_detail = {}
       
       
    async def fetch_3d_model(self, model_id: str):

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/products/get_3d_model/{model_id}/")

            if response.status_code == 200:
               
                self.model_file = response.content
              
                self.model_filename = response.headers.get("Content-Disposition", f"{model_id}.glb").split("filename=")[-1]
                print(f"✅ Fetched 3D model: {self.model_filename}")
            elif response.status_code == 404:
                print("❌ Model not found")
                self.model_file = b""
                self.model_filename = ""
            else:
                print(f"❌ Backend error: {response.status_code}")
                self.model_file = b""
                self.model_filename = ""

        except Exception as e:
            print(f"❌ Error fetching 3D model: {e}")
            self.model_file = b""
            self.model_filename = ""

    async def fetch_display_scene(self, scene_id: str):

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE_URL}/products/get_display_scene/{scene_id}/")

            if response.status_code == 200:
                self.scene_file = response.content
                self.scene_filename = response.headers.get("Content-Disposition", f"{scene_id}.glb").split("filename=")[-1]
                print(f"✅ Fetched display scene: {self.scene_filename}")
            elif response.status_code == 404:
                print("❌ Scene not found")
                self.scene_file = b""
                self.scene_filename = ""
            else:
                print(f"❌ Backend error: {response.status_code}")
                self.scene_file = b""
                self.scene_filename = ""

        except Exception as e:
            print(f"❌ Error fetching display scene: {e}")
            self.scene_file = b""
            self.scene_filename = ""


def search_and_filters() -> rx.Component:
    return rx.hstack(
        rx.input(
            rx.input.slot(rx.icon("search")),
            placeholder="Search...",
            value=ShopState.search_query,
            on_change=lambda e: ShopState.set_search_query(e.to(str)),
        ),
       
        rx.select(
            ["All Categories", "Living Room", "Gaming Room", "Bedroom", "Kitchen"],
            value=ShopState.category,
            on_change=lambda e: ShopState.set_category(e.to(str)),
        ),
        rx.select(
            ["All Products", "Physical", "Digital"],
            value=ShopState.product_format,
            on_change=lambda e: ShopState.set_product_format(e.to(str)),
        ),
        rx.select(
            [
                "Most Popular", 
                "Newest",
                "Digital Price: Low to High",
                "Digital Price: High to Low",
                "Physical Price: Low to High",
                "Physical Price: High to Low"
            ],
            value=ShopState.sort_by,
            on_change=lambda e: ShopState.set_sort_by(e),
            width="200px",  
            height="40px",
        ),
        rx.button("Search", on_click=ShopState.load_products),
        spacing="2",
        justify="center",
        width="100%",
    )

def shop_content() -> rx.Component:

    return rx.vstack(
        rx.vstack(
            rx.heading(
                "FURNITURE CATALOG",
                font_size="2em",
                font_weight="bold",
                color="#22282C",
                font_family="Poppins"
            ),
            rx.text(
                "Explore our full range of AR & VR-ready furniture models",
                font_size="1em",
                color="#22282C",
                font_family="Poppins"
            ),
            margin_bottom="2rem",
            margin_top="2rem",
            align="center",       
            text_align="center",
            width = "100%",
        ),
        search_and_filters(),
        rx.cond(
                ShopState.products,
                rx.grid(
                     rx.foreach(
                        ShopState.products,
                        render_fn=product_card,
                    ),
                    columns="4",
                    spacing="4",
                    width="100%",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("package-x", size=48, color="#CBD5E1"),
                        rx.text("No products found", size="4", color="#64748B"),
                        spacing="3",
                    ),
                    height="400px",
                ),
            ),
            
            spacing="6",
            width="100%",
            on_mount=ShopState.load_products,
        ),


def hover_swap_photo(default_img: str, hover_img: str, link: str) -> rx.Component:

    return rx.box(
        rx.box(
            rx.image(
                src=default_img,
                width="100%",
                height="250px",
                border_radius="12px",
                object_fit="cover",
            ),
            rx.box(
                rx.image(
                    src="/images/bedroom_grey.jpg",
                    width="100%",
                    height="250px",
                    border_radius="12px",
                    object_fit="cover",
                ),
                rx.center(
                    rx.button(
                        "See Detail",
                        font_size="18px",
                        font_weight="bold",
                        color="white",
                        background_color="rgba(0,0,0,0.6)",
                        padding="6px 12px",
                        border_radius="8px",
                        border="none",
                        cursor="pointer",
                        
                    ),
                    position="absolute",
                    top="50%",
                    left="50%",
                    transform="translate(-50%, -50%)",
                ),
                position="absolute",
                top="0",
                left="0",
                width="100%",
                height="100%",
                opacity="0",
                transition="opacity 0.3s ease",
                _hover={"opacity": "1"},
                z_index="2",
            ),
            position="relative",
            width="100%",
            overflow="hidden",
            cursor="pointer",
            on_click=rx.redirect(link),  
        ),
        style={
            "width": "100%",
            "height": "220px",
            "border_radius": "12px 12px 0 0",
            "margin_bottom": "40px",
        },
    )

def product_card(product: Dict) -> rx.Component:
    return rx.box(
        rx.vstack(
            hover_swap_photo(
                product.get("image", "/images/default.png"),
                product.get("hover_image", "/images/default.jpg"),
                product.get("link", "/cart"),
         
            ),
            rx.vstack(
                rx.hstack(
                    rx.badge(product["category"], color_scheme="orange", border_radius="md"),
                    rx.spacer(),
                    rx.icon("star", color="gold"),
                    rx.text("4.5", font_weight="medium", color="#22282C"),
                    rx.icon("heart", color="black"),
                    align="center",
                    width="100%",
                ),
                rx.text(product["title"], font_weight="bold", font_size="1.1em", color="#22282C"),
                rx.hstack(
                    rx.text("Physical: ", font_weight="medium", color="#22282C"),
                    rx.text(f"${product['physical_price']}", font_weight="bold", color="#22282C"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("shopping-cart"),
                        "Add",
                        color="#22282C",
                        border="1px solid #929FA7",
                        background_color="white",
                        border_radius="8px",
                        cursor = "pointer",
                        on_click=ShopState.add_to_cart(product["id"],"physical",quantity=1),
                    ),
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Digital: ", font_weight="medium", color="#22282C"),
                    rx.text(f"${product['digital_price']}", font_weight="bold", color="#22282C"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("zap"),
                        "Add",
                        color="#22282C",
                        border="1px solid #929FA7",
                        background_color="white",
                        border_radius="8px",
                        cursor = "pointer",
                        on_click=ShopState.add_to_cart(product["id"],"digital",quantity=1),
                    ),
                    width="100%",
                ),
                width="100%",
                align="start",
                padding="0px 20px",
            ),
            bg="white",
            border="1px solid #E2E8F0",
            border_radius="16px",
            width="330px",
            height="450px"
        )
    )

def shop_page() -> rx.Component:
    return template(shop_content)


filter_style = {
    "background_color": "white",
    "border": "1px solid #22282C",
    "border_radius":"12px"
}

