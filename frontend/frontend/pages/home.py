import reflex as rx
from ..template import template
from reflex.components.component import NoSSRComponent
from typing import Any, Dict, List
import urllib.parse
from typing import Optional
from reflex.event import Event
from ..state import DynamicState, AuthState
from ..config import API_BASE_URL
import re,asyncio
import httpx

category_images = {
    "Living Room": "/images/livingroom.jpg",
    "Office Room": "/images/officeroom.jpg",
    "Bedroom": "/images/bedroom.jpg",
    "Kitchen": "/images/kitchenroom.jpg"
}

class CategoryItem(rx.Base):
    """Model for category with image"""
    name: str
    image: str


class CategoryState(rx.State):
    categories: list[str] = []
    category_items: list[CategoryItem] = []  
    product_types: dict[str, list[str]] = {}  
    selected_category: str = ""  
    is_loading: bool = False
    error_message: str = ""

    async def load_categories(self):
      
        
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        self.is_loading = True
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/products/categories/",
                    cookies=cookies_dict,
                )

                if response.status_code == 200:
                    data = response.json()
                    raw_categories = data.get("categories", [])

                    cleaned = []
                    items = []
                    
                    for cat in raw_categories:
                        name = cat.strip()
                        if name not in cleaned:
                            cleaned.append(name)
                           
                            img_path = category_images.get(name, "/images/default.jpg")
                            items.append(CategoryItem(name=name, image=img_path))
                           
                    self.categories = cleaned
                    self.category_items = items
                    
                else:
                    self.error_message = "Failed to load categories"
                 
        except Exception as e:
            self.error_message = f"Error: {str(e)}"

        finally:
            self.is_loading = False

def hover_photo(name: str, img: str, link: str) -> rx.Component:
    return rx.vstack(
        rx.link(
            rx.box(
                rx.image(
                    src=img,
                    width="100%",
                    height="250px",
                    object_fit="cover",
                ),
                rx.box(
                    rx.button(
                        name,
                        background_color="rgba(0,0,0,0.7)",
                        color="white",
                        padding="30px 10px",
                        cursor="pointer",
                        font_size="20px",
                        font_weight="bold",
                        font_family="Racing Sans One",
                    ),
                    position="absolute",
                    top="50%",
                    left="50%",
                    transform="translate(-50%, -50%)",
                    opacity="0",
                    transition="opacity 0.3s ease",
                    _hover={"opacity": "1"},
                ),
                position="relative",
                overflow="hidden",
                _hover={"cursor": "pointer"},
            ),
            href=link,
        ),
       rx.link(
            rx.text(
                name,
                font_size="16px",
                font_weight="bold",
                color="#22282C",
                text_align="center",
                margin_top="8px",
            ),
            href=link,
        ),
        spacing="2",
        align="center",
    )


def product_spot(x: str, y: str, name: str, price: str, url: str) -> rx.Component:
   
    return rx.box(
        rx.hover_card.root(
            rx.hover_card.trigger(
                rx.button(
                    "●",
                    size="2",
                    border_radius = "50px",
                    background_color= "rgba(0, 0, 0, 0.4)", 
                    color="white",
                    font_size="25px",
                    cursor="pointer",
                    padding="10px 5px",
                    border="1px solid grey",
                    _hover={
                        "transform": "scale(1.2)",      
                     
                    },
                ),
            ),
            rx.hover_card.content(
                rx.vstack(
                    rx.text(name, font_weight="bold", color="#22282c", font_size="12px"),
                    rx.text(price, color="black",font_size = "16px",font_weight="bold"),
                    rx.link("View >", href=url, color="#22282c",font_size = "12px"),
                ),
                side="right",
                style={"background": "white", "padding": "10px", "border_radius": "8px"},
            ),
        ),
        position="absolute",
        top=y,
        left=x,
    )



def ikea_showcase_layout() -> rx.Component:
    """IKEA-style product showcase matching the reference image"""
    return rx.box(
        rx.hstack(
           
            rx.box(
                rx.image(
                    src="/images/room.jpg",
                    width="100%",
                    height="100%",
                    object_fit="cover",
                ),
            
                
                rx.box(
                    rx.hstack(
                        rx.vstack(
                            rx.text("MALM", font_weight="700", font_size="15px", color="#111"),
                            rx.text("Bed frame, high", font_size="12px", color="#484848"),
                            rx.hstack(
                                rx.text("7,290", font_weight="700", font_size="22px", color="#111"),
                                rx.text("THB", font_size="13px", color="#484848"),
                                spacing="1",
                                align_items="baseline",
                            ),
                            align_items="start",
                            spacing="0",
                        ),
                        rx.box(
                            rx.text("›", font_size="24px", color="#484848",on_click=rx.redirect("/product_detail")),
                            display="flex",
                            align_items="center",
                        ),
                        justify_content="space-between",
                        align_items="center",
                        width="100%",
                    ),
                    position="absolute",
                    top="39%",
                    left="30%",
                    bg="white",
                    padding="14px 16px",
                    box_shadow="0 2px 8px rgba(0,0,0,0.12)",
                    width="190px",
                    cursor="pointer",
                    transition="all 0.2s ease",
                    _hover={
                        "box_shadow": "0 4px 12px rgba(0,0,0,0.18)",
                        "transform": "translateY(-1px)",
                    },
                ),
                product_spot("20%", "80%", "Modern Sofa", "299 THB", "/product_detail"),
                
                position="relative",
                width="40%",
                height="810px",
                overflow="hidden",
            ),
           
            rx.vstack(
               
                rx.box(
                    rx.image(
                        src="/images/roomChair.png",
                        width="100%",
                        height="100%",
                        object_fit="cover",
                    ),
                    
                    product_spot("60%", "35%", "Modern Chair", "569 THB", "/product_detail"),
                
                    position="relative",
                    height="300px",
                    overflow="hidden",
                    flex="0 0 auto",
                ),
                
              
                rx.box(
                    rx.image(
                        src="/images/roomSofa.png",
                        width="100%",
                        height="100%",
                        object_fit="cover",
                    ),
                    product_spot("30%", "30%", "Bedside Table", "799 THB", "/product_detail"),
                    product_spot("60%", "70%", "Modern Sofa", "299 THB", "/product_detail"),
                    position="relative",
                    height="500px",
                    overflow="hidden",
                    flex="0 0 auto",
                ),
                width="30%",
                spacing="3",
                align_items="stretch",
                height="800px",
                justify_content="flex-start",
            ),

            rx.vstack(
    
                rx.box(
                    rx.image(
                        src="/images/roomWardrobe.png",
                        width="100%",
                        height="100%",
                        object_fit="cover",
                    ),
                    product_spot("48%", "30%", "Wooden Wardrobe", "1909 THB", "/product_detail"),
                    product_spot("70%", "80%", "Bedside Table", "249 THB", "/product_detail"),
                   
                    position="relative",
                    height="550px",
                    overflow="hidden",
                    flex="0 0 auto",
                ),
                
              
                rx.box(
                    rx.image(
                        src="/images/roomShelf.png",
                        width="100%",
                        height="100%",
                        object_fit="cover",
                    ),
                    product_spot("40%", "25%", "Book Shelf", "799 THB", "/product_detail"),
                    position="relative",
                    height="250px",
                    overflow="hidden",
                    flex="0 0 auto",
                ),
                width="30%",
                spacing="3",
                align_items="stretch",
                height="800px",
                justify_content="flex-start",
            ),
            
            width="100%",
            spacing="3",
            align_items="stretch",
            padding="10px 0",
        ),
        width="100%",
        margin_bottom="50px",
    )


def home_content() -> rx.Component:

    return rx.box(
    
    ikea_showcase_layout(), 

    rx.center(
        rx.text("Design your Space",font_size = "2rem", font_weight="bold",color="#22282c",font_family="Racing Sans One",text_align="center"),
    ),
    rx.center(
         rx.text("Whether it's your living room, bedroom, or office, we've got the perfect pieces to match your style.",font_size = "16px", color="#22282c",margin_bottom="50px"),
    ),

    rx.cond(
        CategoryState.is_loading,
        rx.center(
            rx.spinner(size="3"),
            margin_bottom="2rem"
        ),
        rx.box()
    ),
 
    rx.hstack(
        rx.foreach(
            CategoryState.category_items,
            lambda item: rx.link(
                rx.vstack(
                    rx.image(
                        src=item.image,
                        width="300px",
                        height="250px",
                        object_fit="cover",
                        border_radius="10px",
                        _hover={
                            "cursor": "pointer",
                            "opacity": "0.8",
                            "transition": "opacity 0.3s"
                        }
                    ),
                    rx.text(
                        item.name,
                        font_size="16px",
                        font_weight="bold",
                        text_align="center",
                        margin_top="8px"
                    ),
                    spacing="2",
                    align="center",
                 
                ),
                href=f"/rooms/{item.name.lower().replace(' ', '-')}",
                style={"textDecoration": "none","color":"#22282c"}
            )
        ),
        justify="center",
        wrap="wrap",
        spacing="4",
        margin_bottom="3rem"
    ),

    rx.hstack(
        rx.vstack(
            rx.text("UNIQUE & STYLISH COLLECTIONS",font_size="14px"),
            rx.hstack(
                rx.text(
                "Create Your",
                font_size="2rem",
                font_family="Racing Sans One",
                font_weight="bold",
                line_height="1.5",
            ),
                rx.text("Interior",font_size="2rem",font_family="Praise",font_weight="bold",font_style="italic"),
            ),
            rx.text("that Inspire everyday",font_size="1.5rem"),
            rx.text("Explore your dream furniture in stunning 3D AR/VR and see exactly how it fits your space before you buy",margin_bottom="2rem",font_size="14px"),
            rx.button("Explore More",style=button_style, ),
            color="#22282C",
            width="50%",    
        ),
        rx.box(
            rx.video(
                url="/videos/demo.mp4",
                controls=True,
                auto_play=True,
                loop=True,
                muted=False,
                width="100%",
                height="300px",
                border_radius="10px",
               
            ),
            width="50%",
            float="right",
           
        ),
        align_items="flex-start",
        width="100%", 
        margin_bottom="50px"
   
    ),
   
        features_section(),

    rx.hstack(
        rx.vstack(
            rx.text("Up To"),
            rx.text(
                "50% OFF",
                font_size="2.5rem",
                font_family="Racing Sans One",
                font_weight="bold",
                font_style="italic",
                line_height="1.5",
            ),
            rx.text("Discover the perfect sofa for your home and enjoy amazing savings while this promotion lasts.",margin_bottom="2rem"),
            rx.button("Shop Now",style=button_style, on_click = rx.redirect("/shop")),
            color="#22282C",
            width="40%",    
        ),
        rx.box(           
            rx.image(
                src="/images/sofa_grey.jpg",
                alt="Home Image",    border_radius="10px",
            ),
            width="60%",   
            float="right",   
         
        ),
        margin_bottom="1rem",
   
    ),
         footer(),

    
    height="100%",
    on_mount=CategoryState.load_categories,
  
)

def feature_card(icon_src: str, title: str, description: str) -> rx.Component:
    """Premium feature card with animations."""
    return rx.box(
        rx.vstack(
       
            rx.box(
                rx.image(
                    src=icon_src,
                    width="64px",
                    height="64px",
                    style={"object_fit": "contain"},
                    border_radius = "0.5rem"
                ),
                padding="20px",
                border_radius="16px",
                display="flex",
                align_items="center",
                justify_content="center",
                width="104px",
                height="104px",
                position="relative",
                transition="all 0.3s ease",
                _before={
                    "content": '""',
                    "position": "absolute",
                    "top": "-4px",
                    "right": "-4px",
                    "width": "100%",
                    "height": "100%",
                    "border_radius": "16px",
                    "transition": "all 0.3s ease",
                },
            ),
            
            # Number badge
            rx.box(
                rx.text(
                    "✓",
                    font_size="18px",
                    font_weight="900",
                    color="#22282c"
                ),
                padding="4px 8px",
                border_radius="8px",
                width="fit-content",
            ),
            
            # Title
            rx.text(
                title,
                font_size="20px",
                font_weight="800",
                color="#22282C",
                text_align="center",
                letter_spacing="-0.5px",
            ),
            
            # Description with better styling
            rx.text(
                description,
                font_size="14px",
                color="#6B7280",
                text_align="center",
                line_height="1.6",
                font_weight="500",
            ),
            
            spacing="2",
            align_items="center",
            width="100%",
        ),
        padding="40px 28px",
        border="2px solid #E5E7EB",
        border_radius="20px",
        background="white",
        width="100%",
        position="relative",
        overflow="hidden",
        transition="all 0.4s cubic-bezier(0.23, 1, 0.320, 1)",
        _before={
            "content": '""',
            "position": "absolute",
            "top": "0",
            "left": "-100%",
            "width": "100%",
            "height": "100%",
            "transition": "left 0.5s ease",
        },
        _hover={
            "transform": "translateY(-8px) scale(1.02)",
        },
    )


def features_section() -> rx.Component:
    """Ultra-premium features showcase section."""
    return rx.box(
        rx.vstack(
            
            # Section Header
            rx.vstack(
                rx.text(
                    "Why Choose",
                    font_size="14px",
                    font_weight="700",
                    color="#929FA7",
                    text_transform="uppercase",
                    letter_spacing="2px",
                ),
                rx.heading(
                    "Digital Home Platform",
                    font_family="Racing Sans One",
                    font_size = "2rem",
                    color="#22282C",
                    text_align="center",
                    weight="bold",
                    margin_bottom="8px",
                ),
             
                spacing="2",
                align_items="center",
                margin_bottom="10px",
                width="100%",
            ),
            
            # Feature Cards Grid
            rx.grid(
                feature_card(
                    "/images/high_quality.png",
                    "Premium Quality",
                    "Handpicked curated products from top designers worldwide",
                   
                ),
                feature_card(
                    "/images/location.png",
                    "Express Delivery",
                    "Fast and secure shipping with real-time tracking",
                   
                ),
                feature_card(
                    "/images/3D.png",
                    "AR/VR Experience",
                    "Visualize furniture in your space with immersive 3D preview",
                    
                ),
                feature_card(
                    "/images/service.png",
                    "24/7 Support",
                    "Dedicated customer service available round the clock",
                    
                ),
                columns="4",
                spacing="8",
                width="100%",
                auto_rows="1fr",
            ),
            
            spacing="8",
            width="100%",
            padding="40px 30px",
            align_items="center",
        ),
        background="linear-gradient(135deg, #FFFFFF 0%, #F9FAFB 50%, #F3F4F6 100%)",
        border_radius="32px",
        border="1px solid #E5E7EB",
        width="100%",
        margin_top="30px",
        margin_bottom="30px",
        box_shadow="0 2px 8px rgba(0, 0, 0, 0.04)",
    )


class NewsletterState(rx.State):
    """State for newsletter subscription."""
    email: str = ""
    is_subscribing: bool = False
    subscribe_message: str = ""
    subscribe_status: str = ""  # "idle", "loading", "success", "error"
    
    def set_email(self, value: str):
        """Update email input."""
        self.email = value
    
    def validate_email(self) -> bool:
        """Validate email format."""
        email_pattern = r'^\S+@\S+\.\S+$'

        return re.match(email_pattern, self.email) is not None
    
    def clear_subscription(self):
        """Clear subscription form and message after delay."""
        self.email = ""
        self.subscribe_message = ""
        self.subscribe_status = "idle"
    
    show_modal: bool = False
    
    def open_modal(self):
        """Open subscription modal."""
        self.show_modal = True
    
    def close_modal(self):
        """Close subscription modal."""
        self.show_modal = False
        self.clear_subscription()
    
    async def subscribe_newsletter(self):
        self.subscribe_message = ""
        self.subscribe_status = "loading"
        self.is_subscribing = True

        if not self.email.strip():
            self.subscribe_message = "Please enter your email address"
            self.subscribe_status = "error"
            self.is_subscribing = False
            return

        if not self.validate_email():
            self.subscribe_message = "Please enter a valid email address"
            self.subscribe_status = "error"
            self.is_subscribing = False
            return

        # Simulate API call
        await asyncio.sleep(0.2)

        # ✅ Open modal first (triggers re-render)
        self.open_modal()

        # Then mark success
        self.subscribe_message = "✓ Successfully subscribed!"
        self.subscribe_status = "success"
        self.is_subscribing = False



def subscription_modal() -> rx.Component:
    """Modal showing subscription confirmation."""
    return rx.cond(
        NewsletterState.show_modal,
        rx.box(
            rx.box(
                rx.vstack(
                    # Close Button
                    rx.box(
                        rx.icon(
                            "x",
                            size=28,
                            color="#6B7280",
                            cursor="pointer",
                            on_click=NewsletterState.close_modal,
                            _hover={"color": "#22282C"},
                        ),
                        width="100%",
                        display="flex",
                        justify_content="flex-end",
                    ),
                    
                    # Success Icon
                    rx.cond(
                        NewsletterState.subscribe_status == "success",
                        rx.box(
                            rx.text("✓", font_size="64px", color="#10B981"),
                            width="100%",
                            text_align="center",
                            margin_bottom="16px",
                        ),
                        rx.box(
                            rx.text("!", font_size="64px", color="#EF4444"),
                            width="100%",
                            text_align="center",
                            margin_bottom="16px",
                        ),
                    ),
                    
                    # Title
                    rx.heading(
                        rx.cond(
                            NewsletterState.subscribe_status == "success",
                            "Subscription Confirmed!",
                            "Subscription Error"
                        ),
                        size="6",
                        color="#22282C",
                        text_align="center",
                    ),
                    
                    # Message
                    rx.text(
                        NewsletterState.subscribe_message,
                        font_size="16px",
                        color="#6B7280",
                        text_align="center",
                        line_height="1.6",
                    ),
                    
                    # Additional Info (only on success)
                    rx.cond(
                        NewsletterState.subscribe_status == "success",
                        rx.vstack(
                            rx.box(
                                rx.hstack(
                                    rx.icon("mail", size=20, color="#2E6FF2"),
                                    rx.text(
                                        "Check your email for exclusive offers",
                                        font_size="14px",
                                        color="#22282C",
                                    ),
                                    spacing="2",
                                    align_items="center",
                                ),
                                padding="16px",
                                background="#EFF6FF",
                                border_radius="8px",
                                width="100%",
                            ),
                            rx.box(
                                rx.hstack(
                                    rx.icon("gift", size=20, color="#F59E0B"),
                                    rx.text(
                                        "Get 10% discount on your first purchase",
                                        font_size="14px",
                                        color="#22282C",
                                    ),
                                    spacing="2",
                                    align_items="center",
                                ),
                                padding="16px",
                                background="#FFFBEB",
                                border_radius="8px",
                                width="100%",
                            ),
                            spacing="3",
                            width="100%",
                            margin_top="16px",
                        ),
                        rx.fragment(),
                    ),
                    
                    # Email Display
                    rx.box(
                        rx.text(
                            f"Email: {NewsletterState.email}",
                            font_size="14px",
                            color="#929FA7",
                            text_align="center",
                        ),
                        padding="16px",
                        background="#F3F4F6",
                        border_radius="8px",
                        width="100%",
                    ),
                    
                    # Close Button
                    rx.button(
                        "Got It!",
                        width="100%",
                        padding="14px",
                        background=rx.cond(
                            NewsletterState.subscribe_status == "success",
                            "linear-gradient(135deg, #2E6FF2 0%, #0078D4 100%)",
                            "linear-gradient(135deg, #EF4444 0%, #DC2626 100%)"
                        ),
                        color="white",
                        border="none",
                        border_radius="10px",
                        font_weight="600",
                        cursor="pointer",
                        font_size="16px",
                        on_click=NewsletterState.close_modal,
                        _hover={
                            "box_shadow": "0 8px 20px rgba(46, 111, 242, 0.3)",
                        },
                        margin_top="20px",
                    ),
                    
                    spacing="4",
                    width="100%",
                ),
                background="white",
                padding="40px",
                border_radius="16px",
                width="500px",
                max_width="90vw",
                box_shadow="0 20px 60px rgba(0, 0, 0, 0.2)",
                position="relative",
            ),
            position="fixed",
            top="0",
            left="0",
            right="0",
            bottom="0",
            background="rgba(0, 0, 0, 0.5)",
            display="flex",
            align_items="center",
            justify_content="center",
            z_index="1000",
        ),
    )


def footer() -> rx.Component:
    """Premium footer for Digital Home Platform."""
    return rx.box(
        rx.vstack(
            # Main Footer Content
            rx.vstack(
                # Top Section with Logo and Description
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            "Digital Home",
                            font_size="28px",
                            font_weight="800",
                            color="white",
                        ),
                        rx.text(
                            "Premium Curated Design Products",
                            font_size="14px",
                            color="#929FA7",
                        ),
                        spacing="2",
                        margin_bottom="20px",
                    ),
                    rx.spacer(),
                    rx.vstack(
                        rx.text(
                            "Follow Us",
                            font_size="14px",
                            font_weight="700",
                            color="white",
                            text_transform="uppercase",
                            letter_spacing="1px",
                        ),
                        rx.hstack(
                            rx.link(
                                rx.box(
                                    rx.icon("facebook", size=20, color="white"),
                                    padding="12px",
                                    border_radius="8px",
                                    background="#374151",
                                    cursor="pointer",
                                    transition="all 0.3s ease",
                                    _hover={
                                        "background": "#2E6FF2",
                                        "transform": "translateY(-2px)",
                                    },
                                ),
                                href="https://facebook.com",
                                is_external=True,
                            ),
                            rx.link(
                                rx.box(
                                    rx.icon("twitter", size=20, color="white"),
                                    padding="12px",
                                    border_radius="8px",
                                    background="#374151",
                                    cursor="pointer",
                                    transition="all 0.3s ease",
                                    _hover={
                                        "background": "#1DA1F2",
                                        "transform": "translateY(-2px)",
                                    },
                                ),
                                href="https://twitter.com",
                                is_external=True,
                            ),
                            rx.link(
                                rx.box(
                                    rx.icon("instagram", size=20, color="white"),
                                    padding="12px",
                                    border_radius="8px",
                                    background="#374151",
                                    cursor="pointer",
                                    transition="all 0.3s ease",
                                    _hover={
                                        "background": "#E1306C",
                                        "transform": "translateY(-2px)",
                                    },
                                ),
                                href="https://instagram.com",
                                is_external=True,
                            ),
                            rx.link(
                                rx.box(
                                    rx.icon("linkedin", size=20, color="white"),
                                    padding="12px",
                                    border_radius="8px",
                                    background="#374151",
                                    cursor="pointer",
                                    transition="all 0.3s ease",
                                    _hover={
                                        "background": "#0077B5",
                                        "transform": "translateY(-2px)",
                                    },
                                ),
                                href="https://linkedin.com",
                                is_external=True,
                            ),
                            spacing="3",
                            align_items="center",
                        ),
                        spacing="3",
                        align_items="flex-start",
                    ),
                    width="100%",
                    align_items="flex-start",
                    padding_bottom="40px",
                    border_bottom="1px solid #374151",
                ),
                
                # Newsletter Subscription
                rx.vstack(
                    rx.text(
                        "Subscribe to Our Newsletter",
                        font_size="18px",
                        font_weight="700",
                        color="white",
                    ),
                    rx.text(
                        "Get exclusive offers and new product launches delivered to your inbox",
                        font_size="14px",
                        color="#929FA7",
                    ),
                    
                    # Email Input and Subscribe Button
                    rx.hstack(
                        rx.input(
                            placeholder="Enter your email",
                            value=NewsletterState.email,
                            on_change=NewsletterState.set_email,
                            width="100%",
                            padding="5px",
                            border="1.5px solid #374151",
                            border_radius="10px",
                            background_color="#1F2937",
                            color="white",
                            font_size="14px",
                            _placeholder={"color": "#6B7280"},
                            _focus={
                                "border_color": "#2E6FF2",
                                "box_shadow": "0 0 0 3px rgba(46, 111, 242, 0.1)",
                            },
                            transition="all 0.2s ease",
                            is_disabled=NewsletterState.is_subscribing,
                        ),
                        rx.button(
                            rx.cond(
                                NewsletterState.is_subscribing,
                                rx.hstack(
                                    rx.spinner(size="2"),
                                    rx.text("Subscribing...", font_weight="600"),
                                    spacing="2",
                                    align_items="center",
                                ),
                                rx.hstack(
                                    rx.icon("send", size=16),
                                    rx.text("Subscribe", font_weight="600"),
                                    spacing="2",
                                    align_items="center",
                                ),
                            ),
                            padding="14px 24px",
                            background="linear-gradient(135deg, #2E6FF2 0%, #0078D4 100%)",
                            color="white",
                            border="none",
                            border_radius="10px",
                            cursor="pointer",
                            transition="all 0.3s ease",
                            is_disabled=NewsletterState.is_subscribing,
                            _hover={
                                "box_shadow": "0 8px 20px rgba(46, 111, 242, 0.3)",
                                "transform": "translateY(-2px)",
                            },
                            on_click=NewsletterState.subscribe_newsletter,
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    
                 
                    rx.cond(
                        NewsletterState.subscribe_message != "",
                        rx.box(
                            rx.text(
                                NewsletterState.subscribe_message,
                                font_size="13px",
                                color=rx.cond(
                                    NewsletterState.subscribe_status == "success",
                                    "#10B981",
                                    "#EF4444"
                                ),
                                font_weight="500",
                            ),
                            padding="12px 16px",
                            border_radius="8px",
                            background=rx.cond(
                                NewsletterState.subscribe_status == "success",
                                "#10B98120",
                                "#EF444420"
                            ),
                            border=rx.cond(
                                NewsletterState.subscribe_status == "success",
                                "1px solid #10B98140",
                                "1px solid #EF444440"
                            ),
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    
                    spacing="4",
                    width="100%",
                    padding="40px 0",
                    border_bottom="1px solid #374151",
                ),
                
              
                rx.grid(
                  
                    rx.vstack(
                        rx.text(
                            "Company",
                            font_size="14px",
                            font_weight="700",
                            color="white",
                            text_transform="uppercase",
                            letter_spacing="1px",
                            margin_bottom="12px",
                        ),
                        rx.link(rx.text("About Us", font_size="14px", color="#929FA7", _hover={"color": "#2E6FF2"}, transition="all 0.2s ease"), href="#"),
                        rx.link(rx.text("Our Team", font_size="14px", color="#929FA7", _hover={"color": "#2E6FF2"}, transition="all 0.2s ease"), href="#"),
                        rx.link(rx.text("Careers", font_size="14px", color="#929FA7", _hover={"color": "#2E6FF2"}, transition="all 0.2s ease"), href="#"),
                        rx.link(rx.text("Blog", font_size="14px", color="#929FA7", _hover={"color": "#2E6FF2"}, transition="all 0.2s ease"), href="#"),
                        spacing="3",
                    ),
                    
                   
                    rx.vstack(
                        rx.text(
                            "Support",
                            font_size="14px",
                            font_weight="700",
                            color="white",
                            text_transform="uppercase",
                            letter_spacing="1px",
                            margin_bottom="12px",
                        ),
                        rx.link(rx.text("Contact Us", font_size="14px", color="#929FA7", _hover={"color": "#2E6FF2"}, transition="all 0.2s ease"), href="#"),
                        rx.link(rx.text("FAQs", font_size="14px", color="#929FA7", _hover={"color": "#2E6FF2"}, transition="all 0.2s ease"), href="#"),
                        rx.link(rx.text("Shipping Info", font_size="14px", color="#929FA7", _hover={"color": "#2E6FF2"}, transition="all 0.2s ease"), href="#"),
                        rx.link(rx.text("Returns", font_size="14px", color="#929FA7", _hover={"color": "#2E6FF2"}, transition="all 0.2s ease"), href="#"),
                        spacing="3",
                    ),
                    
                  
                    rx.vstack(
                        rx.text(
                            "Legal",
                            font_size="14px",
                            font_weight="700",
                            color="white",
                            text_transform="uppercase",
                            letter_spacing="1px",
                            margin_bottom="12px",
                        ),
                        rx.link(rx.text("Privacy Policy", font_size="14px", color="#929FA7", _hover={"color": "#2E6FF2"}, transition="all 0.2s ease"), href="#"),
                        rx.link(rx.text("Terms of Service", font_size="14px", color="#929FA7", _hover={"color": "#2E6FF2"}, transition="all 0.2s ease"), href="#"),
                        rx.link(rx.text("Cookie Policy", font_size="14px", color="#929FA7", _hover={"color": "#2E6FF2"}, transition="all 0.2s ease"), href="#"),
                        rx.link(rx.text("Sitemap", font_size="14px", color="#929FA7", _hover={"color": "#2E6FF2"}, transition="all 0.2s ease"), href="#"),
                        spacing="3",
                    ),
                    
                    
                    rx.vstack(
                        rx.text(
                            "Contact",
                            font_size="14px",
                            font_weight="700",
                            color="white",
                            text_transform="uppercase",
                            letter_spacing="1px",
                            margin_bottom="12px",
                        ),
                        rx.hstack(
                            rx.icon("phone", size=16, color="#2E6FF2"),
                            rx.link(rx.text("+1 (555) 123-4567", font_size="14px", color="#929FA7", _hover={"color": "#2E6FF2"}, transition="all 0.2s ease"), href="tel:+15551234567"),
                            spacing="2",
                            align_items="center",
                        ),
                        rx.hstack(
                            rx.icon("mail", size=16, color="#2E6FF2"),
                            rx.link(rx.text("support@digitalhome.com", font_size="14px", color="#929FA7", _hover={"color": "#2E6FF2"}, transition="all 0.2s ease"), href="mailto:support@digitalhome.com"),
                            spacing="2",
                            align_items="center",
                        ),
                        rx.hstack(
                            rx.icon("map-pin", size=16, color="#2E6FF2"),
                            rx.text("Bangkok, Thailand", font_size="14px", color="#929FA7"),
                            spacing="2",
                            align_items="center",
                        ),
                        spacing="3",
                    ),
                    
                    columns="4",
                    spacing="8",
                    width="100%",
                    padding="40px 0",
                    border_bottom="1px solid #374151",
                ),
                
            
                rx.hstack(
                    rx.text(
                        "© 2024 Digital Home Platform. All rights reserved.",
                        font_size="12px",
                        color="#6B7280",
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.text("Made with ", font_size="12px", color="#6B7280"),
                        rx.text("❤️", font_size="14px"),
                        rx.text(" in Bangkok", font_size="12px", color="#6B7280"),
                        spacing="1",
                        align_items="center",
                    ),
                    width="100%",
                    align_items="center",
                    padding="24px 0",
                ),
                
                spacing="0",
                width="100%",
            ),
            
            spacing="0",
            width="100%",
        ),
     
        subscription_modal(),
        background="linear-gradient(135deg, #22282C 0%, #2A3037 100%)",
        padding="60px 50px",
        width="100%",
    )

@rx.page(route="/home", on_load=CategoryState.load_categories)
def home_page() -> rx.Component:
    return template(home_content)

button_style = {
    "background_color": "#22282C",
    "color": "white",
    "font_size": "16px",
    "padding": "20px 30px",
    "cursor": "pointer",
    "font_weight": "bold",
    "border_radius": "8px",
    "_hover": {
        "background_color": "white",
        "color": "#22282C",
        "border": "1px solid #929FA7"
    }
}

icon_style = {
    "background_color":"white", 
    "border_radius":"100px", 
    "padding":"8px",

}

load_button = {
   "background_color": "white",
    "border": "1px solid #929FA7",
    "color": "#22282c",
    "font_size": "12px",
    "padding": "20px 30px",
    "cursor": "pointer",
    "font_weight": "bold",
    "border_radius": "20px",
    "margin_top": "20px",
    "_hover": {
        "background_color": "#22282c",
        "color": "white",
       
    } 
}


######################### DON'T REMOVE THIS #########################################
'''rx.vstack(
        
        rx.hstack(
        
            rx.vstack(
                hover_photo("Bedroom", "/images/bedroom.jpg", "/rooms/bedroom"),
        
            ),

            rx.vstack(
                hover_photo("Office Room", "/images/officeroom.jpg", "/rooms/officeroom"),
        
            ),
            
            rx.vstack(
                hover_photo("Living Room", "/images/livingroom.jpg", "/rooms/livingroom"),
                
            ),
            rx.vstack(
                hover_photo("Kitchen", "/images/kitchenroom.jpg", "/rooms/kitchen"),
        
            ),
          
        
            ),
              rx.center(
                 rx.button(
                "Load More Rooms", style = load_button
            ),
           
            width="100%",
            justify="between",
            margin_bottom="50px",
            align_item = "center"
            
        ),
   
    ),
   '''
#testimonials_session
'''rx.hstack(
        rx.button("←", bg="#212529", color="white", border_radius="50%",width="40px",height="40px"),
        rx.hstack(
            *testimonials_section(),   
            align="center",
            justify="center"
        ),
        rx.button("→", bg="#212529", color="white", border_radius="50%",width="40px",height="40px"),
        width="100%",
        justify="center",
        align = "center",
        padding="40px",
    ),'''

#function

def testimonials_section():
    card_style = {
        "border_radius": "10px",
        "padding": "20px",
        "width": "300px",
        "min_height": "200px",
        "text_align": "center",
        "box_shadow": "0 4px 8px rgba(0, 0, 0, 0.1)"
    }

    reviews = [
        {"name": "Cyntra", "rating": 5, "text": "I absolutely love my new sofa! The color matches perfectly with my living room, and it's even more comfortable than I expected. Delivery was quick and hassle-free", "bg": "#e0e5e8","color":"black"},
        {"name": "Pop", "rating": 5, "text": "I absolutely love my new sofa! The color matches perfectly with my living room, and it's even more comfortable than I expected. Delivery was quick and hassle-free", "bg": "#212529", "color": "white"},
        {"name": "Mai", "rating": 5, "text": "I absolutely love my new sofa! The color matches perfectly with my living room, and it's even more comfortable than I expected. Delivery was quick and hassle-free", "bg": "#e0e5e8","color":"black"},
    ]

    '''review_cards = []
    for review in reviews:
        review_cards.append(
            rx.vstack(
                rx.hstack(
                    *[rx.text("★", color="#FFA500") for _ in range(review["rating"])],
                    spacing="2"
                   
                ),
                rx.text(review["name"], font_weight="bold", font_size="1.1em",color=review.get("color", "black")),
                rx.text(review["text"], font_size="0.9em", color=review.get("color", "black")),
                bg=review["bg"],
                **card_style
            ),
            
        )

    return review_cards'''