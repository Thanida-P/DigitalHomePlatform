import reflex as rx
from typing import List, Any
from ..template import template
from ..state import AuthState
from ..config import API_BASE_URL
from datetime import datetime, timedelta
import uuid


def format_datetime(dt_str: str) -> str:
    """Format ISO datetime to human readable format"""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        local_time = dt + timedelta(hours=7)
        return local_time.strftime("%b %d, %Y %H:%M")
    except Exception as e:
        print(f"Error formatting datetime: {e}")
        return dt_str

class Order(rx.Base):
    order_id: int
    order_items: List[dict]
    total_price: str
    status: str
    created_at: str
    updated_at: str
    payment_method: dict | None


class OrdersState(rx.State):
    orders: List[Order] = []
    is_loading: bool = False
    is_processing: bool = False
    selected_filter: str = "all"
    
    # Review Modal State
    show_review_modal: bool = False
    selected_product_id: int = 0
    selected_product_name: str = ""
    review_rating: int = 5
    review_comment: str = ""
    review_image: str = ""
    upload_status: str = ""
    
    def set_filter(self, filter_type: str):
        """Set the order filter"""
        self.selected_filter = filter_type
    
    @rx.var
    def filtered_orders(self) -> List[Order]:
        """Return filtered orders based on selected filter"""
        if self.selected_filter == "all":
            return self.orders
        elif self.selected_filter == "active":
            return [order for order in self.orders if order.status in ["pending", "payment completed"]]
        elif self.selected_filter == "completed":
            return [order for order in self.orders if order.status == "complete"]
        elif self.selected_filter == "cancelled":
            return [order for order in self.orders if order.status == "cancelled"]
        return self.orders
    
    def open_review_modal(self, product_id: int, product_name: str):
        """Open review modal for a specific product"""
        self.selected_product_id = product_id
        self.selected_product_name = product_name
        self.review_rating = 5
        self.review_comment = ""
        self.review_image = ""
        self.show_review_modal = True
    
    def close_review_modal(self):
        """Close review modal"""
        self.show_review_modal = False
        self.selected_product_id = 0
        self.selected_product_name = ""
        self.review_rating = 5
        self.review_comment = ""
        self.review_image = ""
    
    def set_review_rating(self, rating: int):
        """Set review rating"""
        self.review_rating = rating
    
    def set_review_comment(self, comment: str):
        """Set review comment"""
        self.review_comment = comment
    
    async def handle_review_image_upload(self, files: List[rx.UploadFile]):
        """Handle product image upload"""
        if not files:
            return
        
        file = files[0]
        upload_data = await file.read()
        filename = f"review_img_{uuid.uuid4().hex[:8]}_{file.name}"
        
      
        outfile = rx.get_upload_dir() / filename
        with outfile.open("wb") as f:
            f.write(upload_data)
        
        self.review_image = filename
        self.upload_status = f"Product image uploaded: {file.name}"
    
    async def submit_review(self):
     
        import httpx
        self.is_processing = True
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        
        try:
            async with httpx.AsyncClient() as client:
                data = {
                    'product_id': str(self.selected_product_id),
                    'rating': str(self.review_rating),
                    'comment': self.review_comment or '',
                }
                
                files = {}
                upload_dir = rx.get_upload_dir()

                if self.review_image:
                    file_path = upload_dir / self.review_image
                    if file_path.exists():
                        files['image'] = open(file_path, 'rb')
                    else:
                        print(f"Product image not found: {file_path}")
                
                response = await client.post(
                    f"{API_BASE_URL}/reviews/add/",
                    data=data,
                    files=files,
                    cookies=cookies_dict,
                )
                
                if response.status_code == 201:
                    rx.toast.success("Review submitted successfully!")
                    print("Review success")
                    self.close_review_modal()
                else:
                    error_data = response.json()
                    error = error_data.get('error', 'Failed to submit review')
                    rx.toast.error(f"Error: {error}")
                    
        except Exception as e:
            rx.toast.error(f"Error: {e}")
        finally:
            self.is_processing = False
            for file in files.values():
                    try:
                        file.close()
                    except:
                        pass
    
    async def load_orders(self):
        import httpx
        self.is_loading = True
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/orders/list/",
                    cookies=cookies_dict,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    orders_data = data.get('orders', [])
                    self.orders = [
                        Order(
                            order_id=order['order_id'],
                            order_items=order['order_items'],
                            total_price=order['total_price'],
                            status=order['status'],
                            created_at=order['created_at'],
                            updated_at=order['updated_at'],
                            payment_method=order.get('payment_method')
                        )
                        for order in orders_data
                    ]
                else:
                    rx.toast.error("Failed to load orders")
                    
        except Exception as e:
            rx.toast.error(f"Error: {e}")
        finally:
            self.is_loading = False
    
    async def mark_payment_completed(self, order_id: int):
        """Mark order payment as completed"""
        import httpx
        self.is_processing = True
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/orders/payment_completed/{order_id}/",
                    cookies=cookies_dict,
                )
                
                if response.status_code == 200:
                    rx.toast.success("Payment marked as completed!")
                    await self.load_orders()
                else:
                    error = response.json().get('error', 'Failed to update payment status')
                    rx.toast.error(f"Error: {error}")
                    
        except Exception as e:
            rx.toast.error(f"Error: {e}")
        finally:
            self.is_processing = False
    
    async def complete_order(self, order_id: int):
        """Complete the order and grant digital items"""
        import httpx
        self.is_processing = True
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/orders/complete/{order_id}/",
                    cookies=cookies_dict,
                )
                
                if response.status_code == 200:
                    rx.toast.success("Order completed! Digital items have been granted.")
                    await self.load_orders()
                else:
                    error = response.json().get('error', 'Failed to complete order')
                    rx.toast.error(f"Error: {error}")
                    
        except Exception as e:
            rx.toast.error(f"Error: {e}")
        finally:
            self.is_processing = False
    
    async def cancel_order(self, order_id: int):
        import httpx
        self.is_processing = True
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/orders/cancel/{order_id}/",
                    cookies=cookies_dict,
                )
                
                if response.status_code == 200:
                    rx.toast.success("Order cancelled successfully")
                    await self.load_orders()
                else:
                    error = response.json().get('error', 'Failed to cancel order')
                    rx.toast.error(f"Error: {error}")
                    
        except Exception as e:
            rx.toast.error(f"Error: {e}")
        finally:
            self.is_processing = False


def get_status_color(status: str) -> str:
    """Return color scheme based on order status"""
    status_colors = {
        "pending": "orange",
        "payment completed": "blue",
        "complete": "green",
        "cancelled": "red"
    }
    return status_colors.get(status, "gray")


def star_rating_item(star_num: int) -> rx.Component:
    """Individual star for rating"""
    return rx.icon(
        "star",
        size=32,
        color=rx.cond(
            star_num <= OrdersState.review_rating,
            "#FFA500",
            "#E2E8F0"
        ),
        fill=rx.cond(
            star_num <= OrdersState.review_rating,
            "#FFA500",
            "transparent"
        ),
        cursor="pointer",
        on_click=OrdersState.set_review_rating(star_num)
    )


def review_modal() -> rx.Component:
    """Modal for writing product reviews"""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title(
                    f"Write a Review",
                    font_size="24px",
                    font_weight="700",
                    color="#22282c",
                    margin_bottom="8px"
                ),
                rx.text(
                    OrdersState.selected_product_name,
                    font_size="16px",
                    color="#929FA7",
                    margin_bottom="20px"
                ),
                
                # Rating Section
                rx.vstack(
                    rx.text(
                        "Rating",
                        font_size="14px",
                        font_weight="600",
                        color="#22282c",
                        margin_bottom="8px"
                    ),
                    rx.hstack(
                        star_rating_item(1),
                        star_rating_item(2),
                        star_rating_item(3),
                        star_rating_item(4),
                        star_rating_item(5),
                        spacing="2"
                    ),
                    align_items="start",
                    width="100%",
                    margin_bottom="20px"
                ),
                
                # Comment Section
                rx.vstack(
                    rx.text(
                        "Your Review",
                        font_size="14px",
                        font_weight="600",
                        color="#22282c",
                        margin_bottom="8px"
                    ),
                    rx.text_area(
                        placeholder="Share your experience with this product...",
                        value=OrdersState.review_comment,
                        on_change=OrdersState.set_review_comment,
                        width="100%",
                        min_height="120px",
                        resize="vertical"
                    ),
                    align_items="start",
                    width="100%",
                    margin_bottom="20px"
                ),
                
                # Image Upload Section
                file_upload_section(
                        "Product Image",
                        "Upload product display image",
                        "Accepted: PNG files only",
                        OrdersState.handle_review_image_upload,
                        OrdersState.review_image,
                        "image"
                    ),
                
                # Action Buttons
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Cancel",
                            variant="soft",
                            color_scheme="gray",
                            cursor="pointer",
                            on_click=OrdersState.close_review_modal
                        )
                    ),
                    rx.button(
                        "Submit Review",
                        bg="#2E6FF2",
                        color="white",
                        cursor="pointer",
                        loading=OrdersState.is_processing,
                        on_click=OrdersState.submit_review,
                        _hover={"bg": "#1E5FE2"}
                    ),
                    spacing="3",
                    justify="end",
                    width="100%"
                ),
                
                spacing="4",
                width="100%"
            ),
            max_width="500px",
            padding="30px"
        ),
        open=OrdersState.show_review_modal
    )


def review_button(product_id: int, product_name: str) -> rx.Component:
    """Reusable review button component"""
    return rx.button(
        rx.icon("star", size=14),
        "Write Review",
        size="1",
        variant="soft",
        color_scheme="orange",
        cursor="pointer",
        on_click=OrdersState.open_review_modal(product_id, product_name)
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

def order_card(order: Order) -> rx.Component:
    """Individual order card with action buttons"""
    return rx.box(
        rx.vstack(
            # Header
            rx.hstack(
                rx.vstack(
                    rx.text(
                        f"Order #{order.order_id}",
                        font_size="20px",
                        font_weight="700",
                        color="#22282c"
                    ),
                    rx.text(
                        format_datetime(order.created_at),
                        font_size="14px",
                        color="#929FA7"
                    ),
                    spacing="1",
                    align_items="start"
                ),
                rx.spacer(),
                rx.vstack(
                    rx.badge(
                        order.status.upper(),
                        color_scheme=get_status_color(order.status),
                        variant="soft",
                        font_size="12px",
                        padding="8px 16px"
                    ),
                    rx.text(
                        f"${order.total_price}",
                        font_size="24px",
                        font_weight="700",
                        color="#22282c"
                    ),
                    spacing="2",
                    align_items="end"
                ),
                width="100%",
                align_items="start"
            ),
            
            rx.divider(margin_y="16px"),
            
            # Order Items with Review Buttons
            rx.vstack(
                rx.text(
                    "Order Items:",
                    font_size="16px",
                    font_weight="600",
                    color="#22282c",
                    margin_bottom="8px"
                ),
                rx.foreach(
                    order.order_items,
                    lambda item: rx.hstack(
                        rx.hstack(
                            rx.text(
                                f"• {item['product_name']}",
                                font_size="14px",
                                color="#22282c"
                            ),
                            rx.badge(item['type'], variant="soft", color_scheme="purple"),
                            rx.text(
                                f"x{item['quantity']}",
                                font_size="14px",
                                font_weight="600",
                                color="#22282c"
                            ),
                            spacing="2"
                        ),
                        rx.spacer(),
                        # Show Write Review button only for completed orders
                        rx.cond(
                            order.status == "complete",
                            review_button(item['product_id'], item['product_name']),
                            rx.fragment()
                        ),
                        width="100%",
                        padding="8px 0",
                        align_items="center"
                    )
                ),
                spacing="2",
                align_items="start",
                width="100%"
            ),
            
            rx.cond(
                order.payment_method is not None,
                rx.vstack(
                    rx.divider(margin_y="16px"),
                    rx.hstack(
                        rx.icon("credit-card", size=18, color="#929FA7"),
                        rx.text(
                            "Payment Method:",
                            font_size="14px",
                            color="#929FA7"
                        ),
                        rx.text(
                            rx.cond(
                                order.payment_method.get('type') == 'credit_card',
                                f"Credit Card •••• {order.payment_method.get('credit_card_last4', '')}",
                                f"Bank Account •••• {order.payment_method.get('bank_account_last4', '')}"
                            ),
                            font_size="14px",
                            font_weight="600",
                            color="#22282c"
                        ),
                        spacing="2",
                        align_items="center"
                    ),
                    spacing="2",
                    align_items="start",
                    width="100%"
                ),
                rx.fragment()
            ),
            
            rx.divider(margin_y="16px"),
            
            # Action Buttons based on status
            rx.hstack(
                rx.cond(
                    order.status == "pending",
                    rx.hstack(
                        rx.button(
                            "Mark Payment Completed",
                            on_click=OrdersState.mark_payment_completed(order.order_id),
                            bg="#2E6FF2",
                            color="white",
                            border_radius="8px",
                            padding="10px 20px",
                            cursor="pointer",
                            loading=OrdersState.is_processing,
                            _hover={"bg": "#1E5FE2"}
                        ),
                        rx.button(
                            "Cancel Order",
                            on_click=OrdersState.cancel_order(order.order_id),
                            variant="outline",
                            color_scheme="red",
                            border_radius="8px",
                            padding="10px 20px",
                            cursor="pointer",
                            loading=OrdersState.is_processing,
                        ),
                        spacing="3"
                    ),
                    rx.fragment()
                ),
                
                rx.cond(
                    order.status == "payment completed",
                    rx.button(
                        "Complete Order",
                        on_click=OrdersState.complete_order(order.order_id),
                        bg="#10B981",
                        color="white",
                        border_radius="8px",
                        padding="10px 20px",
                        cursor="pointer",
                        loading=OrdersState.is_processing,
                        _hover={"bg": "#059669"}
                    ),
                    rx.fragment()
                ),
                
                rx.cond(
                    order.status == "complete",
                    rx.text(
                        "✓ Order Completed",
                        font_size="14px",
                        font_weight="600",
                        color="#10B981"
                    ),
                    rx.fragment()
                ),
                
                rx.cond(
                    order.status == "cancelled",
                    rx.text(
                        "✗ Order Cancelled",
                        font_size="14px",
                        font_weight="600",
                        color="#EF4444"
                    ),
                    rx.fragment()
                ),
                
                width="100%",
                justify="end"
            ),
            
            spacing="4",
            width="100%"
        ),
        padding="24px",
        border="1px solid #e2e8f0",
        border_radius="12px",
        bg="white",
        width="100%",
        box_shadow="0 1px 3px rgba(0, 0, 0, 0.1)",
        _hover={"box_shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"}
    )


def orders_content() -> rx.Component:
    """Main orders page content with filter tabs"""
    return rx.box(
        review_modal(),
        rx.vstack(
            rx.heading(
                "MY ORDERS",
                font_size="32px",
                font_weight="700",
                color="#22282c",
                margin_bottom="20px"
            ),
            
            # Filter Tabs (Prettier Version)
            rx.hstack(
                rx.button(
                    "All Orders",
                    on_click=OrdersState.set_filter("all"),
                    variant=rx.cond(OrdersState.selected_filter == "all", "solid", "outline"),
                    color_scheme=rx.cond(OrdersState.selected_filter == "all", "teal", "gray"),
                    cursor="pointer",
                    border_radius="20px",
                    padding="10px 22px",
                    color=rx.cond(OrdersState.selected_filter == "all", "white", "#22282c"),
                    _hover={"bg": rx.cond(OrdersState.selected_filter == "all", "#059669", "#e2e8f0")},
                ),
                rx.button(
                    "Active",
                    on_click=OrdersState.set_filter("active"),
                    variant=rx.cond(OrdersState.selected_filter == "active", "solid", "outline"),
                    color_scheme=rx.cond(OrdersState.selected_filter == "active", "cyan", "gray"),
                    cursor="pointer",
                    border_radius="20px",
                    padding="10px 22px",
                    color=rx.cond(OrdersState.selected_filter == "active", "white", "#22282c"),
                    _hover={"bg": rx.cond(OrdersState.selected_filter == "active", "#06b6d4", "#e2e8f0")},
                ),
                rx.button(
                    "Completed",
                    on_click=OrdersState.set_filter("completed"),
                    variant=rx.cond(OrdersState.selected_filter == "completed", "solid", "outline"),
                    color_scheme=rx.cond(OrdersState.selected_filter == "completed", "green", "gray"),
                    cursor="pointer",
                    border_radius="20px",
                    padding="10px 22px",
                    color=rx.cond(OrdersState.selected_filter == "completed", "white", "#22282c"),
                    _hover={"bg": rx.cond(OrdersState.selected_filter == "completed", "#10b981", "#e2e8f0")},
                ),
                rx.button(
                    "Cancelled",
                    on_click=OrdersState.set_filter("cancelled"),
                    variant=rx.cond(OrdersState.selected_filter == "cancelled", "solid", "outline"),
                    color_scheme=rx.cond(OrdersState.selected_filter == "cancelled", "red", "gray"),
                    cursor="pointer",
                    border_radius="20px",
                    padding="10px 22px",
                    color=rx.cond(OrdersState.selected_filter == "cancelled", "white", "#22282c"),
                    _hover={"bg": rx.cond(OrdersState.selected_filter == "cancelled", "#ef4444", "#e2e8f0")},
                ),
                spacing="4",
                margin_bottom="30px",
                flex_wrap="wrap"
            ),

            
            rx.cond(
                OrdersState.is_loading,
                rx.center(
                    rx.spinner(size="3"),
                    padding="40px"
                ),
                rx.cond(
                    OrdersState.filtered_orders.length() > 0,
                    rx.vstack(
                        rx.foreach(
                            OrdersState.filtered_orders,
                            order_card
                        ),
                        spacing="4",
                        width="100%",
                        max_width="1000px"
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("shopping-bag", size=48, color="#929FA7"),
                            rx.text(
                                rx.cond(
                                    OrdersState.selected_filter == "all",
                                    "No orders yet",
                                    f"No {OrdersState.selected_filter} orders"
                                ),
                                font_size="20px",
                                font_weight="600",
                                color="#22282c"
                            ),
                            rx.text(
                                "Start shopping to see your orders here",
                                font_size="14px",
                                color="#929FA7"
                            ),
                            rx.link(
                                rx.button(
                                    "Browse Products",
                                    bg="#22282c",
                                    color="white",
                                    padding="12px 24px",
                                    border_radius="8px",
                                    margin_top="20px",
                                    cursor="pointer",
                                    _hover={"bg": "#1a1f23"}
                                ),
                                href="/products"
                            ),
                            spacing="4",
                            align_items="center"
                        ),
                        padding="60px"
                    )
                )
            ),
            
            spacing="6",
            width="100%",
            padding="40px",
            align_items="center",
            min_height="100vh"
        )
    )


@rx.page(route="/orders", on_load=OrdersState.load_orders)
def orders_page() -> rx.Component:
    return template(orders_content)