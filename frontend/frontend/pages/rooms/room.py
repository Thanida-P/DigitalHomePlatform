import reflex as rx
from ...state import DynamicState
from ...components.product_card import product_list
from ...template import template

def room_content() -> rx.Component:
    return rx.hstack(
        # Sidebar
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
                # You can add product type filters here later
                # rx.vstack(
                #     rx.foreach(
                #         DynamicState.room_categories,
                #         lambda category: rx.link(
                #             rx.hstack(
                #                 rx.icon(tag="chevron-right", size=16),  
                #                 rx.text(category),
                #                 spacing="2",
                #                 align_items="center",
                #             ),
                #             style=menu_item_style(),
                #             href="#"
                #         ),
                #     ),
                #     align_items="start",
                #     width="100%",
                # ),
            ),
            width="280px",  
            height="100%",
            bg="#F9FAFB",
        ),
     
        # Products Section
        rx.box(
            rx.cond(
                DynamicState.is_loading,
                # Loading state
                rx.center(
                    rx.vstack(
                        rx.spinner(size="3"),
                        rx.text("Loading products...", color="#6B7280"),
                        spacing="3",
                    ),
                    width="100%",
                    height="400px",
                ),
                # Loaded state
                rx.cond(
                    DynamicState.room_products.length() > 0,
                    # Products grid
                    rx.grid(
                        rx.foreach(
                            DynamicState.room_products,
                            lambda product: product_list([product])  
                        ),
                        columns="3",
                        spacing="4",
                        width="100%",
                    ),
                    # Empty state
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
        spacing="9",
        width="100%",
        height="100vh",
        padding_top="30px"
    )

def menu_item_style(active: bool = False):
    return {
        "padding": "12px 20px",
        "font_size": "15px",
        "color": "#22282C" if not active else "white",
        "background_color": "#22282C" if active else "transparent",
        "text_decoration": "none",
        "width": "280px",
        "_hover": {
            "background_color": "#E5E7EB" if not active else "#22282C",
        }
    }

@rx.page(route="/rooms/[room]", on_load=DynamicState.on_load)
def room_page() -> rx.Component:
    return template(room_content)