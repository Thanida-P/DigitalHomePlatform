import reflex as rx
from typing import Dict
from ..pages.shop import ShopState
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
 
    is_in_wishlist = ShopState.wishlist_items.contains(product["id"])
  
    return rx.box(
        rx.vstack(
            rx.box(
                    hover_swap_photo(
                        product.get("image", "/images/default.png"),
                        product.get("hover_image", "/images/default.jpg"),
                        product.get("link", "/cart"),
                    ),
                    rx.button(
                        rx.cond(
                            is_in_wishlist,
                            rx.icon("heart", color="#EF4444", fill="#EF4444", size=20),
                            rx.icon("heart", color="#9CA3AF", size=20),
                        ),
                        position="absolute",
                        top="10px",
                        right="10px",
                        border="none",
                        border_radius="full",
                        background = "white",
                        padding="8px",
                        width="40px",
                        height="40px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        cursor="pointer",
                        transition="all 0.3s ease",
                        _hover={
                            "background_color": "rgba(255, 255, 255, 1)",
                            "transform": "scale(1.1)",
                        },
                        on_click=lambda: ShopState.toggle_wishlist(product["id"]),
                        z_index="10",
                    ),
                    position="relative",
                    width="100%",
    
                ),
            
            rx.vstack(
                rx.hstack(
                    rx.badge(product["category"], color_scheme="orange", border_radius="md"),
                    rx.spacer(),
                    rx.icon("star", color="gold"),
                    rx.text("4.5", font_weight="medium", color="#22282C"),
                    #rx.icon("heart", color="black"),
                    align="center",
                    width="100%",
                ),
                rx.text(product["title"], font_weight="bold", font_size="1.1em", color="#22282C"),
                rx.hstack(
                    rx.text("Physical: ", font_weight="medium", color="#22282C"),
                    rx.text(f"${product['physical_price']}", font_weight="bold", color="#22282C"),
                    rx.spacer(),
                    rx.button(
                        rx.icon("shopping-cart",color="#22282c",stroke_width=1),
                        "Add",
                        color="#22282C",
                        border="1px solid #E5E7EB",
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
                        rx.icon("zap",color="#22282C",stroke_width=1),
                        "Add",
                        color="#22282C",
                        border="1px solid #E5E7EB",
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
            border="1px solid #E5E7EB",
            border_radius="16px",
            width="330px",
            height="450px"
        )
    )