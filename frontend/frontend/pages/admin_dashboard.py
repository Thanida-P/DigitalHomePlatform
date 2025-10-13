import reflex as rx
from typing import List, Dict
from ..state import AuthState

class AdminDashboardState(rx.State):
    # Product list
    products: List[Dict] = []
    filtered_products: List[Dict] = []
    
    # Search and filter
    search_query: str = ""
    selected_room: str = "all"
    selected_category: str = "all"
    
    # Add/Edit product form
    show_add_modal: bool = False
    show_edit_modal: bool = False
    editing_product_id: str = ""
    
    # Form fields
    product_name: str = ""
    description: str = ""
    physical_price: str = ""
    digital_price: str = ""
    category: str = ""
    room_type: str = "livingroom"
    rating: str = "5.0"
    preview_image: str = ""
    hover_image: str = ""
    model_file: str = ""
    material_file: str = ""
    
    # Stats
    total_products: int = 0
    total_sold: int = 0
    total_revenue: float = 0.0
    
    def load_products(self):
        """Load all products from data"""
        from ..rooms_data import rooms_data
        
        all_products = []
        for room_key, room_data in rooms_data.items():
            for product in room_data["products"]:
                product_copy = product.copy()
                product_copy["room"] = room_key
                product_copy["room_title"] = room_data["title"]
                product_copy["id"] = f"{room_key}_{product['title'].replace(' ', '_')}"
                all_products.append(product_copy)
        
        self.products = all_products
        self.filtered_products = all_products
        self.total_products = len(all_products)
        self.apply_filters()
    
    def apply_filters(self):
        """Apply search and filters"""
        filtered = self.products
        
        # Search filter
        if self.search_query:
            filtered = [
                p for p in filtered 
                if self.search_query.lower() in p["title"].lower()
            ]
        
        # Room filter
        if self.selected_room != "all":
            filtered = [p for p in filtered if p["room"] == self.selected_room]
        
        # Category filter
        if self.selected_category != "all":
            filtered = [p for p in filtered if p["category"] == self.selected_category]
        
        self.filtered_products = filtered
    
    def set_search_query(self, value: str):
        self.search_query = value
        self.apply_filters()
    
    def set_room_filter(self, value: str):
        self.selected_room = value
        self.apply_filters()
    
    def set_category_filter(self, value: str):
        self.selected_category = value
        self.apply_filters()
    
    # Modal controls
    def open_add_modal(self):
        self.show_add_modal = True
        self.clear_form()
    
    def close_add_modal(self):
        self.show_add_modal = False
        self.clear_form()
    
    def open_edit_modal(self, product: Dict):
        self.show_edit_modal = True
        self.editing_product_id = product["id"]
        self.product_name = product["title"]
        self.description = product.get("description", "")
        self.physical_price = str(product["physical_price"])
        self.digital_price = str(product["digital_price"])
        self.category = product["category"]
        self.room_type = product["room"]
        self.rating = str(product["rating"])
        self.preview_image = product["image"]
        self.hover_image = product["hover_image"]
        self.model_file = product["model_url"]
    
    def close_edit_modal(self):
        self.show_edit_modal = False
        self.clear_form()
    
    def clear_form(self):
        self.product_name = ""
        self.description = ""
        self.physical_price = ""
        self.digital_price = ""
        self.category = ""
        self.room_type = "livingroom"
        self.rating = "5.0"
        self.preview_image = ""
        self.hover_image = ""
        self.model_file = ""
        self.material_file = ""
        self.editing_product_id = ""
    
    # Form setters
    def set_product_name(self, value: str):
        self.product_name = value
    
    def set_description(self, value: str):
        self.description = value
    
    def set_physical_price(self, value: str):
        self.physical_price = value
    
    def set_digital_price(self, value: str):
        self.digital_price = value
    
    def set_category(self, value: str):
        self.category = value
    
    def set_room_type(self, value: str):
        self.room_type = value
    
    def set_rating(self, value: str):
        self.rating = value
    
    def set_preview_image(self, value: str):
        self.preview_image = value
    
    def set_hover_image(self, value: str):
        self.hover_image = value
    
    def set_model_file(self, value: str):
        self.model_file = value
    
    def set_material_file(self, value: str):
        self.material_file = value
    
    def save_product(self):
        """Save new product (placeholder - implement API call)"""
        print(f"Saving product: {self.product_name}")
        # TODO: Implement API call to save product
        self.close_add_modal()
        self.load_products()
    
    def update_product(self):
        """Update existing product (placeholder - implement API call)"""
        print(f"Updating product: {self.editing_product_id}")
        # TODO: Implement API call to update product
        self.close_edit_modal()
        self.load_products()
    
    def delete_product(self, product_id: str):
        """Delete product (placeholder - implement API call)"""
        print(f"Deleting product: {product_id}")
        # TODO: Implement API call to delete product
        self.load_products()


def stats_card(title: str, value: str, icon: str, color: str) -> rx.Component:
    """Stats card component"""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon(icon, size=24, color=color),
                rx.spacer(),
                rx.badge("+12%", color_scheme="green", variant="soft"),
                width="100%",
            ),
            rx.vstack(
                rx.text(title, size="2", color="#64748B", weight="medium"),
                rx.heading(value, size="7", weight="bold", color="#0F172A"),
                spacing="1",
                align="start",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def product_card(product: Dict) -> rx.Component:
    """Individual product card"""
    return rx.card(
        rx.vstack(
            # Product image
            rx.image(
                src=product["image"],
                width="100%",
                height="200px",
                object_fit="cover",
                border_radius="8px",
            ),
            
            # Product info
            rx.vstack(
                rx.hstack(
                    rx.heading(product["title"], size="4", weight="bold"),
                    rx.spacer(),
                    rx.badge(product["category"], variant="soft"),
                    width="100%",
                ),
                
                rx.hstack(
                    rx.text(product["room_title"], size="2", color="#64748B"),
                    rx.spacer(),
                    rx.hstack(
                        rx.icon("star", size=16, color="#F59E0B"),
                        rx.text(product["rating"], size="2", weight="medium"),
                        spacing="1",
                    ),
                    width="100%",
                ),
                
                rx.hstack(
                    rx.vstack(
                        rx.text("Physical", size="1", color="#64748B"),
                        rx.text(f"${product['physical_price']}", size="3", weight="bold", color="#0F172A"),
                        spacing="0",
                        align="start",
                    ),
                    rx.vstack(
                        rx.text("Digital", size="1", color="#64748B"),
                        rx.text(f"${product['digital_price']}", size="3", weight="bold", color="#6366F1"),
                        spacing="0",
                        align="start",
                    ),
                    spacing="6",
                    width="100%",
                ),
                
                # Action buttons
                rx.hstack(
                    rx.button(
                        rx.icon("pencil", size=16),
                        "Edit",
                        variant="soft",
                        size="2",
                        on_click=lambda: AdminDashboardState.open_edit_modal(product),
                    ),
                    rx.button(
                        rx.icon("trash-2", size=16),
                        "Delete",
                        variant="soft",
                        color_scheme="red",
                        size="2",
                        on_click=lambda: AdminDashboardState.delete_product(product["id"]),
                    ),
                    spacing="2",
                    width="100%",
                ),
                
                spacing="3",
                width="100%",
            ),
            
            spacing="3",
            width="100%",
        ),
        width="100%",
    )


def product_form_modal(is_edit: bool = False) -> rx.Component:
    """Modal for adding/editing products"""
    title = "Edit Product" if is_edit else "Add New Product"
    show_state = AdminDashboardState.show_edit_modal if is_edit else AdminDashboardState.show_add_modal
    close_fn = AdminDashboardState.close_edit_modal if is_edit else AdminDashboardState.close_add_modal
    save_fn = AdminDashboardState.update_product if is_edit else AdminDashboardState.save_product
    
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title(title),
            rx.dialog.description(
                "Fill in the product details below",
                size="2",
                margin_bottom="16px",
            ),
            
            rx.vstack(
                # Product Name
                rx.vstack(
                    rx.text("Product Name *", size="2", weight="medium"),
                    rx.input(
                        placeholder="Modern Luxury Sofa",
                        value=AdminDashboardState.product_name,
                        on_change=AdminDashboardState.set_product_name,
                    ),
                    spacing="1",
                    width="100%",
                ),
                
                # Description
                rx.vstack(
                    rx.text("Description", size="2", weight="medium"),
                    rx.text_area(
                        placeholder="Enter product description...",
                        value=AdminDashboardState.description,
                        on_change=AdminDashboardState.set_description,
                        rows="3",
                    ),
                    spacing="1",
                    width="100%",
                ),
                
                # Prices
                rx.hstack(
                    rx.vstack(
                        rx.text("Physical Price ($) *", size="2", weight="medium"),
                        rx.input(
                            placeholder="1299",
                            type="number",
                            value=AdminDashboardState.physical_price,
                            on_change=AdminDashboardState.set_physical_price,
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Digital Price ($) *", size="2", weight="medium"),
                        rx.input(
                            placeholder="99",
                            type="number",
                            value=AdminDashboardState.digital_price,
                            on_change=AdminDashboardState.set_digital_price,
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                
                # Room and Category
                rx.hstack(
                    rx.vstack(
                        rx.text("Room *", size="2", weight="medium"),
                        rx.select(
                            ["livingroom", "bedroom", "kitchen", "officeroom"],
                            value=AdminDashboardState.room_type,
                            on_change=AdminDashboardState.set_room_type,
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    rx.vstack(
                        rx.text("Category *", size="2", weight="medium"),
                        rx.input(
                            placeholder="Sofa",
                            value=AdminDashboardState.category,
                            on_change=AdminDashboardState.set_category,
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                
                # Rating
                rx.vstack(
                    rx.text("Rating (1-5)", size="2", weight="medium"),
                    rx.input(
                        placeholder="4.5",
                        type="number",
                        min="0",
                        max="5",
                        step="0.1",
                        value=AdminDashboardState.rating,
                        on_change=AdminDashboardState.set_rating,
                    ),
                    spacing="1",
                    width="100%",
                ),
                
                # File Uploads
                rx.vstack(
                    rx.text("Preview Image *", size="2", weight="medium"),
                    rx.input(
                        placeholder="/images/product.jpg or upload",
                        value=AdminDashboardState.preview_image,
                        on_change=AdminDashboardState.set_preview_image,
                    ),
                    rx.text("Upload image file", size="1", color="#64748B"),
                    spacing="1",
                    width="100%",
                ),
                
                rx.vstack(
                    rx.text("3D Model File *", size="2", weight="medium"),
                    rx.input(
                        placeholder="/models/product.glb or upload",
                        value=AdminDashboardState.model_file,
                        on_change=AdminDashboardState.set_model_file,
                    ),
                    rx.text("Upload .glb file", size="1", color="#64748B"),
                    spacing="1",
                    width="100%",
                ),
                
                rx.vstack(
                    rx.text("Material File (Optional)", size="2", weight="medium"),
                    rx.input(
                        placeholder="Upload material file",
                        value=AdminDashboardState.material_file,
                        on_change=AdminDashboardState.set_material_file,
                    ),
                    spacing="1",
                    width="100%",
                ),
                
                spacing="4",
                width="100%",
            ),
            
            rx.flex(
                rx.dialog.close(
                    rx.button(
                        "Cancel", 
                        variant="soft", 
                        color_scheme="gray",
                        on_click=close_fn,
                    ),
                ),
                rx.dialog.close(
                    rx.button(
                        "Save Product",
                        on_click=save_fn,
                    ),
                ),
                spacing="3",
                margin_top="16px",
                justify="end",
            ),
            
            max_width="600px",
            padding="24px",
        ),
        open=show_state,
    )


def admin_dashboard() -> rx.Component:
    """Main admin dashboard page"""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading("Product Management", size="8", weight="bold"),
                rx.spacer(),
                rx.button(
                    rx.icon("plus", size=20),
                    "Add Product",
                    size="3",
                    on_click=AdminDashboardState.open_add_modal,
                ),
                width="100%",
                align="center",
            ),
            
            # Stats cards
            rx.grid(
                stats_card("Total Products", AdminDashboardState.total_products.to(str), "package", "#6366F1"),
                stats_card("Total Sold", "1,234", "shopping-cart", "#10B981"),
                stats_card("Revenue", "$48,567", "dollar-sign", "#F59E0B"),
                stats_card("Avg Rating", "4.8", "star", "#EC4899"),
                columns="4",
                spacing="4",
                width="100%",
            ),
            
            # Filters
            rx.card(
                rx.hstack(
                    rx.input(
                        rx.input.slot(rx.icon("search")),
                        placeholder="Search products...",
                        value=AdminDashboardState.search_query,
                        on_change=AdminDashboardState.set_search_query,
                        width="300px",
                    ),
                    rx.select(
                        ["all", "livingroom", "bedroom", "kitchen", "officeroom"],
                        placeholder="All Rooms",
                        value=AdminDashboardState.selected_room,
                        on_change=AdminDashboardState.set_room_filter,
                    ),
                    rx.select(
                        ["all", "Sofa", "Tables", "Chairs", "Beds", "Fridges"],
                        placeholder="All Categories",
                        value=AdminDashboardState.selected_category,
                        on_change=AdminDashboardState.set_category_filter,
                    ),
                    spacing="3",
                    width="100%",
                ),
            ),
            
            # Products grid
            rx.cond(
                AdminDashboardState.filtered_products.length() > 0,
                rx.grid(
                    rx.foreach(
                        AdminDashboardState.filtered_products,
                        product_card,
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
        ),
        
        # Modals
        product_form_modal(is_edit=False),
        product_form_modal(is_edit=True),
        
        padding="40px",
        padding_top="100px",
        min_height="100vh",
        background_color="#F8FAFC",
        
        on_mount=AdminDashboardState.load_products,
    )