import reflex as rx
from ..template import template

class ProfileState(rx.State):
    active_section: str = "profile"
    show_address_form: bool = False
    show_password_form: bool = False
    has_addresses: bool = False
    
    full_name: str = ""
    phone_number: str = ""
    province: str = ""
    street_address: str = ""
    
    current_password: str = ""
    new_password: str = ""
    confirm_password: str = ""
    
    def set_section(self, section: str):
        self.active_section = section
    
    def toggle_address_form(self):
        self.show_address_form = not self.show_address_form
    
    def open_address_form(self):
        self.show_address_form = True
    
    def close_address_form(self):
        self.show_address_form = False
    
    def open_password_form(self):
        self.show_password_form = True
    
    def close_password_form(self):
        self.show_password_form = False
        self.current_password = ""
        self.new_password = ""
        self.confirm_password = ""
    
    def submit_address(self):
        self.has_addresses = True
        self.show_address_form = False
        self.full_name = ""
        self.phone_number = ""
        self.province = ""
        self.street_address = ""
    
    def submit_password_change(self):
        # Add password validation logic here
        self.show_password_form = False
        self.current_password = ""
        self.new_password = ""
        self.confirm_password = ""

def profile_content() -> rx.Component:
    return rx.hstack(
  
        rx.box(
            rx.vstack(
                rx.center(
                    rx.avatar(
                        fallback="JS",
                        size="8",
                        radius="full",
                    ),
                    style={"margin": "20px 0px", "width": "100%"},
                ),
                
                rx.center(
                    rx.text("John Smith", font_size="18px", font_weight="bold", color="#22282C"),
                    width="100%",
                ),
                
                rx.vstack(
                    nav_button("Personal Information", "profile"),
                    nav_button("My Address", "address"),
                    nav_button("Wishlist", "wishlist"),
                    nav_button("My Orders", "orders"),
                    nav_button("My Reviews", "reviews"),
                    nav_button("Notification", "notification"),
                    rx.link("Logout", href="/logout", style=menu_item_style(False)),
                    spacing="3",
                ),
            ),
            width="280px",
            height="100%",
            bg="#F9FAFB",
        ),
 
      
        rx.box(
            rx.match(
                ProfileState.active_section,
                ("profile", profile_info_content()),
                ("address", address_content()),
                ("wishlist", wishlist_content()),
                ("orders", orders_content()),
                ("reviews", reviews_content()),
                ("notification", notification_content()),
                profile_info_content(),  
            ),
            flex="1",
            padding="40px",
            bg="white",
        ),
        
        # Password Change Modal
        password_change_modal(),
    
        width="100%",
        height="100vh",
    )

def nav_button(text: str, section: str) -> rx.Component:
    return rx.button(
        text,
        on_click=lambda: ProfileState.set_section(section),
        style=rx.cond(
            ProfileState.active_section == section,
            menu_item_style(True),
            menu_item_style(False),
        ),
    )

def profile_info_content() -> rx.Component:
   
    return rx.vstack(
        rx.center(
            rx.text(
                "Personal Information",
                font_size="20px",
                font_weight="bold",
                margin_bottom="20px",
                color="#22282c"
            ),
            width="100%",
        ),

        rx.hstack(
            input_with_label("First Name", "John"),
            input_with_label("Last Name", "Smith"),
            spacing="4",
            width="100%",
        ),

        input_with_label("Username", "John_Smith007"),
        input_with_label("E-mail", "JohnSmith007@gmail.com"),
        input_with_label("Mobile No.", "08 768987677"),

        rx.hstack(
            select_with_label("Gender (Optional)", ["Male", "Female", "Other"]),
            input_with_label_Date("Birthday (Optional)", ""),
            spacing="4",
            width="100%",
        ),

        rx.button(
            "Save",
            width="100%",
            bg="#22282C",
            color="white",
            border_radius="8px",
            padding="20px",
        ),

        rx.button(
            "Change Password",
            on_click=ProfileState.open_password_form,
            width="100%",
            variant="outline",
            border_radius="8px",
            margin_top="12px",
            padding="30px",
            color="#22282c",
            border="0.5px solid #929FA7",
        ),
        
        spacing="5",
        width="100%",
    )

def password_change_modal() -> rx.Component:
    return rx.cond(
        ProfileState.show_password_form,
        rx.box(
            rx.box(
                rx.vstack(
                    rx.box(
                        rx.icon(
                            tag="x",
                            size=28,
                            color="#6B7280",
                            cursor="pointer",
                            on_click=ProfileState.close_password_form,
                            _hover={"color": "#22282C"},
                        ),
                        width="100%",
                        display="flex",
                        justify_content="flex-end",
                    ),
                    rx.center(
                        rx.text(
                            "Change Password",
                            font_size="24px",
                            font_weight="bold",
                            color="#22282C",
                        ),
                        width="100%",

                    ),
                 
                        rx.text(
                            "Please enter a new password",
                            font_size="16px",
                            color="#22282C",
                        ),
                
                  
                    rx.vstack(
                        rx.text("Current Password", font_size="16px", font_weight="600", color="#22282C"),
                        rx.box(
                            rx.input(
                                type="password",
                                placeholder="Enter a password ( at least 6 characters )",
                                value=ProfileState.current_password,
                                on_change=ProfileState.set_current_password,
                                width="100%",
                                padding="18px",
                                border="1px solid #D1D5DB",
                                border_radius="12px",
                                font_size="16px",
                                color="#22282C",
                            ),
                            rx.icon(
                                tag="eye",
                                size=24,
                                color="#9CA3AF",
                                position="absolute",
                                right="18px",
                                top="50%",
                                transform="translateY(-50%)",
                                cursor="pointer",
                            ),
                            position="relative",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                        align_items="flex-start",
                    ),
                    
             
                    rx.box(
                        rx.text(
                            "Forget Password ?",
                            font_size="16px",
                            color="#EF4444",
                            cursor="pointer",
                            _hover={"text_decoration": "underline"},
                        ),
                        width="100%",
                        text_align="right",
                        margin_top="-20px",
                    
                    ),
                    
                  
                    rx.vstack(
                        rx.text("New Password", font_size="16px", font_weight="600", color="#22282C"),
                        rx.box(
                            rx.input(
                                type="password",
                                placeholder="Enter a password ( at least 6 characters )",
                                value=ProfileState.new_password,
                                on_change=ProfileState.set_new_password,
                                width="100%",
                                padding="18px",
                                border="1px solid #D1D5DB",
                                border_radius="12px",
                                font_size="16px",
                                color="#22282C",
                            ),
                            rx.icon(
                                tag="eye",
                                size=24,
                                color="#9CA3AF",
                                position="absolute",
                                right="18px",
                                top="50%",
                                transform="translateY(-50%)",
                                cursor="pointer",
                            ),
                            position="relative",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                        align_items="flex-start",
                    ),
                    
                
                    rx.vstack(
                        rx.text("Confirm New Password", font_size="16px", font_weight="600", color="#22282C"),
                        rx.box(
                            rx.input(
                                type="password",
                                placeholder="Enter a password ( at least 6 characters )",
                                value=ProfileState.confirm_password,
                                on_change=ProfileState.set_confirm_password,
                                width="100%",
                                padding="18px",
                                border="1px solid #D1D5DB",
                                border_radius="12px",
                                font_size="16px",
                                color="#22282C",
                            ),
                            rx.icon(
                                tag="eye",
                                size=24,
                                color="#9CA3AF",
                                position="absolute",
                                right="18px",
                                top="50%",
                                transform="translateY(-50%)",
                                cursor="pointer",
                            ),
                            position="relative",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                        align_items="flex-start",
                    ),
                    
                    
                    rx.button(
                        "Change Password",
                        on_click=ProfileState.submit_password_change,
                        width="100%",
                        bg="#22282C",
                        color="white",
                        border_radius="12px",
                        padding="18px",
                        font_size="18px",
                        font_weight="600",
                        cursor="pointer",
                        margin_top="20px",
                        border="none",
                        _hover={"opacity": "0.9"},
                    ),
                    
                    spacing="6",
                    width="100%",
                ),
                bg="white",
                padding="20px 50px",
                border_radius="20px",
                width="600px",
                max_width="90vw",
                max_height="90vh",
                overflow_y="auto",
                box_shadow="0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
                position="relative",
            ),
            position="fixed",
            top="0",
            left="0",
            right="0",
            bottom="0",
            bg="rgba(0, 0, 0, 0.5)",
            display="flex",
            align_items="center",
            justify_content="center",
            z_index="1001",
            
        ),
        rx.fragment(),
    )


def address_content() -> rx.Component:

    return rx.box(
  
        rx.cond(
            ~ProfileState.has_addresses,
            rx.center(
                rx.box(
                    rx.vstack(
                       
                        rx.center(
                            rx.icon(
                                tag="map-pin",
                                size=48,
                                color="white",
                            ),
                            width="100px",
                            height="100px",
                            bg="#22282C",
                            border_radius="50%",
                        ),
                        
                        rx.text(
                            "No Address",
                            font_size="24px",
                            font_weight="600",
                            color="#22282C",
                        ),
                        
                        rx.text(
                            "Please add your address",
                            font_size="16px",
                            color="#6B7280",
                        ),
                        
                        rx.button(
                            "Add New Address",
                            on_click=ProfileState.toggle_address_form,
                            width="100%",
                            bg="#22282C",
                            color="white",
                            border_radius="12px",
                            padding="18px",
                            font_size="16px",
                            font_weight="500",
                            cursor="pointer",
                            border="none",
                            _hover={"opacity": "0.9"},

                            
                        ),
                        
                        
                        align_items="center",
                        spacing="4",
                        width="100%",
                    ),
                    
                    bg="white",
                    border="1px solid #E5E7EB",
                    border_radius="16px",
                    padding="60px 40px",
                    width="100%",
                    max_width="700px",
                ),
                width="100%",
                height="100%",
                padding="40px",
            ),
            rx.vstack(
                rx.text("Your saved addresses will appear here...", color="#22282c"),
                spacing="5",
                width="100%",
            ),
        ),

        rx.cond(
            ProfileState.show_address_form,
            rx.box(
                rx.box(
                    rx.vstack(
                       
                       rx.hstack(
                            rx.text(
                                "My Address",
                                font_size="28px",
                                font_weight="700",
                                color="#22282C",
                            ),
                            rx.spacer(),  
                            rx.icon(
                                tag="x",
                                size=28,
                                color="#6B7280",
                                cursor="pointer",
                                on_click=ProfileState.close_address_form,
                                _hover={"color": "#22282C"},
                            ),
                            align_items="center", 
                            width="100%",          
                        ),
                        
                     
                        rx.vstack(
                            rx.text("Full Name", font_size="16px", font_weight="600", color="#22282C"),
                            rx.input(
                                placeholder="John Smith",
                                default_value=ProfileState.full_name,
                                width="100%",
                                padding="20px",
                                border="1px solid #D1D5DB",
                                border_radius="12px",
                                font_size="20px",
                                color="black",
                            ),
                            spacing="2",
                            width="100%",
                            align_items="flex-start",
                        ),
                        
                 
                        rx.vstack(
                            rx.text("Phone Number", font_size="16px", font_weight="600", color="#22282C"),
                            rx.input(
                                placeholder="+666 34567892",
                                default_value=ProfileState.phone_number,
                                width="100%",
                                padding="20px",
                                border="1px solid #D1D5DB",
                                border_radius="12px",
                                font_size="16px",
                                color="#9CA3AF",
                            ),
                            spacing="2",
                            width="100%",
                            align_items="flex-start",
                        ),
                        
                       
                        rx.vstack(
                            rx.text("Province", font_size="16px", font_weight="600", color="#22282C"),
                            rx.select(
                                ["Province, District, Sub District, Postal Code"],
                                placeholder="Province, District, Sub District, Postal Code",
                                width="100%",
                                size="3",
                            ),
                            spacing="2",
                            width="100%",
                            align_items="flex-start",
                        ),
                        
                      
                        rx.vstack(
                            rx.text("Street Name, Building, House No.", font_size="16px", font_weight="600", color="#22282C"),
                            rx.input(
                                placeholder="Street Name, Building, House No.",
                                width="100%",
                                padding="20px",
                                border="1px solid #D1D5DB",
                                border_radius="12px",
                                font_size="16px",
                                color="#9CA3AF",
                            ),
                            spacing="2",
                            width="100%",
                            align_items="flex-start",
                        ),
                        
                       
                        rx.button(
                            "Submit",
                            width="100%",
                            bg="#22282C",
                            color="white",
                            border_radius="12px",
                            padding="18px",
                            font_size="16px",
                            font_weight="500",
                            cursor="pointer",
                            margin_top="10px",
                            border="none",
                            _hover={"opacity": "0.9"},
                        ),
                        
                        spacing="6",
                        width="100%",
                    ),
                    bg="white",
                    padding="50px",
                    border_radius="20px",
                    width="600px",
                    max_width="90vw",
                    max_height="90vh",
                    overflow_y="auto",
                    box_shadow="0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
                    position="relative",
                ),
                position="fixed",
                top="0",
                left="0",
                right="0",
                bottom="0",
                bg="rgba(0, 0, 0, 0.5)",
                display="flex",
                align_items="center",
                justify_content="center",
                z_index="1000",
                
            ),
            rx.fragment(),
        ),
        
        position="relative",
        width="100%",
        height="100%",
    )



def wishlist_content() -> rx.Component:
    return rx.vstack(
        rx.center(
            rx.text(
                "Wishlist",
                font_size="20px",
                font_weight="bold",
                margin_bottom="20px",
                color="#22282c"
            ),
            width="100%",
        ),
        rx.text("Your wishlist items will appear here...", color="#22282c"),
        spacing="5",
        width="100%",
    )

def orders_content() -> rx.Component:
    return rx.vstack(
        rx.center(
            rx.text(
                "My Orders",
                font_size="20px",
                font_weight="bold",
                margin_bottom="20px",
                color="#22282c"
            ),
            width="100%",
        ),
        rx.text("Your order history will appear here...", color="#22282c"),
        spacing="5",
        width="100%",
    )

def reviews_content() -> rx.Component:
    return rx.vstack(
        rx.center(
            rx.text(
                "My Reviews",
                font_size="20px",
                font_weight="bold",
                margin_bottom="20px",
                color="#22282c"
            ),
            width="100%",
        ),
        rx.text("Your reviews will appear here...", color="#22282c"),
        spacing="5",
        width="100%",
    )

def notification_content() -> rx.Component:
    return rx.vstack(
        rx.center(
            rx.text(
                "Notifications",
                font_size="20px",
                font_weight="bold",
                margin_bottom="20px",
                color="#22282c"
            ),
            width="100%",
        ),
        rx.text("Your notifications will appear here...", color="#22282c"),
        spacing="5",
        width="100%",
    )

def input_with_label(label: str, value: str = "") -> rx.Component:
    return rx.vstack(
        rx.text(label, font_size="14px", font_weight="500", margin_bottom="4px"),
        rx.input(default_value=value, placeholder=label, width="100%", style=input_style),
        spacing="1",
        width="100%",
        color="#22282c",
    )

def input_with_label_Date(label: str, value: str = "") -> rx.Component:
    return rx.vstack(
        rx.text(label, font_size="14px", font_weight="500", margin_bottom="4px"),
        rx.input(type="date", default_value=value, placeholder=label, width="100%", style=input_style),
        spacing="1",
        width="100%",
        color="#22282c",
    )

def select_with_label(label: str, options: list[str]) -> rx.Component:
    return rx.vstack(
        rx.text(label, font_size="14px", font_weight="500", margin_bottom="4px"),
        rx.select(options, placeholder=label, width="100%"),
        spacing="1",
        width="100%",
        color="#22282c",
    )

def menu_item_style(active: bool = False):
    return {
        "padding": "12px",
        "font_size": "15px",
        "text_decoration": "none",
        "width": "280px",
        "border": "none",
        "cursor": "pointer",
        "text_align": "left",
        "color":"white",
        "background_color": "#22282C", 
    }

def profile_page() -> rx.Component:
    return template(profile_content)

input_style = {
    "color": "#22282C",
    "background_color": "white",
    "border": "1px solid #929FA7",
    "border_radius": "8px",
}