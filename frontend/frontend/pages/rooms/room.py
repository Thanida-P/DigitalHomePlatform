import reflex as rx
from ...state import DynamicState, AuthState
from ...template import template
from ...config import API_BASE_URL
import httpx
import asyncio
from ...components.product_card import product_card

class RoomState(rx.State):
    product_types: list[str] = []
    selected_product_type: str = ""
    is_loading: bool = False
    error_message: str = ""


    async def load_product_types_for_room(self):
        """Fetch product types for the current room category"""
        
        self.product_types = []
        self.selected_product_type = ""
        
        dynamic_state = await self.get_state(DynamicState)
        
        max_attempts = 50
        attempts = 0
        while dynamic_state.is_loading and attempts < max_attempts:
            await asyncio.sleep(0.1)
            attempts += 1
        
        room_title = dynamic_state.room_title
        
        if not room_title or room_title == "":
            print("⚠️ No room title available yet")
            return
        
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        
        self.is_loading = True
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/products/types/",
                    data={"category": room_title},
                    cookies=cookies_dict,
                )

                if response.status_code == 200:
                    data = response.json()
                    self.product_types = data.get("product_types", [])
                    await self.filter_by_product_type("")
                   
                else:
                    self.error_message = f"Failed to load product types"
                  
        except Exception as e:
            self.error_message = f"Error: {str(e)}"
           
        finally:
            self.is_loading = False

    async def filter_by_product_type(self, product_type: str):
        
        self.selected_product_type = product_type
        
        dynamic_state = await self.get_state(DynamicState)
        room_title = dynamic_state.room_title
        
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        
        dynamic_state.is_loading = True
        
        try:
            async with httpx.AsyncClient() as client:
                if product_type == "":
                 
                    response = await client.post(
                        f"{API_BASE_URL}/products/list/",
                        data={"category": room_title},
                        cookies=cookies_dict,
                    )
                else:
                    
                    response = await client.post(
                        f"{API_BASE_URL}/products/list/",
                        data={
                            "category": room_title,
                            "product_type": product_type
                        },
                        cookies=cookies_dict,
                    )
                
                if response.status_code == 200:
                    data = response.json()

                    dynamic_state.room_products = [
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
                
                else:
                    dynamic_state.room_products = []
                    
                    
        except Exception as e:
            dynamic_state.room_products = []
            print(f"❌ Exception filtering products: {str(e)}")
        finally:
            dynamic_state.is_loading = False


def room_content() -> rx.Component:
    return rx.hstack(
      
        rx.box(
            rx.vstack(
                rx.center(
                    rx.image(
                        src=DynamicState.room_image,
                        width="95%",
                        height="auto",
                    ),
                    style={"margin": "0px 0px"},
                ),
                rx.center(
                    rx.text(
                        DynamicState.room_title,
                        font_size="18px",
                        font_weight="bold",
                        color="#22282C",
                    ),
                    width="100%",
                    padding="20px 0",
                ),
             
                rx.vstack(
                   
                    rx.cond(
                        RoomState.is_loading,
                        rx.center(
                            rx.spinner(size="2"),
                            padding="20px",
                        ),
                        rx.cond(
                            RoomState.product_types.length() > 0,
                            rx.vstack(
                               
                                rx.box(
                                    rx.hstack(
                                        rx.icon(
                                            tag="chevron-right",
                                            size=16,
                                            color=rx.cond(
                                                RoomState.selected_product_type == "",
                                                "#22282C",
                                                "#9CA3AF"
                                            ),
                                        ),
                                        rx.text(
                                            "View All",
                                            font_size="14px",
                                            color=rx.cond(
                                                RoomState.selected_product_type == "",
                                                "#22282C",
                                                "#6B7280"
                                            ),
                                            font_weight=rx.cond(
                                                RoomState.selected_product_type == "",
                                                "bold",
                                                "normal"
                                            ),
                                        ),
                                        spacing="2",
                                        align_items="center",
                                    ),
                                    padding="12px 20px",
                                    background_color=rx.cond(
                                        RoomState.selected_product_type == "",
                                        "#E5E7EB",
                                        "transparent"
                                    ),
                                    cursor="pointer",
                                    _hover={"background_color": "#E5E7EB"},
                                    on_click=RoomState.filter_by_product_type(""),
                                    width="100%",
                                ),
                              
                                rx.foreach(
                                    RoomState.product_types,
                                    lambda product_type: rx.box(
                                        rx.hstack(
                                            rx.icon(
                                                tag="chevron-right",
                                                size=16,
                                                color=rx.cond(
                                                    RoomState.selected_product_type == product_type,
                                                    "#22282C",
                                                    "#9CA3AF"
                                                ),
                                            ),
                                            rx.text(
                                                product_type,
                                                font_size="14px",
                                                color=rx.cond(
                                                    RoomState.selected_product_type == product_type,
                                                    "#22282C",
                                                    "#6B7280"
                                                ),
                                                font_weight=rx.cond(
                                                    RoomState.selected_product_type == product_type,
                                                    "bold",
                                                    "normal"
                                                ),
                                            ),
                                            spacing="2",
                                            align_items="center",
                                        ),
                                        padding="12px 20px",
                                        background_color=rx.cond(
                                            RoomState.selected_product_type == product_type,
                                            "#E5E7EB",
                                            "transparent"
                                        ),
                                        cursor="pointer",
                                        _hover={"background_color": "#E5E7EB"},
                                        on_click=RoomState.filter_by_product_type(product_type),
                                        width="100%",
                                    )
                                ),
                                width="100%",
                                align_items="stretch",
                            ),
                         
                            rx.text(
                                "No product types available",
                                font_size="12px",
                                color="#9CA3AF",
                                padding="20px",
                                text_align="center",
                            ),
                        ),
                    ),
                    width="100%",
                    spacing="2",
                ),
            ),
            width="280px",  
            height="100%",
            bg="#F9FAFB",
        ),
     
     
        rx.box(
            rx.cond(
                DynamicState.is_loading | (DynamicState.room_products.length() == 0),
                
                rx.center(
                    rx.vstack(
                        rx.spinner(size="3"),
                        rx.text("Loading products...", color="#6B7280"),
                        spacing="3",
                    ),
                    width="100%",
                    height="400px",
                ),
             
                rx.cond(
                    DynamicState.room_products.length() > 0,
                 
                    rx.grid(
                        rx.foreach(
                            DynamicState.room_products,
                            render_fn = product_card,
                        ),
                        columns="3",
                        spacing="6",
                        width="100%",
                    ),
                   
                    rx.center(
                        rx.vstack(
                            rx.text(
                                "No products found",
                                font_size="18px",
                                font_weight="bold",
                                color="#22282C",
                            ),
                            rx.text(
                                f"We couldn't find any products in {DynamicState.room_title}",
                                font_size="14px",
                                color="#6B7280",
                            ),
                            rx.link(
                                rx.button(
                                    "Back to Home",
                                    style={
                                        "background_color": "#22282C",
                                        "color": "white",
                                        "padding": "10px 20px",
                                        "border_radius": "8px",
                                    }
                                ),
                                href="/",
                            ),
                            spacing="3",
                        ),
                        width="100%",
                        height="400px",
                    ),
                ),
            ),
            flex="1",
            padding="0 20px",
        ),
        spacing="4",
        width="100%",
        height="100%",
        padding_top="30px",
    )


@rx.page(route="/rooms/[room]", on_load=[DynamicState.on_load, RoomState.load_product_types_for_room])
def room_page() -> rx.Component:
    return template(room_content)