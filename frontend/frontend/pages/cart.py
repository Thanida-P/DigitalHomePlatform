import reflex as rx
from typing import List, Optional
from ..template import template
from ..state import AuthState
from ..config import API_BASE_URL
from ..components.navbar import NavCartState

class CreditCard(rx.Base):
    id: int = 0
    card_brand: str = ""
    last4: str = ""
    exp_month: int = 0
    exp_year: int = 0
    is_default: bool = False
    provider: str = ""
    provider_token: str = ""


class BankAccount(rx.Base):
    id: int = 0
    bank_name: str = ""
    account_holder: str = ""
    last4: str = ""
    is_default: bool = False
    provider: str = ""

class CartItem(rx.Base):
   
    id: int
    product_id: int
    name: str
    price: int
    quantity: int
    colors: List[str]
    image: str
    item_type: str

class Address(rx.Base):
    id: int = 0
    name: str = ""
    phone: str = ""
    address: str = ""
    is_default: bool = False

class CartState(rx.State):

    cart_items: List[CartItem] = []
    cart_id: Optional[int] = None
    is_loading: bool = False
    promo_code: str = ""
    delivery_fee: int = 50
    discount: int = 50
    selected_payment: str = ""
    
    addresses: list[Address] = []
    selected_address: Address | None = None
    show_address_dialog: bool = False

    username: str = ""
    phone_number: str = ""

    credit_cards: list[CreditCard] = []
    bank_accounts: list[BankAccount] = []
    is_loading_payments: bool = False

    async def update_navbar_cart_quantity(self, quantity: int):
        """Update the navbar cart quantity"""
        nav_state = await self.get_state(NavCartState)
        nav_state.cart_quantity = quantity


    def select_payment(self, payment_id: str):
        """Select a payment method"""
        self.selected_payment = payment_id


    def close_address_dialog(self):
        self.show_address_dialog = False
    
    async def open_address_dialog(self):
        """Open dialog and load addresses."""
        self.show_address_dialog = True
        await self.load_addresses()

    
    def select_address(self, addr: Address):
        """Select an address and close dialog."""
        self.selected_address = addr
        self.show_address_dialog = False

    async def load_user_data(self):
        import httpx
    
        auth_state = await self.get_state(AuthState)
        
        if not auth_state.is_logged_in:
            return

        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/users/profile/",
                    cookies=cookies_dict,
                    timeout=5.0
                )
            if response.status_code == 200:
                data = response.json()
                user = data.get("user_profile", {})
          
                self.username = user.get("username", "")
                self.phone_number = user.get("phone_no", "")

        except Exception as e:
            print(f"Error loading user data: {str(e)}")
    
    async def load_addresses(self):
        import httpx
       
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"{API_BASE_URL}/users/address/",
                    cookies=cookies_dict,
                )
            if res.status_code == 200:
                addresses_data = res.json()
                addresses_list = addresses_data.get("addresses", [])
                self.addresses = [
                    Address(
                        id=addr.get("id", 0),
                        name=addr.get("name", ""),  
                        phone=addr.get("phone", ""),  
                        address=addr.get("address", ""),
                        is_default=addr.get("is_default", False)
                    )
                    for addr in addresses_list
                ]
                
                if not self.selected_address:
                    default_addr = next((a for a in self.addresses if a.is_default), None)
                    if default_addr:
                        self.selected_address = default_addr
                    elif self.addresses:
                        self.selected_address = self.addresses[0]
                        
            else:
                print("Failed to fetch addresses:", res.text)
        except Exception as e:
            print("Request failed:", e)

 

    async def load_cart(self):
        import httpx
        
        self.is_loading = True
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        
        try:
            async with httpx.AsyncClient() as client:
                # Get cart items
                response = await client.get(
                    f"{API_BASE_URL}/carts/view/",
                    cookies=cookies_dict,
                    timeout=10.0  # 
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"📦 Cart data: {data}")
                    
                    self.cart_id = data.get('cart_id')
                    print(f"🛒 Cart ID: {self.cart_id}")
                    
                    items = []
                    for item in data.get('items', []):
                        print(f"\n🔍 Processing item: {item}")
                        product_id = item.get('product_id')
                        
                        try:
                            
                            product_response = await client.get(
                                f"{API_BASE_URL}/products/get_product_detail/{product_id}/",
                                cookies=cookies_dict,
                                timeout=10.0
                            )
                            
                            
                            if product_response.status_code == 200:
                                response_data = product_response.json()
                                
                                
                                product_data = response_data.get('product', {})   
                              
                                item_type = item.get('type', 'physical')
                                
                                if item_type == 'digital':
                                    price_value = product_data.get('digital_price', 0)
                                else:
                                    price_value = product_data.get('physical_price', 0)
                                
                                try:
                                    price = int(float(price_value))
                                except (ValueError, TypeError):
                                    print(f"⚠️ Could not convert price '{price_value}' to int, using 0")
                                    price = 0
                                
                                
                                cart_item = CartItem(
                                    id=item.get('id'),
                                    product_id=product_id,
                                    name=product_data.get('name', item.get('product_name', 'Unknown Product')),
                                    price=price,
                                    quantity=item.get('quantity', 1),
                                    colors=["#C0C0C0", "#F5F5DC", "#D2B48C"],
                                    image=f"data:image/png;base64,{product_data.get('image')}",
                                    item_type=item_type
                                )
                                
                                items.append(cart_item)
                                
                                
                            else:
                               
                                print(f"❌ Failed to fetch product {product_id}")
                                print(f"   Status: {product_response.status_code}")
                                try:
                                    error_data = product_response.json()
                                    print(f"   Error data: {error_data}")
                                except:
                                    print(f"   Response text: {product_response.text}")
                                
                               
                                cart_item = CartItem(
                                    id=item.get('id'),
                                    product_id=product_id,
                                    name=item.get('product_name', 'Product Not Found'),
                                    price=0,
                                    quantity=item.get('quantity', 1),
                                    colors=["#C0C0C0", "#F5F5DC", "#D2B48C"],
                                    image="/placeholder.jpg",
                                    item_type=item.get('type', 'physical')
                                )
                                items.append(cart_item)
                                
                        except httpx.TimeoutException:
                            print(f"⏱️ Timeout fetching product {product_id}")
                            cart_item = CartItem(
                                id=item.get('id'),
                                product_id=product_id,
                                name=item.get('product_name', 'Product Unavailable'),
                                price=0,
                                quantity=item.get('quantity', 1),
                                colors=["#C0C0C0", "#F5F5DC", "#D2B48C"],
                                image="/placeholder.jpg",
                                item_type=item.get('type', 'physical')
                            )
                            items.append(cart_item)
                            
                        except Exception as e:
                            print(f"❌ Error fetching product {product_id}: {type(e).__name__}: {str(e)}")
                            import traceback
                            traceback.print_exc()
                            
                        
                            cart_item = CartItem(
                                id=item.get('id'),
                                product_id=product_id,
                                name=item.get('product_name', 'Error Loading Product'),
                                price=0,
                                quantity=item.get('quantity', 1),
                                colors=["#C0C0C0", "#F5F5DC", "#D2B48C"],
                                image="/placeholder.jpg",
                                item_type=item.get('type', 'physical')
                            )
                            items.append(cart_item)
                    
                    self.cart_items = items
                    print(f"✅ Total items loaded: {len(items)}")
                    await self.update_navbar_cart_quantity(len(items))
                    
                elif response.status_code == 404:
                    self.cart_items = []
                    print("ℹ️ Cart is empty (404)")
                    rx.toast.info("Your cart is empty")
                else:
                    error_text = response.text
                    print(f"❌ Failed to load cart: {response.status_code}")
                    print(f"   Response: {error_text}")
                    try:
                        error = response.json().get('error', 'Failed to load cart')
                    except:
                        error = 'Failed to load cart'
                    rx.toast.error(f"Error: {error}")
                    
        except httpx.TimeoutException:
            print("⏱️ Timeout loading cart")
            rx.toast.error("Request timeout. Please try again.")
        except Exception as e:
            print(f"❌ Exception in load_cart: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            rx.toast.error(f"Network error: {str(e)}")
        finally:
            self.is_loading = False

    async def remove_item(self, item_id: int):
        """Remove item from cart via API"""
        import httpx
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{API_BASE_URL}/carts/remove_item/{item_id}/",
                    cookies=cookies_dict,
                )
                
                if response.status_code == 200:
                    # Remove item from local state
                    self.cart_items = [item for item in self.cart_items if item.id != item_id]
                    rx.toast.success("Item removed from cart")
                    await self.update_navbar_cart_quantity(len(self.cart_items))
                elif response.status_code == 404:
                    rx.toast.error("Item not found in cart")
                else:
                    error = response.json().get('error', 'Failed to remove item')
                    rx.toast.error(f"Error: {error}")
                    
        except Exception as e:
            rx.toast.error(f"Network error: {e}")
            print(f"Exception in remove_item: {e}")

    async def remove_all(self):
        """Clear all items from cart via API"""
        import httpx
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        
        if not self.cart_items:
            rx.toast.info("Cart is already empty")
            return
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{API_BASE_URL}/carts/clear_cart/",
                    cookies=cookies_dict,
                )
                
                if response.status_code == 200:
                
                    self.cart_items = []
                    rx.toast.success("Cart cleared successfully")
                    await self.update_navbar_cart_quantity(0)
                elif response.status_code == 404:
                    rx.toast.error("Cart not found")
                else:
                    error = response.json().get('error', 'Failed to clear cart')
                    rx.toast.error(f"Error: {error}")
                    
        except Exception as e:
            rx.toast.error(f"Failed to clear cart: {e}")
            print(f"Exception in remove_all: {e}")

                    
        except Exception as e:
            rx.toast.error(f"Failed to clear cart: {e}")
            print(f"Exception in remove_all: {e}")

    async def load_payment_methods(self):
        """Load all payment methods (credit cards and bank accounts)."""
        self.is_loading_payments = True
        await self.load_credit_cards()
        await self.load_bank_accounts()
        self.is_loading_payments = False 
    
    async def load_credit_cards(self):
        import httpx
        """Fetch all credit cards from backend."""
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"{API_BASE_URL}/users/payment_methods/",  
                    cookies=cookies_dict,
                    timeout=10.0
                )
            
            if res.status_code == 200:
                data = res.json()
                cards_data = data.get("payment_methods", [])  
                self.credit_cards = [
                    CreditCard(
                        id=card.get("id", 0),
                        card_brand=card.get("card_brand", ""),
                        last4=card.get("last4", ""),
                        exp_month=card.get("exp_month", 0),
                        exp_year=card.get("exp_year", 0),
                        is_default=card.get("is_default", False),
                        provider=card.get("provider", ""),
                        provider_token=card.get("provider_token", "")
                    )
                    for card in cards_data
                ]
                print(f"Loaded {len(self.credit_cards)} credit cards")
            else:
                print(f"Failed to load credit cards: {res.status_code}")
                self.credit_cards = []
                
        except Exception as e:
            print(f"Error loading credit cards: {e}")
            self.credit_cards = []

    async def load_bank_accounts(self):
        """Fetch all bank accounts from backend."""
        import httpx
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"{API_BASE_URL}/users/payment_methods/list_bank_accounts/",
                    cookies=cookies_dict,
                    timeout=10.0
                )
            
            if res.status_code == 200:
                data = res.json()
                accounts_data = data.get("bank_accounts", [])
                
                self.bank_accounts = [
                    BankAccount(
                        id=account.get("id", 0),
                        bank_name=account.get("bank_name", ""),
                        account_holder=account.get("account_holder", ""),
                        last4=account.get("last4", ""),
                        is_default=account.get("is_default", False),
                        provider=account.get("provider", ""),
                        provider_token=account.get("provider_token", "")
                    )
                    for account in accounts_data
                ]
                print(f"Loaded {len(self.bank_accounts)} bank accounts")
            else:
                print(f"Failed to load bank accounts: {res.status_code}")
                self.bank_accounts = []
                
        except Exception as e:
            print(f"Error loading bank accounts: {e}")
            self.bank_accounts = []

    
    promo_code: str = ""
    delivery_fee: int = 50
    discount: int = 100
    selected_payment: str = ""
    
    @rx.var
    def subtotal(self) -> int:
        return sum(item.price * item.quantity for item in self.cart_items)
    
    @rx.var
    def total(self) -> int:
        return self.subtotal + self.delivery_fee - self.discount
    
    def increment_quantity(self, item_id: int):
        for i, item in enumerate(self.cart_items):
            if item.id == item_id:
                updated_item = item.copy()
                updated_item.quantity += 1
                self.cart_items[i] = updated_item
                break
    
    def decrement_quantity(self, item_id: int):
        for i, item in enumerate(self.cart_items):
            if item.id == item_id and item.quantity > 1:
                updated_item = item.copy()
                updated_item.quantity -= 1
                self.cart_items[i] = updated_item
                break
    
    
    async def place_order(self):
        """Submit order via checkout API"""
        import httpx
        
        if not self.selected_payment:
            rx.toast.error("Please select a payment method")
            return
        
        if not self.cart_items:
            rx.toast.error("Cart is empty")
            return
        
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        
        # Parse payment type and method_id
        payment_parts = self.selected_payment.split("_")
        payment_type = "credit_card" if payment_parts[0] == "card" else "bank_account"
        method_id = payment_parts[1]
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/orders/checkout/",
                    data={
                        "payment_type": payment_type,
                        "method_id": method_id
                    },
                    cookies=cookies_dict,
                )
                
                if response.status_code == 201:
                    data = response.json()
                    order_id = data.get('order_id')
                    rx.toast.success("Order created successfully!")
                    print("order successfully added,", order_id)
                    # Redirect to orders list page
                    await self.update_navbar_cart_quantity(0)
                    return rx.redirect("/orders")
                    
                else:
                    error = response.json().get('error', 'Failed to place order')
                    rx.toast.error(f"Error: {error}")
                    
        except Exception as e:
            rx.toast.error(f"Network error: {e}")


def cart_item(item: CartItem) -> rx.Component:
    print(f"🎨 Rendering cart item with image: {item.image}") 
    return rx.box(
        rx.hstack(
          
            rx.checkbox(size="2"),
            
       
            rx.box(
                rx.image(
                    src=item.image,
                    width="120px",
                    height="120px",
                    object_fit="cover",
                    border_radius="8px",
                    bg="gray.100",
                ),
            ),
            
         
            rx.vstack(
                rx.hstack(
                    rx.text(
                        item.name,
                        font_size="18px",
                        font_weight="600",
                        color="#22282c"
                    ),
                    rx.badge(item.item_type, color_scheme="orange", variant="soft"),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.text("Colors:", font_size="14px",color="#22282c"),
                    rx.foreach(
                        item.colors,
                        lambda color: rx.box(
                            width="16px",
                            height="16px",
                            border_radius="50%",
                            bg=color,
                            border="1px solid #e2e8f0",
                        )
                    ),
                    spacing="2",
                ),
                rx.text(
                    f"Price: ${item.price} / per item",
                    color="#22282c",
                    font_size="14px",
                ),
                rx.hstack(
                    rx.button(
                        "−",
                        on_click=lambda: CartState.decrement_quantity(item.id),
                        variant="outline",
                        size="1",
                        border_radius="md",
                    ),
                    rx.text(item.quantity, font_weight="600",color="#22282c", min_width="30px", text_align="center"),
                    rx.button(
                        "+",
                        on_click=lambda: CartState.increment_quantity(item.id),
                        variant="outline",
                        size="1",
                        border_radius="md",
                    ),
                    spacing="2",
                ),
                spacing="2",
                align_items="start",
                flex="1",
            ),
            
           
            rx.vstack(
                rx.button(
                    rx.icon("trash-2", size=18),
                    on_click=lambda: CartState.remove_item(item.id),
                    variant="ghost",
                    color_scheme="red",
                ),
                rx.text(
                    f"$ {item.price * item.quantity}",
                    font_size="20px",
                    font_weight="700",
                    color="#22282c"
                ),
                spacing="4",
                align_items="end",
            ),
            
            spacing="4",
            align="start",
            width="100%",
        ),
        padding="20px",
        border="1px solid #e2e8f0",
        border_radius="12px",
        bg="white",
        width="100%",
    )


def order_summary() -> rx.Component:
  
    return rx.box(
        rx.vstack(
            rx.heading("Order Summary", size="7", margin_bottom="20px",color="#22282c",),
            
           
            rx.hstack(
                rx.text("Subtotal", font_size="18px",color="#22282c",),
                rx.spacer(),
                rx.text(f"$ {CartState.subtotal}", font_size="18px", font_weight="600",color="#22282c",),
                width="100%",
            ),
            
   
            rx.hstack(
                rx.text("Delivery", font_size="18px",color="#22282c",),
                rx.spacer(),
                rx.text(f"$ {CartState.delivery_fee}", font_size="18px", font_weight="600",color="#22282c"),
                width="100%",
            ),
            
       
            rx.hstack(
                rx.text("Discount", font_size="18px",color="#22282c",),
                rx.spacer(),
                rx.text(f"-$ {CartState.discount}", font_size="18px", font_weight="600",color="#22282c",),
                width="100%",
            ),
            
            
            rx.divider(margin_y="20px"),
            
        
            rx.hstack(
                rx.text("Total", font_size="24px", font_weight="700",color="#22282c",),
                rx.spacer(),
                rx.text(f"$ {CartState.total}", font_size="24px", font_weight="700",color="#22282c",),
                width="100%",
            ),
            
          
            rx.button(
                "Place Order",
                on_click=CartState.place_order,
                bg="#22282c",
                color="white",
                width="100%",
                padding="25px",
                border_radius="12px",
                font_size="16px",
                font_weight="bold",
                margin_top="20px",
                cursor = "pointer",
                _hover={
                    "color": "#22282c",
                    "border": "1px solid #22282c",
                    "background_color": "white"
                }
            ),
            
            spacing="4",
            
        ),
        padding="30px",
        border="1px solid #e2e8f0",
        border_radius="12px",
        bg="white",
        width="100%",
    )


def shipping_address() -> rx.Component:
 
    return rx.box(
        rx.vstack(
            rx.heading("Shipping Address", size="6", margin_bottom="20px", color="#22282c"),
            rx.hstack(
                rx.text(CartState.username, font_size="18px", font_weight="600",color="#22282c",),
                rx.spacer(),
                rx.text(CartState.phone_number, font_size="16px", color="#22282c",),
                width="100%",
            ),
            rx.hstack(
                rx.cond(
                    CartState.selected_address,
                    rx.text(
                        CartState.selected_address.name,
                        font_size="18px", 
                        font_weight="600",
                        color="#22282c"
                    ),
                   
                ),
                rx.spacer(),
                rx.cond(
                    CartState.selected_address,
                    rx.text(
                        CartState.selected_address.phone,
                        font_size="16px", 
                        color="#22282c"
                    ),
                    
                ),
                width="100%",
            ),
            
            rx.cond(
                CartState.selected_address,
                rx.text(
                    CartState.selected_address.address,
                    font_size="14px",
                    color="#22282c",
                    margin_top="8px",
                ),
                rx.text(
                    "3 Thanon Chalone Krun, Khwaeng lam Prathew Lam Pla Thio, Latkrabang, Bangkok, 10520",
                    font_size="14px",
                    color="#22282c",
                    margin_top="8px",
                ),
            ),
            
            rx.button(
                "See all Delivery Addresses",
                on_click=CartState.open_address_dialog,
                variant="ghost",
                color="#929FA7",
                text_decoration="underline",
                margin_top="12px",
                padding="0",
                cursor="pointer",
            ),
            
            spacing="2",
            align_items="start",
            width="500px",
        ),
        padding="30px",
        border="1px solid #e2e8f0",
        border_radius="12px",
        bg="white",
        margin_top="20px",
    )


def address_selection_dialog() -> rx.Component:
 
    return rx.dialog.root(
        rx.dialog.content(
            rx.box(
    
                rx.hstack(
                    rx.dialog.title(
                        "Select Delivery Address",
                        font_size="22px",
                        font_weight="700",
                        color="#1a1a1a",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon(
                            "x",
                            size=22,
                            color="#667085",
                            cursor="pointer",
                            _hover={"color": "#1a1a1a"},
                        ),
                        on_click=CartState.close_address_dialog(),
                    ),
                    align_items="center",
                    margin_bottom="12px",
                ),

                rx.dialog.description(
                    "Choose an address for your delivery below.",
                    color="#667085",
                    margin_bottom="20px",
                    font_size="14px",
                ),

                rx.box(
                    rx.cond(
                        CartState.addresses,
                        rx.vstack(
                            rx.foreach(
                                CartState.addresses,
                                lambda addr: address_card(addr)
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        rx.text(
                            "No addresses found. Please add an address first.",
                            color="#929FA7",
                            text_align="center",
                            padding="20px",
                            font_size="14px",
                        ),
                    ),
                    max_height="350px",
                    overflow_y="auto",
                    background_color="#f9fafb",
                    border_radius="12px",
                    padding="10px",
                    box_shadow="inset 0 0 4px rgba(0,0,0,0.05)",
                    margin_bottom="20px",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Cancel",
                            variant="soft",
                            color_scheme="gray",
                            font_weight="500",
                            padding_x="18px",
                            padding_y="8px",
                            border_radius="10px",
                            on_click=CartState.close_address_dialog(),
                        ),
                    ),
                    rx.spacer(),
                    rx.link(
                        rx.button(
                            "Add New Address",
                            variant="outline",
                            color_scheme="blue",
                            font_weight="600",
                            padding_x="18px",
                            padding_y="8px",
                            border_radius="10px",
                        ),
                        href="/profile?section=addresses",
                    ),
                    width="100%",
                    margin_top="10px",
                ),
            ),
            background_color="white",
            border_radius="16px",
            box_shadow="0 8px 30px rgba(0, 0, 0, 0.1)",
            padding="28px",
            max_width="600px",
        ),
        open=CartState.show_address_dialog,
    )


def address_card(addr: Address) -> rx.Component:
    """
    Individual address card in the selection dialog.
    """
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    addr.name,
                    font_size="16px",
                    font_weight="600",
                    color="#22282c",
                ),
                rx.cond(
                    addr.is_default,
                    rx.badge("Default", color_scheme="blue", variant="soft"),
                    rx.fragment(),
                ),
                rx.spacer(),
                rx.text(
                    addr.phone,
                    font_size="14px",
                    color="#929FA7",
                ),
                width="100%",
                align_items="center",
            ),
            
            rx.text(
                addr.address,
                font_size="14px",
                color="#22282c",
                margin_top="8px",
            ),
            
            spacing="2",
            align_items="start",
            width="100%",
        ),
        padding="16px",
        border="2px solid",
        border_color=rx.cond(
            CartState.selected_address.id == addr.id,
            "#3b82f6",  
            "#e2e8f0", 
        ),
        border_radius="8px",
        bg=rx.cond(
            CartState.selected_address.id == addr.id,
            "#eff6ff", 
            "white",
        ),
        cursor="pointer",
        on_click=lambda: CartState.select_address(addr),
        _hover={"border_color": "#3b82f6"},
        transition="all 0.2s ease",
        width="100%",
    )

def payment_method() -> rx.Component:
    """Payment method selection with credit cards and bank accounts"""
    return rx.box(
        rx.vstack(
         
            rx.vstack(
                rx.heading(
                    "Payment Method",
                    size="7",
                    color="#22282c",
                    margin_bottom="8px"
                ),
                rx.text(
                    "Select your preferred payment method",
                    font_size="14px",
                    color="#929FA7"
                ),
                spacing="2",
                align_items="start",
                width="100%",
                margin_bottom="24px"
            ),

        
            rx.hstack(
            
                rx.vstack(
                    rx.hstack(
                        rx.icon("credit-card", size=20, color="#2E6FF2"),
                        rx.text(
                            "Credit Cards",
                            font_size="18px",
                            font_weight="600",
                            color="#22282C"
                        ),
                        spacing="2",
                        align_items="center",
                        margin_bottom="16px"
                    ),

                    rx.box(
                        rx.cond(
                            CartState.credit_cards.length() > 0,
                            rx.vstack(
                                rx.foreach(
                                    CartState.credit_cards,
                                    lambda card: credit_card_payment_item(card)
                                ),
                                spacing="3",
                                width="100%"
                            ),
                            rx.center(
                                rx.text(
                                    "No credit cards added",
                                    color="#929FA7",
                                    font_size="14px"
                                ),
                                padding="40px",
                                width="100%"
                            )
                        ),
                        max_height="400px",
                        overflow_y="auto",
                        padding_right="8px",
                        width="100%"
                    ),

                    rx.link(
                        rx.button(
                            "+ Add New Card",
                            width="100%",
                            variant="outline",
                            color="#2E6FF2",
                            border="2px dashed #D1D5DB",
                            border_radius="8px",
                            padding="12px",
                            margin_top="12px",
                            cursor="pointer",
                            _hover={
                                "border_color": "#2E6FF2",
                                "background_color": "#EFF6FF"
                            }
                        ),
                        href="/profile?section=card"
                    ),

                    spacing="3",
                    align_items="start",
                    width="100%",
                    flex="1"
                ),

                rx.vstack(
                    rx.hstack(
                        rx.icon("landmark", size=20, color="#10B981"),
                        rx.text(
                            "Bank Accounts",
                            font_size="18px",
                            font_weight="600",
                            color="#22282C"
                        ),
                        spacing="2",
                        align_items="center",
                        margin_bottom="16px"
                    ),

                    rx.box(
                        rx.cond(
                            CartState.bank_accounts.length() > 0,
                            rx.vstack(
                                rx.foreach(
                                    CartState.bank_accounts,
                                    lambda account: bank_account_payment_item(account)
                                ),
                                spacing="3",
                                width="100%"
                            ),
                            rx.center(
                                rx.text(
                                    "No bank accounts added",
                                    color="#929FA7",
                                    font_size="14px"
                                ),
                                padding="40px",
                                width="100%"
                            )
                        ),
                        max_height="400px",
                        overflow_y="auto",
                        padding_right="8px",
                        width="100%"
                    ),

                    rx.link(
                        rx.button(
                            "+ Add New Bank Account",
                            width="100%",
                            variant="outline",
                            color="#10B981",
                            border="2px dashed #D1D5DB",
                            border_radius="8px",
                            padding="12px",
                            margin_top="12px",
                            cursor="pointer",
                            _hover={
                                "border_color": "#10B981",
                                "background_color": "#D1FAE5"
                            }
                        ),
                        href="/profile?section=card"
                    ),

                    spacing="3",
                    align_items="start",
                    width="100%",
                    flex="1"
                ),

                spacing="6",
                width="100%",
                align="start"
            ),

            rx.cond(
                CartState.selected_payment != "",
                rx.box(
                    rx.hstack(
                        rx.icon("check", size=18, color="#10B981"),
                        rx.text(
                            "Payment method selected",
                            font_size="14px",
                            color="#22282C",
                            font_weight="500"
                        ),
                        spacing="2",
                        align_items="center"
                    ),
                    padding="16px",
                    background_color="#F9FAFB",
                    border_radius="8px",
                    border="1px solid #E5E7EB",
                    margin_top="24px",
                    width="100%"
                ),
                rx.fragment()
            ),

            spacing="4",
            width="100%"
        ),
        padding="30px",
        border="1px solid #e2e8f0",
        border_radius="12px",
        bg="white",
        width="100%",
        margin_top="20px"
    )


def credit_card_payment_item(card: CreditCard) -> rx.Component:
    """Individual credit card selection item"""
    is_selected = CartState.selected_payment == f"card_{card.id}"
    
    return rx.box(
        rx.hstack(
    
            rx.hstack(
                rx.box(
                    rx.icon(
                        "credit-card",
                        size=24,
                        color="#2E6FF2"
                    ),
                    padding="12px",
                    border_radius="8px",
                    bg="#EFF6FF"
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            card.card_brand,
                            font_size="16px",
                            font_weight="600",
                            color="#22282C"
                        ),
                        rx.cond(
                            card.is_default,
                            rx.badge(
                                "Default",
                                color_scheme="green",
                                variant="soft"
                            ),
                            rx.fragment()
                        ),
                        spacing="2",
                        align_items="center"
                    ),
                    rx.text(
                        f"•••• •••• •••• {card.last4}",
                        font_size="14px",
                        color="#6B7280"
                    ),
                    rx.text(
                        f"Expires {card.exp_month}/{card.exp_year}",
                        font_size="12px",
                        color="#9CA3AF"
                    ),
                    spacing="1",
                    align_items="start"
                ),
                spacing="3",
                align_items="center",
                flex="1"
            ),

            rx.cond(
                is_selected,
                rx.box(
                    rx.icon("check", size=16, color="white"),
                    width="24px",
                    height="24px",
                    border_radius="50%",
                    bg="#2E6FF2",
                    display="flex",
                    align_items="center",
                    justify_content="center"
                ),
                rx.fragment()
            ),

            width="100%",
            align_items="center",
            justify_content="space-between"
        ),
        padding="20px",
        border=f"2px solid {rx.cond(is_selected, '#2E6FF2', '#E5E7EB')}",
        border_radius="12px",
        bg=rx.cond(is_selected, "#EFF6FF", "white"),
        cursor="pointer",
        on_click=lambda: CartState.select_payment(f"card_{card.id}"),
        _hover={
            "border_color": "#2E6FF2",
            "transform": "translateY(-2px)",
            "box_shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
        },
        transition="all 0.2s ease",
        width="100%"
    )


def bank_account_payment_item(account: BankAccount) -> rx.Component:
    """Individual bank account selection item"""
    is_selected = CartState.selected_payment == f"bank_{account.id}"
    
    return rx.box(
        rx.hstack(
    
            rx.hstack(
                rx.box(
                    rx.icon(
                        "landmark",
                        size=24,
                        color="#10B981"
                    ),
                    padding="12px",
                    border_radius="8px",
                    bg="#D1FAE5"
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            account.bank_name,
                            font_size="16px",
                            font_weight="600",
                            color="#22282C"
                        ),
                        rx.cond(
                            account.is_default,
                            rx.badge(
                                "Default",
                                color_scheme="green",
                                variant="soft"
                            ),
                            rx.fragment()
                        ),
                        spacing="2",
                        align_items="center"
                    ),
                    rx.text(
                        account.account_holder,
                        font_size="14px",
                        color="#6B7280"
                    ),
                    rx.text(
                        f"•••• •••• •••• {account.last4}",
                        font_size="12px",
                        color="#9CA3AF"
                    ),
                    spacing="1",
                    align_items="start"
                ),
                spacing="3",
                align_items="center",
                flex="1"
            ),

            rx.cond(
                is_selected,
                rx.box(
                    rx.icon("check", size=16, color="white"),
                    width="24px",
                    height="24px",
                    border_radius="50%",
                    bg="#10B981",
                    display="flex",
                    align_items="center",
                    justify_content="center"
                ),
                rx.fragment()
            ),

            width="100%",
            align_items="center",
            justify_content="space-between"
        ),
        padding="20px",
        border=f"2px solid {rx.cond(is_selected, '#10B981', '#E5E7EB')}",
        border_radius="12px",
        bg=rx.cond(is_selected, "#D1FAE5", "white"),
        cursor="pointer",
        on_click=lambda: CartState.select_payment(f"bank_{account.id}"),
        _hover={
            "border_color": "#10B981",
            "transform": "translateY(-2px)",
            "box_shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
        },
        transition="all 0.2s ease",
        width="100%"
    )


def cart_content() -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.heading(
                "YOUR CART",
                text_align="center",
                margin_bottom="30px",
                font_size="32px",
                color="#22282c",
                font_family="Poppins"
            ),
            
            rx.box(
                rx.hstack(
                    rx.vstack(
                        rx.box(
                            rx.vstack(
                                rx.foreach(
                                    CartState.cart_items,
                                    cart_item,
                                ),
                                spacing="4",
                                width="100%",
                            ),
                            max_height="700px",  
                            overflow_y="auto",
                            padding_right="10px",
                            width="100%",
                        ),

                        rx.button(
                            "Remove all from cart",
                            on_click=CartState.remove_all,
                            variant="ghost",
                            color="#929FA7",
                            text_decoration="underline",
                            margin_top="12px",
                            cursor="pointer",
                            padding="0",
                            _hover={"color": "#22282c"}
                        ),
                        spacing="4",
                        align_items="start",
                        width="55%"
                    ),
                    
                    rx.vstack(
                        order_summary(),
                        shipping_address(),
                        spacing="4",
                        align_items="start",
                        width="45%"
                    ),
                    
                    spacing="6",
                    align="start",
                    width="100%",
                    justify="center",   
                ),
                padding="30px",
                border_radius="12px",
                width="100%",          
                margin_x="auto",     
            ),
            
            payment_method(),
            address_selection_dialog(),
            
            spacing="5",
            width="100%",
            padding_y="40px",
            align_items="center",
        ),
        
        min_height="100vh",
        width="100%",
        justify="center",
        align="center",
        
    )

@rx.page(route="/cart", on_load=[CartState.load_cart, CartState.load_user_data, CartState.load_payment_methods])
def cart_page() -> rx.Component:
    return template(cart_content)

