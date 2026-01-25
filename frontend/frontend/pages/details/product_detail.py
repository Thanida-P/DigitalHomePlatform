import reflex as rx 
from ...template import template 
from ...state import AuthState
from ...config import API_BASE_URL
import httpx


class ProductDetailState(rx.State):
    product_id: str = ""
    api_base_url: str = API_BASE_URL
    login_token: str = ""

    async def on_load(self):
        self.product_id = self.router.page.params.get("product_Id", "")
        await self.get_login_token()

    async def get_login_token(self):
        auth_state = await self.get_state(AuthState)
        async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/users/get_login_token/",
                    cookies=auth_state.session_cookies,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    token = data.get("token")
                  
                    self.login_token = token
                else:
                    print(f"❌ Failed to get token: {response.status_code}")
                    self.login_token = None


def product_viewer_iframe() -> rx.Component:
    iframe_url = (
        f"/pages/viewer_3d/viewer_3d.html"
        f"?productId={ProductDetailState.product_id}"
        f"&token={ProductDetailState.login_token}"
        f"&api={ProductDetailState.api_base_url}"
    )

    return rx.fragment(
        rx.el.iframe(
            src=iframe_url,
            width="100%",
            height="100%",
            min_height = "700px",
            style={"border": "none"}
        ),

       rx.script(f"""
            window.addEventListener('message', function(event) {{
                if (event.data.type === 'ADD_TO_CART') {{
                    const form = new FormData();
                    form.append('product_id', event.data.productId);
                    form.append('type', event.data.priceType);
                    form.append('quantity', event.data.quantity);

                    fetch('{API_BASE_URL}/carts/add_item/', {{
                        method: 'POST',
                        credentials: 'include',
                        body: form
                    }}).then(res => {{
                        if (!res.ok) {{
                            console.error("Cart add failed:", res.status);
                        }}
                    }}).catch(err => console.error("Cart add error:", err));
                }}

                if (event.data.type === 'NAVIGATE') {{
                    window.location.href = event.data.url;
                }}
            }});
        """)


    )


def product_detail_content() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading(
                "Product Details",
                size="7",
                margin_bottom="20px",
                color="#22282c"
            ),
            
            product_viewer_iframe(),
            
            width="100%",
            max_width="1400px",
            margin="0 auto",
            padding="20px"
        )
    )


@rx.page(
    route="/details/[product_Id]",
    on_load=ProductDetailState.on_load
)
def product_detail_page() -> rx.Component:
    return template(product_detail_content)
