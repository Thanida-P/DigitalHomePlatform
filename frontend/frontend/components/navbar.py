import reflex as rx
import httpx
import os
from ..state import AuthState
from ..config import API_BASE_URL


def iframe_message_listener() -> rx.Component:
    api_base = API_BASE_URL 
    return rx.script(f"""
        (function() {{
            if (window._iframeListenerAttached) return;
            window._iframeListenerAttached = true;

            async function refreshCartBadge() {{
                try {{
                    const resp = await fetch('{api_base}/carts/view/', {{
                        credentials: 'include',
                    }});
                    if (resp.ok) {{
                        const cartData = await resp.json();
                        const items = cartData.items || [];
                        const totalQty = items.reduce((sum, item) => sum + (item.quantity || 1), 0);
                        window.dispatchEvent(new CustomEvent('cart-updated', {{ detail: {{ quantity: totalQty }} }}));
                    }}
                }} catch(err) {{
                    console.error('Cart refresh error:', err);
                }}
            }}
 
            window.addEventListener('message', async function(event) {{
                const data = event.data;
                if (!data || !data.type) return;

                if (data.type === 'NAVIGATE') {{
                    window.location.href = data.url;
                }}
                     
                if (data.type === 'CART_UPDATED') {{
                    await refreshCartBadge();
                }}

                if (data.type === 'ADD_TO_CART') {{
                    try {{
                        const formData = new FormData();
                        formData.append('product_id', data.productId);
                        formData.append('quantity', data.quantity || 1);
                        formData.append('price_type', data.priceType);

                        const response = await fetch('{api_base}/carts/add_item/', {{
                            method: 'POST',
                            body: formData,
                            credentials: 'include',
                        }});

                        if (response.ok) {{
                            await refreshCartBadge();  
                        }} else {{
                            const text = await response.text();
                            
                        }}
                    }} catch (err) {{
                        console.error('Add to cart error:', err);
                    }}
                }}
            }});
        }})();
    """)


def cart_refresh_listener() -> rx.Component:
    return rx.script("""
        (function() {
            if (window._cartRefreshListenerAttached) return;
            window._cartRefreshListenerAttached = true;

            window.addEventListener('cart-updated', function(e) {
                const quantity = e.detail?.quantity ?? 0;

                const badgeBox = document.getElementById('cart-badge-box');
                if (badgeBox) {
                    badgeBox.style.display = quantity > 0 ? 'flex' : 'none';
                    const text = badgeBox.querySelector('[data-cart-badge]');
                    if (text) text.textContent = quantity;
                }
            });
        })();
    """)


class NavCartState(rx.State):
    total_itmes: int = 0
    total_quantity: int = 0
    is_loading = True
    cart_quantity: int = 0

    @rx.var
    def current_url(self) -> str:
        return self.router.page.path


    async def load_cart_quantity(self):
        import httpx
        """Fetch only cart quantity from backend"""
        
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/carts/view/",
                    cookies=cookies_dict,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    items = data.get('items', [])
                    total_quantity = sum(item.get('quantity', 1) for item in items)
                    
                    self.cart_quantity = total_quantity
                
                elif response.status_code == 404:
                    self.cart_quantity = 0

                else:
                    self.cart_quantity = 0

        except Exception as e:
            rx.toast.error(f"Network error: {e}")
            print(f"Exception in load_cart_quantity: {e}")

        finally:
            self.is_loading = False


def nav_link(label: str, href: str):
    """Create a nav link with active state styling"""
    return rx.link(
        label,
        href=href,
        style={
            "font_family": "Lato, sans-serif",
            "font_size": "16px",
            "color": rx.cond(
                NavCartState.current_url == href,
                "#22282c",  
                "#22282C"   
            ),
            "font_weight": rx.cond(
                NavCartState.current_url == href,
                "mdedium",
                "normal"
            ),
            "display": "inline-block",
            "padding_bottom": "2px",
            "text_decoration": "none",
            "border_bottom": rx.cond(
                NavCartState.current_url == href,
                "1px solid #22282c",
                "2px solid transparent"
            ),
        },
    )


def navbar_page():
    return rx.fragment(
        iframe_message_listener(),
        cart_refresh_listener(),
        rx.hstack(
        rx.hstack(
            rx.link(
                "Digital Home",
                href="/",
                style={
                    "font_family": "Racing Sans One",
                    "font_size": "16px", 
                    "font_weight": "bold",
                    "font_style": " italic",
                    "color": "#22282c",
                    "text_decoration": "none",
                },
            ),
            nav_link("Shop", "/shop"),
            rx.cond(
                AuthState.is_logged_in,
                rx.link(
                    rx.hstack(
                        rx.text("My Home"),
                        spacing="2",
                    ),
                    variant="ghost",
                    style={
                        "color": "#22282C",
                        "font_family": "Lato, sans-serif",
                        "font_size": "16px",
                        "align-item": "center",
                        "text_decoration": "none",
                        "_hover": {
                            "cursor": "pointer",
                            "color": "#E0E6EA",
                            "background_color": "transparent"
                        },
                    },
                    on_click=AuthState.open_scene_creator,
                ),
                rx.fragment(),  
            ),
   
            spacing="6",
        ),

        
        rx.spacer(),
        
   
        rx.hstack(
            rx.box(
                rx.button(
                    rx.icon("shopping-cart"),
                    cursor = "pointer",
                    aria_label="Cart",
                    variant="ghost",
                    style={
                        "color": rx.cond(
                            NavCartState.current_url == "/cart",
                            "#299FCA",  
                            "#22282C"  
                        ),
                        "width": "40px",
                        "height": "40px",
                        "_hover": {
                                    "background_color": "white",
                                    "varient": "ghost",
                                    "color": "#299FCA"
                                },
                    },
                    on_click=rx.redirect("/cart"),
                    
                ),
                rx.box(
                    
                    rx.box(
                        rx.text(
                            NavCartState.cart_quantity,
                            data_cart_badge=True,
                            font_size="12px",
                            color="white",
                            font_weight="bold",
                            text_align="center",
                        ),
                        id="cart-badge-box",
                        position="absolute",
                        top="2px",
                        right="4px",
                        background_color="#FF4C4C",
                        border_radius="9999px",
                        width="18px",
                        height="18px",
                        display=rx.cond(NavCartState.cart_quantity > 0, "flex", "none"), 
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
                        rx.link(
                            rx.hstack(
                                rx.icon("user", size=20),
                                rx.text(AuthState.username, weight="medium"),
                                spacing="2",
                            ),
                            variant="ghost",
                            style={
                               
                                "color": rx.cond(
                                    NavCartState.current_url == "/profile",
                                    "#299FCA",
                                    "#22282c",   
                                ),
                                "padding": "10px 5px",
                                "border_radius": "8px",
                                "text_decoration": "none",
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
                    "Sign In",
                    color="white",
                    background_color="#22282C",
                    border_radius="8px",
                    cursor = "pointer",
                    text_decoration =  "none",
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
    ))


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
  
'''rx.input(
                rx.input.slot(rx.icon("search"), color="#807E80"),
                placeholder="Search...",
                type="search",
                size="2",
                width="400px",
                justify="end",
                background_color="#E0E6EA",
                border_radius="20px",
                color="#22282C",
),'''
          
  
'''rx.input(
                rx.input.slot(rx.icon("search"), color="#807E80"),
                placeholder="Search...",
                type="search",
                size="2",
                width="400px",
                justify="end",
                background_color="#E0E6EA",
                border_radius="20px",
                color="#22282C",
),'''
          