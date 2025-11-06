import reflex as rx
from ..state import AuthState

class LoginState(rx.State):
    # Form fields
    identifier: str = ""
    password: str = ""
    
    # UI state
    is_loading: bool = False
    error_message: str = ""
    
    def set_identifier(self, value: str):
        self.identifier = value
        self.error_message = ""
    
    def set_password(self, value: str):
        self.password = value
        self.error_message = ""
    
    def reset_form(self):
        """Reset form state when page loads"""
        self.identifier = ""
        self.password = ""
        self.error_message = ""
        self.is_loading = False
    
    async def handle_login(self):
        """Handle login form submission"""
        # Validation
        if not self.identifier.strip():
            self.error_message = "Username or email is required"
            return
        
        if not self.password:
            self.error_message = "Password is required"
            return
        
        # Clear error and set loading
        self.error_message = ""
        self.is_loading = True
        
        try:
            # Get auth state and call login
            auth_state = await self.get_state(AuthState)
            
            # Perform login
            result = await auth_state.login(self.identifier.strip(), self.password)
            
            # If we get here and auth is successful, redirect will happen
            # Clear the form
            self.password = ""
            self.identifier = ""
            
            return result
            
        except Exception as e:
            self.error_message = f"Login error: {str(e)}"
            self.is_loading = False
        finally:
            # Reset loading state
            self.is_loading = False


def login_page() -> rx.Component:
    return rx.center(
        rx.card(
            rx.vstack(
                # Error Message
                rx.cond(
                    LoginState.error_message != "",
                    rx.callout(
                        LoginState.error_message,
                        icon="triangle_alert",
                        color_scheme="red",
                        size="2",
                        width="100%",
                    )
                ),
                
                # Header
                rx.center(
                    rx.heading(
                        "Sign in to your account",
                        size="6",
                        as_="h2",
                        text_align="center",
                        width="100%",
                        color="#22282C",
                    ),
                    direction="column",
                    spacing="5",
                    width="100%",
                ),
                
                # Username or Email Field
                rx.vstack(
                    rx.text(
                        "Username or Email",
                        size="3",
                        weight="medium",
                        text_align="left",
                        width="100%",
                        color="#22282C",
                    ),
                    rx.input(
                        rx.input.slot(
                            rx.icon("user", style={"color": "#929FA7", "width": "20px", "height": "20px"})
                        ),
                        placeholder="myopapakyaw or user@reflex.dev",
                        type="text",
                        size="3",
                        width="100%",
                        color="#22282C",
                        background_color="white",
                        border="1px solid #929FA7",
                        border_radius="8px",
                        value=LoginState.identifier,
                        on_change=LoginState.set_identifier,
                    ),
                    justify="start",
                    spacing="2",
                    width="100%",
                    margin_bottom="-1.5rem"
                ),
                
                # Password Field
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            "Password",
                            size="3",
                            weight="medium",
                            color="#22282C",
                        ),
                        rx.link(
                            "Forgot password?",
                            href="#",
                            size="3",
                        ),
                        justify="between",
                        width="100%",
                    ),
                    rx.input(
                        rx.input.slot(
                            rx.icon("lock", style={"color": "#929FA7", "width": "20px", "height": "20px"})
                        ),
                        placeholder="Enter your password",
                        type="password",
                        size="3",
                        width="100%",
                        color="#22282C",
                        background_color="white",
                        border="1px solid #929FA7",
                        border_radius="8px",
                        value=LoginState.password,
                        on_change=LoginState.set_password,
                        # Add Enter key support
                        on_key_down=lambda key: rx.cond(
                            key == "Enter",
                            LoginState.handle_login(),
                            rx.noop()
                        ),
                    ),
                    spacing="2",
                    width="100%",
                    margin_bottom="-1.5rem"
                ),
                
                # Sign Up Link
                rx.hstack(
                    rx.text("New here?", size="3", color="#22282C"),
                    rx.link("Sign up", href="/signup", size="3"),
                    opacity="0.8",
                    spacing="2",
                    width="100%",
                ),
                
                # Sign In Button
                rx.button(
                    rx.cond(
                        LoginState.is_loading,
                        rx.hstack(
                            rx.spinner(size="3"),
                            rx.text("Signing in..."),
                            spacing="2",
                        ),
                        rx.text("Sign In"),
                    ),
                    size="3",
                    width="100%",
                    background_color="#22282C",
                    cursor="pointer",
                    border_radius="8px",
                    _hover={"background_color": "white", "color": "#22282C", "border": "1px solid #929FA7"},
                    on_click=LoginState.handle_login,
                    disabled=LoginState.is_loading,
                ),
                
                # Divider
                rx.hstack(
                    rx.divider(margin="0", border_color="#E9EBEC", border_width="1px", width="100%"),
                    rx.text(
                        "Or Sign In with",
                        white_space="nowrap",
                        weight="medium",
                        color="#22282C",
                    ),
                    rx.divider(margin="0", border_color="#E9EBEC", border_width="1px", width="100%"),
                    align="center",
                    width="100%",
                ),
                
                # Social Login Buttons
                rx.center(
                    rx.icon_button(
                        rx.icon(tag="chrome"),
                        variant="soft",
                        size="3",
                        border_radius="100px",
                        color="#22282C",
                        background_color="white",
                        border="1px solid #929FA7",
                    ),
                    rx.icon_button(
                        rx.icon(tag="facebook"),
                        variant="soft",
                        size="3",
                        radius="full",
                        border_radius="100px",
                        color="#22282C",
                        background_color="white",
                        border="1px solid #929FA7",
                    ),
                    rx.icon_button(
                        rx.icon(tag="instagram"),
                        variant="soft",
                        size="3",
                        border_radius="100px",
                        color="#22282C",
                        background_color="white",
                        border="1px solid #929FA7",
                    ),
                    rx.icon_button(
                        rx.icon(tag="twitter"),
                        variant="soft",
                        size="3",
                        border_radius="100px",
                        color="#22282C",
                        background_color="white",
                        border="1px solid #929FA7",
                    ),
                    spacing="4",
                    direction="row",
                    width="100%",
                ),
                
                spacing="6",
                width="100%",
            ),
            max_width="28em",
            size="4",
            width="100%",
            background_color="white",
        ),
        height="100vh",
        # 👇 Reset form state when page loads
        on_mount=[LoginState.reset_form, AuthState.check_auth],
    )

background_style = {
    "width": "100%",
    "align_items": "center",
    "background_color": "white",
}

input_style = {
    "color": "#22282C",
    "background_color": "white",
    "border": "1px solid #929FA7",
    "border_radius": "8px",
  
}

border_style = {
    "border_radius": "100px" ,
    "color":"#22282C",
    "background_color":"white",
    "border": "1px solid #929FA7"}

divider_style = {
    "border_color": "#E9EBEC",
    "border_width": "1px",
    "width": "100%",
}