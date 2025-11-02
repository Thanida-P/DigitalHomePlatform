import reflex as rx
import httpx
import os
from ..state import AuthState


class NavCartState(rx.State):
    total_itmes: int = 0
    total_quantity: int = 0
    is_loading = True
    cart_quantity: int = 0

    API_BASE_URL: str = "http://localhost:8001"
    async def load_cart_quantity(self):
        import httpx
        """Fetch only cart quantity from backend"""
        
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.API_BASE_URL}/carts/view/",
                    cookies=cookies_dict,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    items = data.get('items', [])
                    total_quantity = len(items)
                    
                    self.cart_quantity = total_quantity

                    print(f"🛒 Cart quantity: {total_quantity}")
                
                elif response.status_code == 404:
                    self.cart_quantity = 0
                    print("Cart is empty.")
                
                else:
                    error = response.json().get('error', 'Failed to load cart quantity')
                    rx.toast.error(f"Error: {error}")

        except Exception as e:
            rx.toast.error(f"Network error: {e}")
            print(f"Exception in load_cart_quantity: {e}")

        finally:
            self.is_loading = False

    def increment_cart_quantity(self):
        self.cart_quantity += 1

    def decrement_cart_quantity(self, amount: int = 1):
        self.cart_quantity = max(self.cart_quantity - amount, 0)


def nav_link(label: str, href: str):
    return rx.link(
        label,
        href=href,
        style={
            "font_family": "Lato, sans-serif",
            "font_size": "16px",
            "color": "#22282C",
            "display": "inline-block",
            "text_decoration": "none",
        },
    )


def navbar_page():
    return rx.hstack(
     
        rx.hstack(
            nav_link("Digital Home", "/"),
            nav_link("Shop", "/shop"),
            # nav_link("My Home", "/my_home"),
            rx.cond(
                AuthState.is_logged_in,
                rx.button(
                    rx.hstack(
                        rx.text("My Home"),
                        spacing="2",
                    ),
                    variant="ghost",
                    style={
                        "color": "#22282C",
                        "font_family": "Lato, sans-serif",
                        "font_size": "16px",
                        "_hover": {
                            "cursor": "pointer",
                            "color": "#E0E6EA",
                            "background_color": "transparent"
                        },
                    },
                    on_click=AuthState.open_scene_creator,
                ),
                rx.fragment(),  # HIDDEN if not logged in
            ),
            # nav_link("About", "/about"),
            spacing="6",
        ),
        
        rx.spacer(),
        
   
        rx.hstack(
          
            rx.input(
                rx.input.slot(rx.icon("search"), color="#807E80"),
                placeholder="Search...",
                type="search",
                size="2",
                width="400px",
                justify="end",
                background_color="#E0E6EA",
                border_radius="20px",
                color="#22282C",
            ),
          
            rx.box(
                rx.button(
                    rx.icon("shopping-cart"),
                    aria_label="Cart",
                    variant="ghost",
                    style=icon_style,
                    on_click=rx.redirect("/cart"),
                ),
                # show red bubble only if there’s something in the cart
                rx.cond(
                    NavCartState.cart_quantity > 0,
                    rx.box(
                        rx.text(
                            NavCartState.cart_quantity,
                            font_size="12px",
                            color="white",
                            font_weight="bold",
                            text_align="center",
                        ),
                        position="absolute",
                        top="2px",
                        right="4px",
                        background_color="#FF4C4C",
                        border_radius="9999px",
                        width="18px",
                        height="18px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        box_shadow="0 0 2px rgba(0,0,0,0.2)",
                    ),
                ),
                position="relative",
            ),

            
            rx.cond(
                AuthState.is_logged_in,
         
                rx.menu.root(
                    rx.menu.trigger(
                        rx.button(
                            rx.hstack(
                                rx.icon("user", size=20),
                                rx.text(AuthState.username, weight="medium"),
                                spacing="2",
                            ),
                            variant="ghost",
                            style={
                                "color": "#22282C",
                                "padding": "8px 16px",
                                "border_radius": "8px",
                                "_hover": {
                                    "background_color": "#F3F4F6",
                                },
                            },
                        ),
                    ),
                    rx.menu.content(
                        rx.menu.item(
                            rx.hstack(
                                rx.icon("user", size=16),
                                rx.text("Profile"),
                                spacing="2",
                            ),
                            on_click=rx.redirect("/profile"),
                        ),
                        rx.menu.separator(),
                        rx.menu.item(
                            rx.hstack(
                                rx.icon("log-out", size=16),
                                rx.text("Logout"),
                                spacing="2",
                            ),
                            on_click=AuthState.logout,
                            color="red",
                        ),
                    ),
                ),
            
                rx.button(
                    "Sign Up",
                    color="white",
                    background_color="#22282C",
                    border_radius="8px",
                    _hover={
                        "background_color": "#3A4248",
                    },
                    on_click=rx.redirect("/login")
                ),
            ),
            
            spacing="4",
        ),
        
        style=style3,
        on_mount=[AuthState.check_auth, 
                  NavCartState.load_cart_quantity],
    )


style1 = {
    "font_family": "Lato, sans-serif",
    "font_size": "16px",
    "color": "#22282C",
    "font_weight": "bold",
}

style3 = {
    "justify_content": "space-between",
    "align_items": "center",
    "border_bottom": "1px solid #E0E6EA",
    "box_shadow": "0 1px 2px rgba(0, 0, 0, 0.1)",
    "width": "100%",
    "padding": "20px 30px",
    "position": "fixed",
    "top": "0",
    "left": "0",
    "z_index": "1000",
    "background_color": "white"
}

icon_style = {
    "color": "#22282C",
    "width": "40px",
    "height": "40px",
}