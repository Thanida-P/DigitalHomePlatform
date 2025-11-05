import reflex as rx
from typing import List, Dict
from ..state import AuthState
import uuid
from ..config import API_BASE_URL

class AdminDashboardState(rx.State):
    # Product list
    UPLOAD_DIR = "uploading_models"

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
    product_type: str = ""
    stock: str = ""
    
    # File uploads - storing file paths/names
    product_image: str = ""
    texture_file: str = ""
    model_file: str = ""
    scene_file: str = ""
    
    # Upload files (for handling the actual upload)
    uploaded_files: list[rx.UploadFile] = []
    
    # Upload status
    upload_status: str = ""
    is_uploading: bool = False
    
    # Availability options
    digital_available: bool = True
    physical_available: bool = True
    is_container: bool = False
    
    # Stats
    total_products: int = 0
    total_sold: int = 0
    total_revenue: float = 0.0

    async def handle_product_image_upload(self, files: List[rx.UploadFile]):
        """Handle product image upload"""
        if not files:
            return
        
        file = files[0]
        upload_data = await file.read()
        filename = f"product_img_{uuid.uuid4().hex[:8]}_{file.name}"
        
        # Save file locally (adjust path as needed)
        outfile = rx.get_upload_dir() / filename
        with outfile.open("wb") as f:
            f.write(upload_data)
        
        self.product_image = filename
        self.upload_status = f"Product image uploaded: {file.name}"

    async def handle_texture_upload(self, files: List[rx.UploadFile]):
        """Handle texture file upload"""
        if not files:
            return
        
        file = files[0]
        upload_data = await file.read()
        filename = f"texture_{uuid.uuid4().hex[:8]}_{file.name}"
        
        outfile = rx.get_upload_dir() / filename
        with outfile.open("wb") as f:
            f.write(upload_data)
        
        self.texture_file = filename
        self.upload_status = f"Texture uploaded: {file.name}"

    async def handle_model_upload(self, files: List[rx.UploadFile]):
        """Handle 3D model file upload"""
        if not files:
            return
        
        file = files[0]
        upload_data = await file.read()
        filename = f"model_{uuid.uuid4().hex[:8]}_{file.name}"
        
        outfile = rx.get_upload_dir() / filename
        with outfile.open("wb") as f:
            f.write(upload_data)
        
        self.model_file = filename
        self.upload_status = f"3D model uploaded: {file.name}"

    async def handle_scene_upload(self, files: List[rx.UploadFile]):
        """Handle scene model file upload"""
        if not files:
            return
        
        file = files[0]
        upload_data = await file.read()
        filename = f"scene_{uuid.uuid4().hex[:8]}_{file.name}"
        
        outfile = rx.get_upload_dir() / filename
        with outfile.open("wb") as f:
            f.write(upload_data)
        
        self.scene_file = filename
        self.upload_status = f"Scene model uploaded: {file.name}"

    def toggle_digital_available(self, value: bool):
        self.digital_available = value

    def toggle_physical_available(self, value: bool):
        self.physical_available = value

    def toggle_is_container(self, value: bool):
        self.is_container = value

    products: list[dict] = []
    filtered_products: list[dict] = []
    total_products: int = 0

    
    
    async def load_products(self):
        import httpx
        API_BASE_URL = "http://localhost:8001"
        try:
            timeout = httpx.Timeout(connect=30.0, read=120.0, write=120.0, pool=60.0)
            auth_state = await self.get_state(AuthState)

        
            filter_body = {}

            async with httpx.AsyncClient(timeout=timeout) as client:
                cookies_dict = auth_state.session_cookies or {}

                response = await client.post(
                    f"{API_BASE_URL}/products/list/",  
                    json=filter_body,               
                    cookies=cookies_dict,
                )

            if response.status_code != 200:
                print(f"❌ Backend error: {response.status_code} {response.text}")
                return

            data = response.json()

            if "products" not in data:
                print("⚠️ No products returned:", data)
                return

            normalized = []
            for p in data["products"]:
                normalized.append({
                    "id": p.get("id"),
                    "title": p.get("name", "Untitled Product"),
                    "description":p.get("description", "None"),
                    "category": p.get("category", "Uncategorized"),
                    "digital_price": p.get("digital_price", "0"),
                    "physical_price": p.get("physical_price", "0"),
                    
                    # ✅ product image from base64
                    "image": (
                        f"data:image/png;base64,{p['image']}"
                        if p.get("image")
                        else "/placeholder.png"
                    ),
                })

            # ✅ update state
            self.products = normalized
            self.filtered_products = normalized
            self.total_products = len(normalized)
            self.apply_filters()

            print(f"✅ Loaded {self.total_products} products from backend")

        except Exception as e:
            print(f"❌ Error loading products: {e}")


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
        self.editing_product_id = str(product["id"])
        self.product_name = product["title"]
        self.description = product.get("description", "")
        self.physical_price = str(product["physical_price"])
        self.digital_price = str(product["digital_price"])
        self.category = product["category"]
        self.product_type = product.get("type", "")
        self.stock = str(product.get("stock", "0"))
        
        # ✅ File fields (for edit)
        self.product_image = product.get("product_image" or "")
        self.texture_file = product.get("texture_file" or "")
        self.model_file = product.get("model_file" or "" )
        self.scene_file = product.get("scene_file" or "")

        # ✅ Toggle fields
        self.digital_available = product.get("digital_available", False)
        self.physical_available = product.get("physical_available", False)
        self.is_container = product.get("is_container", False)

    
    def close_edit_modal(self):
        self.show_edit_modal = False
        self.clear_form()
    
    def clear_form(self):
        self.product_name = ""
        self.description = ""
        self.physical_price = ""
        self.digital_price = ""
        self.category = ""
        self.product_type = ""
        self.stock = ""
        self.editing_product_id = ""
        self.product_image = ""
        self.texture_file = ""
        self.model_file = ""
        self.scene_file = ""
        self.digital_available = True
        self.physical_available = True
        self.is_container = False
        self.upload_status = ""
    
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

    def set_product_type(self, value: str):
        self.product_type = value

    def set_stock(self, value: str):
        self.stock = value

    async def save_product(self):
        """Save new product - call backend API"""
        import httpx
        import traceback
        API_BASE_URL = "http://localhost:8001"
        
        self.is_uploading = True
        self.upload_status = ""
        
        try:
            # Validate required fields
            if not self.product_name or not self.physical_price or not self.digital_price:
                self.upload_status = "Please fill in all required fields"
                self.is_uploading = False
                return
            
            # Prepare form data - convert all values to strings for multipart/form-data
            data = {
                "name": str(self.product_name),
                "description": str(self.description),
                "digital_price": str(self.digital_price),
                "physical_price": str(self.physical_price),
                "category": str(self.category),
                "product_type": str(self.product_type),
                "stock": str(self.stock) if self.stock else "0",
                "digital_available": "true" if self.digital_available else "false",
                "physical_available": "true" if self.physical_available else "false",
                "is_container": "true" if self.is_container else "false",
            }
            
            # Prepare files for upload
            files = {}
            upload_dir = rx.get_upload_dir()
            
            try:
                if self.product_image:
                    file_path = upload_dir / self.product_image
                    if file_path.exists():
                        files['image'] = open(file_path, 'rb')
                    else:
                        print(f"Product image not found: {file_path}")
                
                if self.texture_file:
                    file_path = upload_dir / self.texture_file
                    if file_path.exists():
                        files['texture_files'] = open(file_path, 'rb')
                    else:
                        print(f"Texture file not found: {file_path}")
                
                if self.model_file:
                    file_path = upload_dir / self.model_file
                    if file_path.exists():
                        files['model_file'] = open(file_path, 'rb')
                    else:
                        print(f"Model file not found: {file_path}")
                
                if self.scene_file:
                    file_path = upload_dir / self.scene_file
                    if file_path.exists():
                        files['scene_files'] = open(file_path, 'rb')
                    else:
                        print(f"Scene file not found: {file_path}")
                
                # Make API call using httpx
                
                
                print(f"Sending request to: {API_BASE_URL}/products/add/")
                print(f"Data: {data}")
                print(f"Files: {list(files.keys())}")
                
                timeout = httpx.Timeout(connect=30.0, read=120.0, write=120.0, pool=60.0) 


                auth_state = await self.get_state(AuthState)
                async with httpx.AsyncClient(timeout=timeout) as client:

                    cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}
                    response = await client.post(
                        f"{API_BASE_URL}/products/add/",
                        data=data,
                        files=files,
                        cookies=cookies_dict,
                    )
                
                print(f"Response status: {response.status_code}")
                print(f"Response body: {response.text}")
                
                if response.status_code == 201:
                    self.upload_status = "Product saved successfully!"
                    print("product_data" , data)
                    self.close_add_modal()
                    await self.load_products()
                elif response.status_code == 400:
                    try:
                        error_data = response.json()
                        self.upload_status = f"Validation error: {error_data.get('error', 'Invalid data')}"
                    except:
                        self.upload_status = f"Validation error: {response.text}"
                elif response.status_code == 409:
                    self.upload_status = "Product with this name already exists"
                else:
                    try:
                        error_msg = response.json().get("error", "Something went wrong")
                    except:
                        error_msg = response.text
                    self.upload_status = f"Error: {error_msg}"
                    
            finally:
                # Close file handles
                for file in files.values():
                    try:
                        file.close()
                    except:
                        pass
                
        except httpx.TimeoutException:
            self.upload_status = "Request timeout - please try again"
            print("Timeout exception occurred")
        except Exception as e:
            self.upload_status = f"Connection error: {str(e)}"
            print(f"Exception during product creation: {str(e)}")
            print(f"Full traceback: {traceback.format_exc()}")
        except httpx.ReadError:
            self.upload_status = "Connection closed unexpectedly. Try again or check backend logs."
            print("httpx.ReadError occurred during product upload.")
        
        finally:
            self.is_uploading = False
    
    
    async def delete_product(self, product_id: int):
        import httpx
        """Delete a product by ID"""
        API_BASE_URL = "http://localhost:8001"
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{API_BASE_URL}/products/delete/{product_id}/",
                    headers={"Content-Type": "application/json"},
                    cookies=cookies_dict,
                )
            
            if response.status_code == 200:
                # Remove product from the list
                self.products = [p for p in self.products if p["id"] != product_id]
                print(f"✅ Product {product_id} deleted successfully")
                await self.load_products()
                return rx.toast.success(f"Product deleted successfully!")
            else:
                print(f"❌ Failed to delete product: {response.status_code} {response.text}")
                return rx.toast.error(f"Failed to delete product")
                
        except Exception as e:
            print(f"❌ Error deleting product: {e}")
            return rx.toast.error(f"Error: {str(e)}")
        
        
    async def update_product(self, product_data):
        import httpx
        """Update an existing product"""
        print(product_data)

        API_BASE_URL = "http://localhost:8001"
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}

        try:
            
            data = {
                "product_id": product_data["id"],
                "name": product_data["name"],
                "description": product_data["description"],
                "digital_price": str(product_data["digital_price"]),
                "physical_price": str(product_data["physical_price"]),
                "category": product_data["category"],
                "product_type": product_data["product_type"],
                "stock": str(product_data["stock"]),
                "digital_available": str(product_data["digital_available"]).lower(),
                "physical_available": str(product_data["physical_available"]).lower(),
                "is_container": str(product_data["is_container"]).lower(),
            }

         
            files = {}

            if "image" in product_data and product_data["image"]:
                files["image"] = (
                    getattr(product_data["image"], "name", "image.png"),
                    product_data["image"],
                    "image/png",
                )

            if "model_file" in product_data and product_data["model_file"]:
                files["model_file"] = (
                    getattr(product_data["model_file"], "name", "model.glb"),
                    product_data["model_file"],
                    "application/octet-stream",
                )

            # Multiple scene files
            for i, f in enumerate(product_data.get("scene_files", [])):
                files[f"scene_files[{i}]"] = (
                    getattr(f, "name", f"scene_{i}.glb"),
                    f,
                    "application/octet-stream",
                )


            # Multiple texture files
            for i, f in enumerate(product_data.get("texture_files", [])):
                files[f"texture_files[{i}]"] = (
                    getattr(f, "name", f"texture_{i}.png"),
                    f,
                    "image/png",
                )

            # Send POST request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/products/update/",
                    data=data,
                    files=files,
                    cookies=cookies_dict,
                )

            if response.status_code == 200:
                print("✅ Product updated successfully")
                await self.load_products()
                return rx.toast.success("Product updated successfully!")
            else:
                print(f"❌ Failed to update product: {response.status_code} {response.text}")
                return rx.toast.error("Failed to update product")

        except Exception as e:
            print(f"❌ Error updating product: {e}")
            return rx.toast.error(f"Error: {str(e)}")



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



def file_upload_section(
    title: str,
    description: str,
    accepted_types: str,
    upload_handler,
    current_file: str,
    icon: str = "upload"
) -> rx.Component:
    """Reusable file upload component"""
    return rx.vstack(
        rx.hstack(
            rx.icon(icon, size=20, color="#6366F1"),
            rx.text(title, size="2", weight="bold"),
            spacing="2",
            align="center",
        ),
        rx.text(description, size="1", color="#64748B"),
        
        rx.upload(
            rx.vstack(
                rx.button(
                    rx.icon("upload", size=16),
                    "Select File",
                    variant="soft",
                    size="2",
                ),
                rx.text(
                    accepted_types,
                    size="1",
                    color="#64748B",
                ),
                spacing="2",
                align="center",
            ),
            id=f"upload_{title.lower().replace(' ', '_')}",
            border=f"1px dashed #CBD5E1",
            padding="16px",
            border_radius="8px",
            width="100%",
        ),
        
        rx.hstack(
            rx.button(
                "Upload",
                size="1",
                on_click=upload_handler(
                    rx.upload_files(
                        upload_id=f"upload_{title.lower().replace(' ', '_')}"
                    )
                ),
            ),
            rx.cond(
                current_file != "",
                rx.hstack(
                    rx.text(current_file, size="1", color="#10B981"),
                    spacing="1",
                ),
                rx.text("No file uploaded", size="1", color="#64748B"),
            ),
            spacing="2",
            align="center",
        ),
        
        spacing="2",
        width="100%",
        padding="12px",
        background_color="#F8FAFC",
        border_radius="8px",
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
            
            rx.scroll_area(
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
                    
                    # Category and Product Type
                    rx.hstack(
                        rx.vstack(
                            rx.text("Category *", size="2", weight="medium"),
                            rx.input(
                                placeholder="Living Room, Bedroom, etc.",
                                value=AdminDashboardState.category,
                                on_change=AdminDashboardState.set_category,
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.text("Product Type *", size="2", weight="medium"),
                            rx.input(
                                placeholder="Sofa, Chair, Table, etc.",
                                value=AdminDashboardState.product_type,
                                on_change=AdminDashboardState.set_product_type,
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    
                    # Stock
                    rx.vstack(
                        rx.text("Stock Quantity *", size="2", weight="medium"),
                        rx.input(
                            placeholder="20",
                            type="number",
                            value=AdminDashboardState.stock,
                            on_change=AdminDashboardState.set_stock,
                        ),
                        spacing="1",
                        width="100%",
                    ),
                    
                    rx.divider(),
                    
                    rx.heading("File Uploads", size="4", weight="bold", margin_bottom="8px"),
                    
        
                    file_upload_section(
                        "Product Image",
                        "Upload product display image",
                        "Accepted: PNG files only",
                        AdminDashboardState.handle_product_image_upload,
                        AdminDashboardState.product_image,
                        "image"
                    ),
                
                    file_upload_section(
                        "Texture File",
                        "Upload texture file for 3D model",
                        "Accepted: PNG files only",
                        AdminDashboardState.handle_texture_upload,
                        AdminDashboardState.texture_file,
                        "palette"
                    ),
                    
                    file_upload_section(
                        "3D Model",
                        "Upload 3D product model",
                        "Accepted: GLB files only",
                        AdminDashboardState.handle_model_upload,
                        AdminDashboardState.model_file,
                        "box"
                    ),
                    
                    file_upload_section(
                        "Scene Model",
                        "Upload 3D room scene model",
                        "Accepted: GLB files only",
                        AdminDashboardState.handle_scene_upload,
                        AdminDashboardState.scene_file,
                        "home"
                    ),
                    
               
                    rx.cond(
                        AdminDashboardState.upload_status != "",
                        rx.callout(
                            AdminDashboardState.upload_status,
                            icon="info",
                            size="1",
                        ),
                    ),
                    
           
                    rx.divider(),
                    
                 
                    rx.heading("Availability Options", size="4", weight="bold", margin_bottom="8px"),
                    
                    rx.hstack(
                        rx.hstack(
                            rx.switch(
                                checked=AdminDashboardState.digital_available,
                                on_change=AdminDashboardState.toggle_digital_available,
                            ),
                            rx.text("Digital Available", size="2", weight="medium"),
                            spacing="2",
                            align="center",
                        ),
                        rx.hstack(
                            rx.switch(
                                checked=AdminDashboardState.physical_available,
                                on_change=AdminDashboardState.toggle_physical_available,
                            ),
                            rx.text("Physical Available", size="2", weight="medium"),
                            spacing="2",
                            align="center",
                        ),
                        rx.hstack(
                            rx.switch(
                                checked=AdminDashboardState.is_container,
                                on_change=AdminDashboardState.toggle_is_container,
                            ),
                            rx.text("Is Container", size="2", weight="medium"),
                            spacing="2",
                            align="center",
                        ),
                        spacing="4",
                        width="100%",
                        wrap="wrap",
                    ),
                    
                    spacing="4",
                    width="100%",
                ),
                height="600px",
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
                rx.button(
                    rx.cond(
                        AdminDashboardState.is_uploading,
                        rx.hstack(
                            rx.spinner(size="1"),
                            rx.text("Saving..."),
                            spacing="2",
                        ),
                        rx.text("Save Product"),
                    ),
                    on_click=save_fn,
                    disabled=AdminDashboardState.is_uploading,
                ),
                spacing="3",
                margin_top="16px",
                justify="end",
            ),
            
            max_width="800px",
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
                rx.heading("Product Management", size="8", weight="bold",color="#22282c"),
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
           
                rx.hstack(
                    rx.input(
                        rx.input.slot(rx.icon("search"),color="#807E80"),
                        placeholder="Search products...",
                        value=AdminDashboardState.search_query,
                        on_change=AdminDashboardState.set_search_query,
                        width="300px",
                        background_color="#E0E6EA",
                        border_radius="20px",
                        color="#22282C",
                        type = "search"
                    ),
                 
                    spacing="3",
                    width="100%",   
                   
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


def product_card(product: Dict) -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.image(
                src=product.get("image", "/placeholder.png"),
                width="100%",
                height="200px",
                object_fit="cover",
                border_radius="8px",
            ),
            
            rx.vstack(
                rx.hstack(
                    rx.heading(product.get("title", "No Title"), size="2", weight="bold",color="#22282c"),
                    rx.spacer(),
                    rx.badge(product.get("category", "N/A"), variant="soft"),
                    width="100%",
                ),
               
                rx.hstack(
                    rx.vstack(
                    rx.vstack(
                        rx.text("Physical", size="1",color="#22282c"),
                        rx.text(f"${product.get('physical_price','0')}", size="3", weight="bold",color="#22282c"),
                        spacing="0",
                    ),
                    rx.vstack(
                        rx.text("Digital", size="1",color="#22282c"),
                        rx.text(f"${product.get('digital_price','0')}", size="3", weight="bold",color="#22282c"),
                        spacing="0",
                    ),
                    ),
                    rx.spacer(),
                    rx.vstack(
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
                    width = "100%",
                    text_align = "center"  
                ),
               
            ),
            spacing="3",
            width="100%",
        ),
        width="100%",
    )

