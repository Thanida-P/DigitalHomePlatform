import os
import reflex as rx
from ..template import template
from ..state import AuthState
import httpx
from typing import Optional, Callable, Any
import json
import random
import string
from ..config import API_BASE_URL
import base64


class Address(rx.Base):
    id: int
    address: str
    is_default: bool


class Address(rx.Base):
    id: int
    address: str
    is_default: bool = False

class AddressState(rx.State):
    show_form: bool = False
    addresses: list[Address] = []
    new_address: str = ""
    editing_address_id: int = 0
    is_loading: bool = False
    error_message: str = ""
    success_message: str = ""


    def start_edit_address(self, address_id: int, current_address: str):
        self.editing_address_id = address_id
        self.show_form = True  # reuse the form modal for editing
        self.new_address = current_address  # pre-fill with existing address
        print(f"Starting edit for address ID {address_id}: {current_address}")


    def toggle_form(self):
        """Toggle visibility of the address form."""
        self.show_form = True
        self.editing_address_id = 0  # Reset editing state
        self.new_address = ""  # Clear input field
        print("Opening address form.")

    def close_form(self):
        """Close the address form and clear input."""
        self.show_form = False
        self.new_address = ""
        self.editing_address_id = 0  # Reset editing state

    def set_new_address(self, value: str):
        """Update the new_address field."""
        self.new_address = value

    async def save_address(self):
        """Save address (add new or update existing)."""
        if self.editing_address_id == 0:
            # Adding new address
            await self.add_address()
        else:
            # Editing existing address
            await self.edit_address(self.editing_address_id, self.new_address)

    async def add_address(self):
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}

        if not self.new_address.strip():
            print("No address entered. Skipping.")
            return

        data = {"address": self.new_address.strip(), "is_default": False}
        print("Sending new address to backend:", data)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/users/address/add/",
                    data=data,
                    cookies=cookies_dict,
                )
            print("POST response status:", response.status_code)

            if response.status_code == 201:
                # Reload addresses
                await self.load_addresses()
                self.new_address = ""
                self.show_form = False
                self.editing_address_id = 0
                print("Address added successfully.")
            else:
                print("Error adding address:", response.text)
        except Exception as e:
            print("Request failed:", e)



    async def load_addresses(self):
        """Fetch existing addresses from backend when the page loads."""
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
                        address=addr.get("address", ""),
                        is_default=addr.get("is_default", False)
                    )
                    for addr in addresses_list
                ]
                print("Addresses loaded:", self.addresses)
            else:
                print("Failed to fetch addresses:", res.text)
        except Exception as e:
            print("Request failed:", e)



    async def delete_address(self, address_id: int):
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}

        # Make DELETE request
        async with httpx.AsyncClient() as client:
            response = await client.request(
                "DELETE",
                f"{API_BASE_URL}/users/address/delete/",
                data=json.dumps({"address_id": address_id}),
                headers={"Content-Type": "application/json"},
                cookies=cookies_dict,
            )

        if response.status_code == 200:
            # Update reactive list safely
            new_addresses = [addr for addr in self.addresses if addr.id != address_id]
            self.addresses = new_addresses
        else:
            print("Failed to delete address:", response.text)


    async def edit_address(self, address_id: int, new_address: str):
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}

        if not new_address.strip():
            print("No address entered. Skipping.")
            return

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    "PUT",
                    f"{API_BASE_URL}/users/address/edit/",
                    data=json.dumps({"address_id": address_id, "address": new_address.strip()}),
                    headers={"Content-Type": "application/json"},
                    cookies=cookies_dict,
                )

            if response.status_code == 200:
                # Reload addresses from backend
                await self.load_addresses()
                self.new_address = ""
                self.show_form = False
                self.editing_address_id = 0
                print("Address updated successfully.")
            else:
                print("Failed to edit address:", response.text)
        except Exception as e:
            print("Request failed:", e)



    async def set_default_address(self, address_id: int):
        """Set an address as the default address"""
        self.is_loading = True
        self.error_message = ""
        self.success_message = ""
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        
        try:
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{API_BASE_URL}/users/address/set_default/",
                    json={"address_id": address_id},
                    headers={"Content-Type": "application/json"},
                    cookies=cookies_dict,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    self.success_message = "Default address updated successfully"
                    
                    updated_addresses = []
                    for addr in self.addresses:
                        addr_copy = addr.copy()
                        if addr_copy["id"] == address_id:
                            addr_copy["is_default"] = True
                        else:
                            addr_copy["is_default"] = False
                        updated_addresses.append(addr_copy)
                    
                    self.addresses = updated_addresses
                    
                elif response.status_code == 401:
                    self.error_message = "Authentication required"
                elif response.status_code == 403:
                    self.error_message = "Only customers can manage addresses"
                elif response.status_code == 404:
                    self.error_message = "Address not found"
                else:
                    data = response.json()
                    self.error_message = data.get("error", "Failed to set default address")
                    
        except httpx.TimeoutException:
            self.error_message = "Request timed out. Please try again."
        except httpx.RequestError as e:
            self.error_message = f"Connection error: {str(e)}"
        except Exception as e:
            self.error_message = f"An error occurred: {str(e)}"
        finally:
            self.is_loading = False



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
    provider_token: str = ""


    def start_edit_address(self, address_id: int, current_address: str):
        self.editing_address_id = address_id
        self.show_form = True  # reuse the form modal for editing
        self.new_address = current_address  # pre-fill with existing address
        print(f"Starting edit for address ID {address_id}: {current_address}")


    def toggle_form(self):
        """Toggle visibility of the address form."""
        self.show_form = True
        self.editing_address_id = 0  # Reset editing state
        self.new_address = ""  # Clear input field
        print("Opening address form.")

    def close_form(self):
        """Close the address form and clear input."""
        self.show_form = False
        self.new_address = ""
        self.editing_address_id = 0  # Reset editing state

    def set_new_address(self, value: str):
        """Update the new_address field."""
        self.new_address = value

    async def save_address(self):
        """Save address (add new or update existing)."""
        if self.editing_address_id == 0:
            # Adding new address
            await self.add_address()
        else:
            # Editing existing address
            await self.edit_address(self.editing_address_id, self.new_address)

    async def add_address(self):
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}

        if not self.new_address.strip():
            print("No address entered. Skipping.")
            return

        data = {"address": self.new_address.strip(), "is_default": False}
        print("Sending new address to backend:", data)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/users/address/add/",
                    data=data,
                    cookies=cookies_dict,
                )
            print("POST response status:", response.status_code)

            if response.status_code == 201:
                # Reload addresses
                await self.load_addresses()
                self.new_address = ""
                self.show_form = False
                self.editing_address_id = 0
                print("Address added successfully.")
            else:
                print("Error adding address:", response.text)
        except Exception as e:
            print("Request failed:", e)



    async def load_addresses(self):
        """Fetch existing addresses from backend when the page loads."""
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
                        address=addr.get("address", ""),
                        is_default=addr.get("is_default", False)
                    )
                    for addr in addresses_list
                ]
                print("Addresses loaded:", self.addresses)
            else:
                print("Failed to fetch addresses:", res.text)
        except Exception as e:
            print("Request failed:", e)



    async def delete_address(self, address_id: int):
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}

        # Make DELETE request
        async with httpx.AsyncClient() as client:
            response = await client.request(
                "DELETE",
                f"{API_BASE_URL}/users/address/delete/",
                data=json.dumps({"address_id": address_id}),
                headers={"Content-Type": "application/json"},
                cookies=cookies_dict,
            )

        if response.status_code == 200:
            # Update reactive list safely
            new_addresses = [addr for addr in self.addresses if addr.id != address_id]
            self.addresses = new_addresses
        else:
            print("Failed to delete address:", response.text)


    async def edit_address(self, address_id: int, new_address: str):
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}

        if not new_address.strip():
            print("No address entered. Skipping.")
            return

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    "PUT",
                    f"{API_BASE_URL}/users/address/edit/",
                    data=json.dumps({"address_id": address_id, "address": new_address.strip()}),
                    headers={"Content-Type": "application/json"},
                    cookies=cookies_dict,
                )

            if response.status_code == 200:
                # Reload addresses from backend
                await self.load_addresses()
                self.new_address = ""
                self.show_form = False
                self.editing_address_id = 0
                print("Address updated successfully.")
            else:
                print("Failed to edit address:", response.text)
        except Exception as e:
            print("Request failed:", e)



    async def set_default_address(self, address_id: int):
        """Set an address as the default address"""
        self.is_loading = True
        self.error_message = ""
        self.success_message = ""
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies or {}
        
        try:
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{API_BASE_URL}/users/address/set_default/",
                    json={"address_id": address_id},
                    headers={"Content-Type": "application/json"},
                    cookies=cookies_dict,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    self.success_message = "Default address updated successfully"
                    
                    updated_addresses = []
                    for addr in self.addresses:
                        addr_copy = addr.copy()
                        if addr_copy["id"] == address_id:
                            addr_copy["is_default"] = True
                        else:
                            addr_copy["is_default"] = False
                        updated_addresses.append(addr_copy)
                    
                    self.addresses = updated_addresses
                    
                elif response.status_code == 401:
                    self.error_message = "Authentication required"
                elif response.status_code == 403:
                    self.error_message = "Only customers can manage addresses"
                elif response.status_code == 404:
                    self.error_message = "Address not found"
                else:
                    data = response.json()
                    self.error_message = data.get("error", "Failed to set default address")
                    
        except httpx.TimeoutException:
            self.error_message = "Request timed out. Please try again."
        except httpx.RequestError as e:
            self.error_message = f"Connection error: {str(e)}"
        except Exception as e:
            self.error_message = f"An error occurred: {str(e)}"
        finally:
            self.is_loading = False



class ProfileState(rx.State):
 
    active_section: str = "profile"
    show_password_form: bool = False
    has_addresses: bool = False
    selected_menu: str = "personal_info"

    profile_picture: str = ""  
    is_uploading: bool = False
    upload_error: str = ""

    # Personal info
    first_name: str = ""
    last_name: str = ""
    username: str = ""
    email: str = ""
    phone_number: str = ""
    gender: str = ""
    birthday: str = ""
    province: str = ""
    street_address: str = ""

    # Password fields
    current_password: str = ""
    new_password: str = ""
    confirm_password: str = ""
    show_password_form: bool = False
    show_current_password: bool = False
    show_new_password: bool = False
    show_confirm_password: bool = False
    is_submitting: bool = False
    password_error: str = ""
    password_success: str = ""

    # Address management
    addresses: list[Address] = []
    editing_address_id: int = 0  # 0 means new address, >0 means editing
    form_username: str = ""
    form_phone_number: str = ""
    form_province: str = ""
    form_street_address: str = ""

    def set_form_username(self, value: str):
        self.form_username = value

    def set_form_province(self, value: str):
        self.form_province = value

    def set_form_street_address(self, value: str):
        self.form_street_address = value

    def set_form_phone_number(self, value: str):
        self.form_phone_number = value

    def set_first_name(self, value: str):
        self.first_name = value

    def set_last_name(self, value: str):
        self.last_name = value

    def set_username(self, value: str):
        self.username = value

    def set_email(self, value: str):
        self.email = value

    def set_phone_number(self, value: str):
        self.phone_number = value

    def set_gender(self, value: str):
        self.gender = value

    def set_birthday(self, value: str):
        self.birthday = value

    def set_current_password(self, value: str):
        self.current_password = value

    def set_new_password(self, value: str):
        self.new_password = value

    def set_confirm_password(self, value: str):
        self.confirm_password = value

    # Sections / menu handling
    def set_section(self, section: str):
        self.active_section = section

    def set_menu(self, menu: str):
        self.selected_menu = menu

    # Password form
    def open_password_form(self):
        self.show_password_form = True

    def close_password_form(self):
        self.show_password_form = False
        self.current_password = ""
        self.new_password = ""
        self.confirm_password = ""

    def toggle_current_password(self):
        self.show_current_password = not self.show_current_password

    def toggle_new_password(self):
        self.show_new_password = not self.show_new_password

    def toggle_confirm_password(self):
        self.show_confirm_password = not self.show_confirm_password

    # Your existing methods...
    def close_password_form(self):
        self.show_password_form = False

    def clear_password_fields(self):
        """Clear all password fields and messages"""
        self.current_password = ""
        self.new_password = ""
        self.confirm_password = ""
        self.password_error = ""
        self.password_success = ""
        self.show_current_password = False
        self.show_new_password = False
        self.show_confirm_password = False

    async def submit_password_change(self):
        """Submit password change request to backend"""
        print("=== PASSWORD CHANGE STARTED ===")

        # Set loading state
        self.is_submitting = True

        # Clear previous messages
        self.password_error = ""
        self.password_success = ""

        print(f"Current password length: {len(self.current_password)}")
        print(f"New password length: {len(self.new_password)}")
        print(f"Confirm password length: {len(self.confirm_password)}")

        # Validate inputs
        if not self.current_password:
            self.password_error = "Please enter your current password"
            self.is_submitting = False
            print(f"Validation error: {self.password_error}")
            return

        if not self.new_password:
            self.password_error = "Please enter a new password"
            self.is_submitting = False
            print(f"Validation error: {self.password_error}")
            return

        if len(self.new_password) < 6:
            self.password_error = "New password must be at least 6 characters"
            self.is_submitting = False
            print(f"Validation error: {self.password_error}")
            return

        if not self.confirm_password:
            self.password_error = "Please confirm your new password"
            self.is_submitting = False
            print(f"Validation error: {self.password_error}")
            return

        if self.new_password != self.confirm_password:
            self.password_error = "New passwords do not match"
            self.is_submitting = False
            print(f"Validation error: {self.password_error}")
            return

        if self.current_password == self.new_password:
            self.password_error = "New password must be different from current password"
            self.is_submitting = False
            print(f"Validation error: {self.password_error}")
            return

        print("Validation passed, getting auth state...")

        # Get auth state
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}

        print(f"Cookies available: {bool(cookies_dict)}")
        print(f"API URL: {API_BASE_URL}/users/change_password/")

        # Make API request
        try:
            async with httpx.AsyncClient() as client:
                print("Sending request to backend...")
                response = await client.put(
                    f"{API_BASE_URL}/users/change_password/",
                    json={
                        "current_password": self.current_password,
                        "new_password": self.new_password,
                    },
                    cookies=cookies_dict,
                    timeout=10.0,
                )

                print(f"Response status: {response.status_code}")
                print(f"Response body: {response.text}")

                if response.status_code == 200:
                    self.password_success = (
                        "Password changed successfully! Redirecting to login..."
                    )
                    print("Password changed successfully!")
                    self.clear_password_fields()
                    self.show_password_form = False
                    self.is_submitting = False

                    # Redirect to login page
                    return rx.redirect("/login")

                elif response.status_code == 403:
                    self.password_error = "Current password is incorrect"
                    print(f"Error: {self.password_error}")

                elif response.status_code == 400:
                    data = response.json()
                    self.password_error = data.get("error", "Invalid request")
                    print(f"Error: {self.password_error}")

                elif response.status_code == 401:
                    self.password_error = (
                        "Authentication required. Please log in again."
                    )
                    print(f"Error: {self.password_error}")
                    self.is_submitting = False
                    return rx.redirect("/login")

                else:
                    self.password_error = (
                        f"Server error (Status: {response.status_code})"
                    )
                    print(f"Error: {self.password_error}")

        except httpx.TimeoutException as e:
            self.password_error = "Request timeout. Please check your connection."
            print(f"Timeout error: {e}")
        except httpx.RequestError as e:
            self.password_error = "Network error. Please try again."
            print(f"Request error: {e}")
        except Exception as e:
            self.password_error = f"An unexpected error occurred: {str(e)}"
            print(f"Unexpected error: {e}")

        self.is_submitting = False
        print("=== PASSWORD CHANGE ENDED ===")
        print(f"Final error message: {self.password_error}")
        print(f"Final success message: {self.password_success}")

    async def save_profile(self):
        # Access AuthState instance to get the actual cookie value
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}

        # Prepare payload
        payload = {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "username": self.username,
            "email": self.email,
            "phone_no": self.phone_number,
            "gender": self.gender,
            "date_of_birth": self.birthday,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{API_BASE_URL}/users/profile/update/",
                    json=payload,
                    cookies=cookies_dict,
                    timeout=5.0,
                )

            if response.status_code == 200:
                data = response.json()
                print(f"Profile updated: {data}")
                # Reload user data
                await self.load_user_data()
            else:
                print(f"Failed to update profile: {response.text}")

        except Exception as e:
            print(f"Error updating profile: {str(e)}")

    async def load_user_data(self):
        """Fetch user profile from backend"""
        auth_state = await self.get_state(AuthState)

        if not auth_state.is_logged_in:
            return

        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/users/profile/", cookies=cookies_dict, timeout=5.0
                )
            if response.status_code == 200:
                data = response.json()
                user = data.get("user_profile", {})

                # DEBUG: Print the entire user object
                print("=== USER DATA ===")
                print(f"Full user object: {user}")
                print(f"Profile pic raw: {user.get('profilePic', 'NOT FOUND')}")
                print(f"All keys: {user.keys()}")

                self.first_name = user.get("first_name", "")
                self.last_name = user.get("last_name", "")
                self.username = user.get("username", "")
                self.email = user.get("email", "")
                self.phone_number = user.get("phone_no", "")
                self.gender = user.get("gender", "")
                self.birthday = user.get("date_of_birth", "")

                profile_pic = user.get("profilePic", "")
                if profile_pic:
                    # Check if it already has the data URI prefix
                    if profile_pic.startswith("data:image"):
                        self.profile_picture = profile_pic
                    else:
                        self.profile_picture = f"data:image/png;base64,{profile_pic}"
                    print(
                        f"Profile picture set to: {self.profile_picture[:100]}..."
                    )  # Print first 100 chars
                else:
                    self.profile_picture = ""
                    print("Profile picture is empty")

        except Exception as e:
            print(f"Error loading user data: {str(e)}")

    async def handle_upload(self, files: Any):
        """Handle file upload from Reflex upload component"""
        print(f"=== UPLOAD DEBUG ===")
        print(f"Files received: {files}")
        print(f"Files type: {type(files)}")

        if not files:
            self.upload_error = "No file selected"
            return

        try:
            self.is_uploading = True
            self.upload_error = ""

            # Get the first file
            upload_file = files[0] if isinstance(files, list) else files

            print(f"Upload file: {upload_file}")
            print(f"Upload file type: {type(upload_file)}")
            print(f"Upload file dir: {dir(upload_file)}")

            # Check various possible formats
            if hasattr(upload_file, "read"):
                # It's an UploadFile object with read method
                print("Has read method - treating as UploadFile")
                file_content = await upload_file.read()
                filename = getattr(upload_file, "filename", "profile.png")
                content_type = getattr(upload_file, "type", "image/png")
            elif isinstance(upload_file, str):
                # It's a file path string
                print(f"File path received: {upload_file}")
                with open(upload_file, "rb") as f:
                    file_content = f.read()
                filename = os.path.basename(upload_file)
                ext = filename.split(".")[-1].lower()
                content_type = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
            elif isinstance(upload_file, bytes):
                # It's raw bytes
                print("Raw bytes received")
                file_content = upload_file
                filename = "profile.png"
                content_type = "image/png"
            else:
                # Unknown format
                print(f"Unknown format: {type(upload_file)}")
                self.upload_error = f"Unexpected file format: {type(upload_file)}"
                self.is_uploading = False
                return

            # Validate file type
            if content_type not in ["image/png", "image/jpeg", "image/jpg"]:
                self.upload_error = "Invalid file type. Only PNG and JPEG are allowed."
                self.is_uploading = False
                return

            # Validate file size (5MB limit)
            if len(file_content) > 5 * 1024 * 1024:
                self.upload_error = "Profile picture exceeds size limit of 5MB"
                self.is_uploading = False
                return

            # Upload to backend
            await self.upload_profile_picture_with_content(
                file_content, filename, content_type
            )

        except Exception as e:
            self.upload_error = f"Error handling upload: {str(e)}"
            print(f"Error in handle_upload: {str(e)}")
            import traceback

            traceback.print_exc()
            self.is_uploading = False

    async def upload_profile_picture_with_content(
        self, file_content: bytes, filename: str, content_type: str
    ):
        """Upload profile picture to backend with file content"""
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}

        try:
            # Create form data with the file content
            files_data = {"profile_picture": (filename, file_content, content_type)}

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/users/profile/upload_profile_picture/",
                    files=files_data,
                    cookies=cookies_dict,
                    timeout=10.0,
                )

            if response.status_code == 200:
                print("Profile picture uploaded successfully")
                # Reload user data to get new profile picture
                await self.load_user_data()
                self.upload_error = ""
            else:
                error_msg = (
                    response.json().get("error", "Unknown error")
                    if response.text
                    else "Unknown error"
                )
                self.upload_error = f"Failed to upload: {error_msg}"
                print(f"Upload failed: {response.text}")

        except Exception as e:
            self.upload_error = f"Error uploading profile picture: {str(e)}"
            print(f"Error uploading profile picture: {str(e)}")
        finally:
            self.is_uploading = False


class PaymentState(rx.State):
    show_card_form: bool = False
    show_bank_form: bool = False

    # User input fields for credit card (what user enters)
    card_number: str = ""
    card_holder_name: str = ""
    cvv: str = ""
    exp_month: str = ""
    exp_year: str = ""
    is_default: bool = False

    # For backend (processed data)
    provider: str = "stripe"
    provider_token: str = ""
    card_brand: str = ""
    last4: str = ""

    # Form fields for bank account
    bank_provider: str = "scb"
    bank_name: str = ""
    account_holder: str = ""
    bank_last4: str = ""
    bank_provider_token: str = ""
    bank_is_default: bool = False
    
    # UI state
    error_message: str = ""
    success_message: str = ""
    credit_cards: list = []

    # Setters for card form
    def set_card_number(self, value: str):
        self.card_number = value
    
    def set_card_holder_name(self, value: str):
        self.card_holder_name = value
    
    def set_cvv(self, value: str):
        self.cvv = value
    
    def set_exp_month(self, value: str):
        self.exp_month = value
    
    def set_exp_year(self, value: str):
        self.exp_year = value

    def set_is_default(self, checked: bool):
        self.is_default = checked


    def toggle_card_form(self):
        self.show_card_form = True
        self.error_message = ""
        self.success_message = ""

    def set_bank_provider(self, value: str):
        self.bank_provider = value

    def close_card_form(self):
        self.show_card_form = False
        self.clear_card_form()

    def toggle_bank_form(self):
        self.show_bank_form = True
        self.show_card_form = False

    def close_bank_form(self):
        self.show_bank_form = False
    
    def clear_card_form(self):
        """Clear all card form fields"""
        self.card_number = ""
        self.card_holder_name = ""
        self.cvv = ""
        self.exp_month = ""
        self.exp_year = ""
        self.is_default = False
        self.error_message = ""
        self.success_message = ""

    def generate_mock_token(self) -> str:
        """Generate a mock provider token like 'pm_xxx'."""
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=24))
        return f"pm_{random_str}"
    
    def detect_card_brand(self, card_number: str) -> str:
        """Detect card brand from card number (simplified logic)."""
        clean_number = card_number.replace(" ", "")
        
        if not clean_number:
            return "Unknown"
        
        first_digit = clean_number[0] if len(clean_number) >= 1 else ""
        first_two = clean_number[:2] if len(clean_number) >= 2 else ""
        
        if first_digit == "4":
            return "Visa"
        elif first_two in ["51", "52", "53", "54", "55"]:
            return "Mastercard"
        elif first_two in ["34", "37"]:
            return "American Express"
        elif first_two in ["60", "65"]:
            return "Discover"
        elif first_two in ["35"]:
            return "JCB"
        else:
            return "Visa"
    
    def get_last4(self, card_number: str) -> str:
        """Extract last 4 digits from card number."""
        clean_number = card_number.replace(" ", "")
        return clean_number[-4:] if len(clean_number) >= 4 else "0000"
    
    def validate_card_input(self) -> bool:
        """Validate user input before submission."""
        clean_number = self.card_number.replace(" ", "")
        
        if not clean_number.isdigit() or len(clean_number) < 13 or len(clean_number) > 19:
            self.error_message = "Please enter a valid card number (13-19 digits)"
            return False
        
        if not self.exp_month or not self.exp_month.isdigit():
            self.error_message = "Please enter a valid expiration month"
            return False
        
        month = int(self.exp_month)
        if month < 1 or month > 12:
            self.error_message = "Expiration month must be between 1 and 12"
            return False
        
        if not self.exp_year or not self.exp_year.isdigit():
            self.error_message = "Please enter a valid expiration year"
            return False
        
        year = int(self.exp_year)
        if year < 2024 or year > 2050:
            self.error_message = "Please enter a valid expiration year"
            return False
        
        if not self.cvv or not self.cvv.isdigit() or len(self.cvv) < 3 or len(self.cvv) > 4:
            self.error_message = "Please enter a valid CVV (3-4 digits)"
            return False
        
        if not self.card_holder_name or len(self.card_holder_name.strip()) < 3:
            self.error_message = "Please enter the cardholder name"
            return False
        
        self.error_message = ""
        return True
 
    def set_bank_name(self, value: str):
        self.bank_name = value

    def set_account_holder(self, value: str):
        self.account_holder = value

    def set_bank_last4(self, value: str):
        self.bank_last4 = value

    def set_bank_provider_token(self, value: str):
        self.bank_provider_token = value

    def set_bank_is_default(self, checked: bool):
        self.bank_is_default = checked
    
    def clear_bank_form(self):
        """Clear all bank form fields"""
        self.bank_provider = "scb"
        self.bank_name = ""
        self.account_holder = ""
        self.bank_last4 = ""
        self.bank_provider_token = ""
        self.bank_is_default = False
        self.error_message = ""
        self.success_message = ""
    
    def validate_bank_input(self) -> bool:
        """Validate bank account input before submission."""
        if not self.bank_name or len(self.bank_name.strip()) < 2:
            self.error_message = "Please enter a valid bank name"
            return False
        
        if not self.account_holder or len(self.account_holder.strip()) < 3:
            self.error_message = "Please enter the account holder name"
            return False
        
        if not self.bank_last4 or not self.bank_last4.isdigit() or len(self.bank_last4) != 4:
            self.error_message = "Please enter the last 4 digits of account number"
            return False
        
        self.error_message = ""
        return True
    
    def generate_bank_token(self) -> str:
        """Generate a mock bank account token like 'ba_xxx'."""
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=24))
        return f"ba_{random_str}"

    async def submit_bank(self):
        """Add a new bank account with mock data."""
        # Validate input
        if not self.validate_bank_input():
            return
        
        # Generate mock provider token if not provided
        if not self.bank_provider_token:
            self.bank_provider_token = self.generate_bank_token()
        
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}
        
        print(f"=== SUBMIT BANK ACCOUNT DEBUG ===")
        print(f"Cookies: {cookies_dict}")
        print(f"API URL: {API_BASE_URL}/users/payment_methods/add_bank_account/")
        
        try:
            async with httpx.AsyncClient() as client:
                # Prepare the form data
                form_data = {
                    "provider": self.bank_provider,
                    "provider_token": self.bank_provider_token,
                    "bank_name": self.bank_name.strip(),
                    "account_holder": self.account_holder.strip(),
                    "last4": self.bank_last4,
                    "is_default": str(self.bank_is_default).lower()
                }
                
                print("Sending bank account data:", form_data)
                
                res = await client.post(
                    f"{API_BASE_URL}/users/payment_methods/add_bank_account/",
                    data=form_data,
                    cookies=cookies_dict,
                    timeout=10.0
                )
                
                print(f"Response status code: {res.status_code}")
                print(f"Response text: '{res.text}'")
                print(f"Response length: {len(res.text)}")
                
                if res.status_code == 201:
                    try:
                        response_data = res.json()
                        print("Bank account added successfully:", response_data)
                    except Exception as json_err:
                        print(f"JSON parse error on success: {json_err}")
                        print("Bank account might have been added despite JSON error")
                    
                    self.success_message = "Bank account added successfully!"
                    self.error_message = ""
                    self.clear_bank_form()
                    self.show_bank_form = False

                    await self.load_bank_accounts() 
                    return rx.toast.success("🏦 Bank account added successfully!")
                    
                elif res.status_code == 302 or res.status_code == 301:
                    print("REDIRECT DETECTED - Authentication issue")
                    self.error_message = "Authentication error. Please log in again."
                    
                elif res.status_code == 403:
                    print("FORBIDDEN - CSRF or permission issue")
                    self.error_message = "Permission denied. Please check authentication."
                    
                elif res.status_code == 404:
                    print("NOT FOUND - Check your endpoint URL")
                    self.error_message = "API endpoint not found. Check URL configuration."
                    
                elif res.status_code == 400:
                    try:
                        error_data = res.json()
                        self.error_message = error_data.get("error", "Invalid data provided")
                    except:
                        self.error_message = "Invalid data provided"
                    print(f"Bad request: {self.error_message}")
                    
                else:
                    try:
                        error_data = res.json()
                        self.error_message = error_data.get("error", f"Error: {res.status_code}")
                    except Exception as json_err:
                        print(f"JSON parse error: {json_err}")
                        self.error_message = f"Server error: {res.status_code} - {res.text[:200]}"
                    
                    self.success_message = ""
                    
        except httpx.TimeoutException:
            self.error_message = "Request timed out. Please try again."
            print("Request timeout")
        except httpx.RequestError as e:
            self.error_message = "Network error. Please check your connection."
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Unexpected error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            self.error_message = "Failed to add bank account. Please try again."
            self.success_message = ""
    
    async def submit_card(self):
        """Add a new credit card with mock data."""
        # Validate input
        if not self.validate_card_input():
            return
        
        # Detect card brand and get last 4 digits
        self.card_brand = self.detect_card_brand(self.card_number)
        self.last4 = self.get_last4(self.card_number)
        
        # Generate mock provider token
        self.provider_token = self.generate_mock_token()
        
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}
        
        print(f"=== SUBMIT CARD DEBUG ===")
        print(f"Cookies: {cookies_dict}")
        print(f"API URL: {API_BASE_URL}/users/credit-card/")
        
        try:
            async with httpx.AsyncClient() as client:
                # Prepare the form data with mock provider info
                form_data = {
                    "provider": self.provider,
                    "provider_token": self.provider_token,
                    "card_brand": self.card_brand,
                    "last4": self.last4,
                    "exp_month": self.exp_month,
                    "exp_year": self.exp_year,
                    "is_default": str(self.is_default).lower()
                }
                
                print("Sending mock payment data:", form_data)
                
                res = await client.post(
                    f"{API_BASE_URL}/users/payment_methods/add_credit_card/",
                    data=form_data,
                    cookies=cookies_dict,
                    timeout=10.0
                )
                
                print(f"Response status code: {res.status_code}")
                print(f"Response headers: {res.headers}")
                print(f"Response text: '{res.text}'")
                print(f"Response length: {len(res.text)}")
                
                if res.status_code == 201:
                    try:
                        response_data = res.json()
                        print("Credit card added successfully:", response_data)
                    except Exception as json_err:
                        print(f"JSON parse error on success: {json_err}")
                        print("Card might have been added despite JSON error")
                    
                    self.success_message = "Card added successfully!"
                    self.error_message = ""
                    self.clear_card_form()
                    self.show_card_form = False

                    await self.load_credit_cards()
                    
                    return rx.toast.success("✅ Credit card added successfully!")
                    
                elif res.status_code == 302 or res.status_code == 301:
                    print("REDIRECT DETECTED - Authentication issue")
                    self.error_message = "Authentication error. Please log in again."
                    
                elif res.status_code == 403:
                    print("FORBIDDEN - CSRF or permission issue")
                    self.error_message = "Permission denied. Please check authentication."
                    
                elif res.status_code == 404:
                    print("NOT FOUND - Check your endpoint URL")
                    self.error_message = "API endpoint not found. Check URL configuration."
                    
                else:
                    try:
                        error_data = res.json()
                        self.error_message = error_data.get("error", f"Error: {res.status_code}")
                    except Exception as json_err:
                        print(f"JSON parse error: {json_err}")
                        self.error_message = f"Server error: {res.status_code} - {res.text[:200]}"
                    
                    self.success_message = ""
                    
        except httpx.TimeoutException:
            self.error_message = "Request timed out. Please try again."
            print("Request timeout")
        except httpx.RequestError as e:
            self.error_message = "Network error. Please check your connection."
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Unexpected error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            self.error_message = "Failed to add card. Please try again."
            self.success_message = ""

    credit_cards: list[CreditCard] = []
    bank_accounts: list[BankAccount] = []
    is_loading_payments: bool = False
    
    async def load_payment_methods(self):
        """Load all payment methods (credit cards and bank accounts)."""
        self.is_loading_payments = True
        await self.load_credit_cards()
        await self.load_bank_accounts()
        self.is_loading_payments = False 
    
    async def load_credit_cards(self):
        """Fetch all credit cards from backend."""
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(
                    f"{API_BASE_URL}/users/payment_methods/",  # ✅ Correct endpoint
                    cookies=cookies_dict,
                    timeout=10.0
                )
            
            if res.status_code == 200:
                data = res.json()
                cards_data = data.get("payment_methods", [])  # ✅ Changed from "credit_cards" to "payment_methods"
                # Convert to typed objects
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
                # Convert to typed objects
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
    
    async def delete_credit_card(self, card_id: int):
        """Delete a credit card."""
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.delete(
                    f"{API_BASE_URL}/users/payment_methods/remove_credit_card/{card_id}/",  # ✅ Add trailing slash
                    cookies=cookies_dict,
                    timeout=10.0
                    # ✅ REMOVE json={"card_id": card_id} - not needed since ID is in URL
                )
            
            if res.status_code == 200:
                print(f"Credit card {card_id} deleted successfully")
                await self.load_credit_cards()
                return rx.toast.success("Credit card deleted successfully!")
            else:
                print(f"Failed to delete credit card: {res.status_code}")
                print(f"Response: {res.text}")  # ✅ Add this for debugging
                return rx.toast.error("Failed to delete credit card")
                
        except Exception as e:
            print(f"Error deleting credit card: {e}")
            import traceback
            traceback.print_exc()  # ✅ Add full traceback
            return rx.toast.error("Error deleting credit card")

    async def delete_bank_account(self, account_id: int):
        """Delete a bank account."""
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.delete(
                    f"{API_BASE_URL}/users/payment_methods/remove_bank_account/{account_id}/",  # ✅ Add trailing slash
                    cookies=cookies_dict,
                    timeout=10.0
                    # ✅ REMOVE json={"account_id": account_id} - not needed since ID is in URL
                )
            
            if res.status_code == 200:
                print(f"Bank account {account_id} deleted successfully")
                await self.load_bank_accounts()
                return rx.toast.success("Bank account deleted successfully!")
            else:
                print(f"Failed to delete bank account: {res.status_code}")
                print(f"Response: {res.text}")  # ✅ Add this for debugging
                return rx.toast.error("Failed to delete bank account")
                
        except Exception as e:
            print(f"Error deleting bank account: {e}")
            import traceback
            traceback.print_exc()  # ✅ Add full traceback
            return rx.toast.error("Error deleting bank account")
    
    async def set_default_card(self, card_id: int):
        """Set a credit card as default."""
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.put(
                    f"{API_BASE_URL}/users/payment_methods/set_default_credit_card/",
                    json={"card_id": card_id},
                    cookies=cookies_dict,
                    timeout=10.0
                )
            
            if res.status_code == 200:
                await self.load_credit_cards()
                return rx.toast.success("Default card updated!")
            else:
                return rx.toast.error("Failed to update default card")
                
        except Exception as e:
            print(f"Error setting default card: {e}")
            return rx.toast.error("Error updating default card")
    
    async def set_default_bank(self, account_id: int):
        """Set a bank account as default."""
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.put(
                    f"{API_BASE_URL}/users/payment_methods/set_default_bank_account/",
                    json={"account_id": account_id},
                    cookies=cookies_dict,
                    timeout=10.0
                )
            
            if res.status_code == 200:
                await self.load_bank_accounts()
                return rx.toast.success("Default bank account updated!")
            else:
                return rx.toast.error("Failed to update default bank account")
                
        except Exception as e:
            print(f"Error setting default bank: {e}")
            return rx.toast.error("Error updating default bank account")

class Review(rx.Base):
    id: int = 0
    product_id: int = 0
    rating: int = 0
    comment: str = ""
    image: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


class ReviewState(rx.State):
    reviews: list[Review] = []
    is_loading: bool = False
    error_message: str = ""
    success_message: str = ""
    
    # Form states
    show_edit_form: bool = False
    
    # Form fields
    product_id: str = ""
    rating: str = "5"
    comment: str = ""
    review_image: Optional[str] = None
    editing_review_id: int = 0
    
    # Image upload
    is_uploading_image: bool = False
    upload_image_error: str = ""

    def set_rating(self, value: str):
        self.rating = value

    def set_comment(self, value: str):
        self.comment = value

    def open_edit_form(self, review: Review):
        self.show_edit_form = True
        self.editing_review_id = review.id
        self.product_id = str(review.product_id)
        self.rating = str(review.rating)
        self.comment = review.comment
        self.review_image = review.image

    def close_form(self):
        self.show_edit_form = False
        self.clear_form()

    def clear_form(self):
        self.product_id = ""
        self.rating = "5"
        self.comment = ""
        self.review_image = None
        self.editing_review_id = 0
        self.error_message = ""
        self.success_message = ""
        self.upload_image_error = ""

    async def load_reviews(self):
        """Fetch all reviews for the current customer."""
        self.is_loading = True
        self.error_message = ""
        
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{API_BASE_URL}/reviews/get_customer_reviews/",
                    cookies=cookies_dict,
                    timeout=10.0
                )

            if response.status_code == 200:
                data = response.json()
                reviews_data = data.get("reviews", [])
                self.reviews = [
                    Review(
                        id=review.get("id", 0),
                        product_id=review.get("product_id", 0),
                        rating=review.get("rating", 0),
                        comment=review.get("comment", ""),
                        image=review.get("image"),
                        created_at=review.get("created_at", ""),
                        updated_at=review.get("updated_at", "")
                    )
                    for review in reviews_data
                ]
                print(f"Loaded {len(self.reviews)} reviews")
            elif response.status_code == 403:
                self.error_message = "Only customers can view reviews"
            else:
                self.error_message = "Failed to load reviews"
                
        except Exception as e:
            self.error_message = f"Error loading reviews: {str(e)}"
            print(f"Error loading reviews: {e}")
        finally:
            self.is_loading = False

    async def handle_image_upload(self, files):
        """Handle image upload for review."""
        if not files:
            return

        try:
            self.is_uploading_image = True
            self.upload_image_error = ""

            upload_file = files[0] if isinstance(files, list) else files

            if hasattr(upload_file, "read"):
                file_content = await upload_file.read()
                filename = getattr(upload_file, "filename", "review.png")
                content_type = getattr(upload_file, "type", "image/png")
            elif isinstance(upload_file, str):
                with open(upload_file, "rb") as f:
                    file_content = f.read()
                filename = upload_file.split("/")[-1]
                ext = filename.split(".")[-1].lower()
                content_type = "image/jpeg" if ext in ["jpg", "jpeg"] else "image/png"
            else:
                self.upload_image_error = "Unsupported file format"
                return

            if content_type not in ["image/png", "image/jpeg", "image/jpg"]:
                self.upload_image_error = "Only PNG and JPEG images are allowed"
                return

            if len(file_content) > 5 * 1024 * 1024:
                self.upload_image_error = "Image size must be less than 5MB"
                return

            self.review_image = base64.b64encode(file_content).decode('utf-8')

        except Exception as e:
            self.upload_image_error = f"Error uploading image: {str(e)}"
            print(f"Error in handle_image_upload: {e}")
        finally:
            self.is_uploading_image = False

    def remove_image(self):
        """Remove the uploaded image."""
        self.review_image = None

    async def edit_review(self):
        """Edit an existing review."""
        self.error_message = ""
        self.success_message = ""

        if not self.editing_review_id:
            self.error_message = "Review ID is required"
            return

        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}

        try:
            
            form_data = {
                "review_id": str(self.editing_review_id),
                "rating": self.rating,
                "comment": self.comment
            }

            # Prepare files if image exists
            files = None
            if self.review_image:
                # Decode base64 and prepare for upload
                image_bytes = base64.b64decode(self.review_image)
                files = {"image": ("review.jpg", image_bytes, "image/jpeg")}
            else:
                # Send empty image to remove it
                form_data["image"] = ""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{API_BASE_URL}/reviews/edit/",
                    data=form_data,
                    files=files,
                    cookies=cookies_dict,
                    timeout=10.0
                )

            if response.status_code == 200:
                self.success_message = "Review updated successfully!"
                await self.load_reviews()
                self.close_form()
                return rx.toast.success("Review updated successfully!")
            elif response.status_code == 400:
                data = response.json()
                self.error_message = data.get("error", "Invalid request")
            elif response.status_code == 403:
                self.error_message = "Only customers can edit reviews"
            elif response.status_code == 404:
                self.error_message = "Review not found"
            else:
                self.error_message = f"Failed to update review: {response.status_code}"

        except Exception as e:
            self.error_message = f"Error updating review: {str(e)}"
            print(f"Error updating review: {e}")

    async def delete_review(self, review_id: int):
        """Delete a review."""
        auth_state = await self.get_state(AuthState)
        cookies_dict = auth_state.session_cookies if auth_state.session_cookies else {}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{API_BASE_URL}/reviews/delete/{review_id}/",
                    cookies=cookies_dict,
                    timeout=10.0
                )

            if response.status_code == 200:
                await self.load_reviews()
                return rx.toast.success("Review deleted successfully!")
            elif response.status_code == 403:
                return rx.toast.error("Only customers can delete reviews")
            elif response.status_code == 404:
                return rx.toast.error("Review not found")
            else:
                return rx.toast.error("Failed to delete review")

        except Exception as e:
            print(f"Error deleting review: {e}")
            return rx.toast.error("Error deleting review")




def profile_avatar_section() -> rx.Component:
    """Profile avatar with upload functionality"""
    return rx.vstack(
        rx.center(
            rx.cond(
                ProfileState.profile_picture != "",
                rx.image(
                    src=ProfileState.profile_picture,
                    width="120px",
                    height="120px",
                    border_radius="full",
                    object_fit="cover",
                    border="4px solid #E5E7EB",
                ),
                rx.avatar(
                    fallback=rx.cond(
                        ProfileState.username != "",
                        ProfileState.username[0:2].upper(),
                        "U",
                    ),
                    size="8",
                    radius="full",
                    color_scheme="blue",
                ),
            ),
            width="100%",
            padding="20px 0px",
        ),
     
        rx.upload(
            rx.button(
                rx.icon("camera", size=16),
                "Change Photo",
                size="1",
                variant="soft",
                cursor="pointer",
            ),
            id="profile_picture_upload",
            accept={
                "image/png": [".png"],
                "image/jpeg": [".jpg", ".jpeg"],
            },
            max_files=1,
            on_drop=ProfileState.handle_upload,
        ),
        
        rx.center(
            rx.text(
                rx.cond(ProfileState.username != "", ProfileState.username, "User"),
                font_size="18px",
                font_weight="bold",
                color="#22282C",
            ),
            width="100%",
        ),
     
        rx.cond(
            ProfileState.is_uploading,
            rx.center(
                rx.spinner(size="2"),
                rx.text("Uploading...", font_size="12px", color="#6B7280"),
                spacing="2",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            ProfileState.upload_error != "",
            rx.center(
                rx.text(
                    ProfileState.upload_error,
                    font_size="12px",
                    color="#EF4444",
                    text_align="center",
                ),
                width="100%",
                padding="0 10px",
            ),
            rx.fragment(),
        ),
        spacing="3",
        width="100%",
    )


def profile_content() -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.vstack(
                profile_avatar_section(),
                rx.vstack(
                    nav_button("Personal Information", "profile"),
                    nav_button("My Address", "address"),
                    nav_button("My Payment Medthods", "card"),
                    nav_button("Wishlist", "wishlist"),
                    #nav_button("My Orders", "orders"),
                    nav_button("My Reviews", "reviews"),
                    nav_button("Notification", "notification"),
                    rx.link("Logout", href="/logout", style=menu_item_style(False)),
                    spacing="3",
                    
                ),
            ),
            width="280px",
            height="100%",
            background= "#E4EEF6"
           
        ),
        rx.box(
            rx.match(
                ProfileState.active_section,
                ("profile", profile_info_content()),
                ("address", address_content()),
                ("card", card_content() ),
                ("wishlist", wishlist_content()),
                #("orders", orders_content()),
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
        height="100%",
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
        color="#22282c",
        background = "#E4EEF6"
    )


def profile_info_content() -> rx.Component:
    return rx.vstack(
        rx.center(
            rx.text(
                "Personal Information",
                font_size="20px",
                font_weight="bold",
                margin_bottom="20px",
                color="#22282c",
            ),
            width="100%",
        ),
        rx.hstack(
            input_with_label(
                "First Name",
                value=ProfileState.first_name,
                on_change=ProfileState.set_first_name,
            ),
            input_with_label(
                "Last Name",
                value=ProfileState.last_name,
                on_change=ProfileState.set_last_name,
            ),
            spacing="4",
            width="100%",
        ),
        input_with_label(
            "Username", ProfileState.username, on_change=ProfileState.set_username
        ),
        input_with_label(
            "E-mail", ProfileState.email, on_change=ProfileState.set_email
        ),
        input_with_label(
            "Mobile No.",
            ProfileState.phone_number,
            on_change=ProfileState.set_phone_number,
        ),
        rx.hstack(
            select_with_label(
                "Gender (Optional)",
                ["Male", "Female", "Other"],
                value=ProfileState.gender,
                on_change=ProfileState.set_gender,
            ),
            input_with_label_date(
                "Birthday (Optional)",
                ProfileState.birthday,
                on_change=ProfileState.set_birthday,
            ),
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
            cursor="pointer",
            on_click=ProfileState.save_profile,
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
                    # Current Password Field
                    rx.vstack(
                        rx.text(
                            "Current Password",
                            font_size="16px",
                            font_weight="600",
                            color="#22282C",
                        ),
                        rx.box(
                            rx.input(
                                type=rx.cond(
                                    ProfileState.show_current_password,
                                    "text",
                                    "password",
                                ),
                                placeholder="Enter a password ( at least 6 characters )",
                                value=ProfileState.current_password,
                                on_change=ProfileState.set_current_password,
                                width="100%",
                                padding="5px",
                                border="1px solid #D1D5DB",
                                border_radius="12px",
                                font_size="16px",
                                color="#22282C",
                                name="current_password",
                                id="current_password",
                                background_color="#ffffff",
                            ),
                            rx.icon(
                                tag=rx.cond(
                                    ProfileState.show_current_password, "eye-off", "eye"
                                ),
                                size=24,
                                color="#9CA3AF",
                                position="absolute",
                                right="18px",
                                top="50%",
                                transform="translateY(-50%)",
                                cursor="pointer",
                                on_click=ProfileState.toggle_current_password,
                                _hover={"color": "#6B7280"},
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
                    # New Password Field
                    rx.vstack(
                        rx.text(
                            "New Password",
                            font_size="16px",
                            font_weight="600",
                            color="#22282C",
                        ),
                        rx.box(
                            rx.input(
                                type=rx.cond(
                                    ProfileState.show_new_password, "text", "password"
                                ),
                                placeholder="Enter a password ( at least 6 characters )",
                                value=ProfileState.new_password,
                                on_change=ProfileState.set_new_password,
                                width="100%",
                                padding="5px",
                                border="1px solid #D1D5DB",
                                border_radius="12px",
                                font_size="16px",
                                color="#22282C",
                                name="new_password",
                                id="new_password",
                                background_color="#ffffff",
                            ),
                            rx.icon(
                                tag=rx.cond(
                                    ProfileState.show_new_password, "eye-off", "eye"
                                ),
                                size=24,
                                color="#9CA3AF",
                                position="absolute",
                                right="18px",
                                top="50%",
                                transform="translateY(-50%)",
                                cursor="pointer",
                                on_click=ProfileState.toggle_new_password,
                                _hover={"color": "#6B7280"},
                            ),
                            position="relative",
                            width="100%",
                        ),
                        spacing="2",
                        width="100%",
                        align_items="flex-start",
                    ),
                    # Confirm Password Field
                    rx.vstack(
                        rx.text(
                            "Confirm New Password",
                            font_size="16px",
                            font_weight="600",
                            color="#22282C",
                        ),
                        rx.box(
                            rx.input(
                                type=rx.cond(
                                    ProfileState.show_confirm_password,
                                    "text",
                                    "password",
                                ),
                                placeholder="Enter a password ( at least 6 characters )",
                                value=ProfileState.confirm_password,
                                on_change=ProfileState.set_confirm_password,
                                width="100%",
                                padding="5px",
                                border="1px solid #D1D5DB",
                                border_radius="12px",
                                font_size="16px",
                                color="#22282C",
                                name="confirm_new_password",
                                id="confirm_new_password",
                                background_color="#ffffff",
                            ),
                            rx.icon(
                                tag=rx.cond(
                                    ProfileState.show_confirm_password, "eye-off", "eye"
                                ),
                                size=24,
                                color="#9CA3AF",
                                position="absolute",
                                right="18px",
                                top="50%",
                                transform="translateY(-50%)",
                                cursor="pointer",
                                on_click=ProfileState.toggle_confirm_password,
                                _hover={"color": "#6B7280"},
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
                        padding="25px",
                        font_size="18px",
                        font_weight="600",
                        cursor="pointer",
                        margin_top="20px",
                        border="none",
                        _hover={"opacity": "0.9"},
                        margin_bottom="20px",
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
    )


import json


class Address(rx.Base):
    id: int
    address: str
    is_default: bool = False

def new_address_modal() -> rx.Component:
    return rx.cond(
        AddressState.show_form,
        rx.box(
            rx.box(
                rx.vstack(
                    # Close button
                    rx.box(
                        rx.icon(
                            tag="x",
                            size=28,
                            color="#6B7280",
                            cursor="pointer",
                            on_click=AddressState.close_form,
                            _hover={"color": "#22282C"},
                        ),
                        width="100%",
                        display="flex",
                        justify_content="flex-end",
                    ),
                    # Modal Title (changes based on mode)
                    rx.center(
                        rx.cond(
                            AddressState.editing_address_id == 0,
                            rx.text(
                                "Add New Address",
                                font_size="24px",
                                font_weight="bold",
                                color="#22282C",
                            ),
                            rx.text(
                                "Edit Address",
                                font_size="24px",
                                font_weight="bold",
                                color="#22282C",
                            ),
                        ),
                        width="100%",
                    ),
                    rx.cond(
                        AddressState.editing_address_id == 0,
                        rx.text(
                            "Please enter your new address",
                            font_size="16px",
                            color="#22282C",
                        ),
                        rx.text(
                            "Update your address",
                            font_size="16px",
                            color="#22282C",
                        ),
                    ),
                    # Address Input Field
                    rx.vstack(
                        rx.input(
                            placeholder="Enter your address...",
                            value=AddressState.new_address,
                            on_change=AddressState.set_new_address,
                            width="100%",
                            padding="5px",
                            border="1px solid #D1D5DB",
                            border_radius="12px",
                            font_size="16px",
                            background_color="#ffffff",
                            color="#22282C",
                        ),
                        spacing="2",
                        width="100%",
                        align_items="flex-start",
                    ),
                    # Submit Button (text changes based on mode)
                    rx.button(
                        rx.cond(
                            AddressState.editing_address_id == 0,
                            "Save Address",
                            "Update Address",
                        ),
                        on_click=AddressState.save_address,
                        width="100%",
                        bg="#2E6FF2",
                        color="white",
                        border_radius="12px",
                        padding="15px",
                        font_size="16px",
                        font_weight="600",
                        cursor="pointer",
                        _hover={"opacity": "0.9"},
                        margin_top="20px",
                    ),
                    spacing="4",
                    width="100%",
                ),
                bg="white",
                padding="20px 40px",
                border_radius="20px",
                width="500px",
                max_width="90vw",
                box_shadow="0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)",
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
    )

def address_card(address: dict):
    return rx.box(
        rx.vstack(
            # Row 1: Name + Edit/Delete buttons
            rx.hstack(
                rx.text(
                    f"{ProfileState.first_name} {ProfileState.last_name}",
                    font_weight="bold",
                    color="#22282C",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.icon(
                        "pencil",
                        size=18,
                        color="#2E6FF2",
                        cursor="pointer",
                        on_click=lambda: AddressState.start_edit_address(
                            address["id"], address["address"]
                        ),
                    ),
                    rx.text(
                        "Edit",
                        font_weight="semibold",
                        color="#2E6FF2",
                        cursor="pointer",
                        on_click=lambda: AddressState.start_edit_address(
                            address["id"], address["address"]
                        ),
                    ),
                    rx.icon(
                        "trash",
                        size=18,
                        color="#FF4D4D",
                        cursor="pointer",
                        on_click=lambda: AddressState.delete_address(address["id"]),
                    ),
                    rx.text(
                        "Delete",
                        font_weight="semibold",
                        color="#FF4D4D",
                        cursor="pointer",
                        on_click=lambda: AddressState.delete_address(address["id"]),
                    ),
                    spacing="3",
                    align="center",
                ),
                align="center",
                width="100%",
            ),

  
            # Row 2: Phone number
            rx.text(ProfileState.phone_number, color="#555", mt="5px"),

            rx.hstack(
              
                rx.hstack(
                    rx.icon("map-pin", color="#2E6FF2"),
                    rx.text(address["address"], font_weight="medium", color="#22282C"),
                    align="center",
                    spacing="2",
                ),

        
                # Right side: default indicator or button
                rx.cond(
                    address["is_default"],
                    rx.text("Default Address", font_weight="bold", color="green"),
                    rx.button(
                        "Set as Default",
                        font_weight="bold",
                        color="white",
                        bg="#2E6FF2",
                        border_radius="5px",
                        padding="6px 12px",
                        cursor="pointer",
                        _hover={"opacity": "0.9"},
                        on_click=lambda: AddressState.set_default_address(
                            address["id"]
                        ),
                    ),
                ),
                justify="between",  # Spread items left/right
                       
                        on_click=lambda: AddressState.set_default_address(address["id"]),
                    ),
                ),

                justify="between",  
                align="center",
                width="100%",
                mt="5px",
            ),
   

def address_content() -> rx.Component:
    return rx.vstack(
        rx.center(
            rx.text(
                "My Address",
                font_size="20px",
                font_weight="bold",
                margin_bottom="20px",
                color="#22282c",
            ),
            width="100%",
        ),
      
        rx.button(
            "Add New Address",
            on_click=AddressState.toggle_form,
            background_color="#2E6FF2",
            color="white",
            border_radius="5px",
            padding="20px 10px",
            margin_bottom="20px",
            align_self="flex-end",
            font_weight="bold",
            cursor="pointer",
        ),
      
        new_address_modal(),

      
        rx.foreach(AddressState.addresses, lambda a: address_card(a)),
        spacing="2",
        width="100%",
        on_mount=AddressState.load_addresses,
    )


def card_content() -> rx.Component:
    return rx.vstack(
        # Header
        rx.hstack(
            rx.heading("Payment Methods", size="6", color="#22282c"),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.icon("credit-card", size=18),
                    "Add Card",
                    on_click=PaymentState.toggle_card_form,
                    color_scheme="blue",
                    variant="soft",
                ),
                rx.button(
                    rx.icon("landmark", size=18),
                    "Add Bank",
                    on_click=PaymentState.toggle_bank_form,
                    color_scheme="green",
                    variant="soft",
                ),
                spacing="3",
            ),
            width="100%",
            align_items="center",
            margin_bottom="20px",
        ),
        
        # Loading state
        rx.cond(
            PaymentState.is_loading_payments,
            rx.center(
                rx.spinner(size="3"),
                padding="40px",
                width="100%",
            ),
            rx.vstack(
                # Credit Cards Section
                rx.cond(
                    PaymentState.credit_cards.length() > 0,
                    rx.vstack(
                        rx.hstack(
                            rx.icon("credit-card", size=20, color="#2E6FF2"),
                            rx.text(
                                "Credit Cards",
                                font_size="18px",
                                font_weight="600",
                                color="#22282C",
                            ),
                            spacing="2",
                            align_items="center",
                        ),
                        rx.vstack(
                            rx.foreach(
                                PaymentState.credit_cards,
                                credit_card_item
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                
                # Bank Accounts Section
                rx.cond(
                    PaymentState.bank_accounts.length() > 0,
                    rx.vstack(
                        rx.hstack(
                            rx.icon("landmark", size=20, color="#10B981"),
                            rx.text(
                                "Bank Accounts",
                                font_size="18px",
                                font_weight="600",
                                color="#22282C",
                            ),
                            spacing="2",
                            align_items="center",
                        ),
                        rx.vstack(
                            rx.foreach(
                                PaymentState.bank_accounts,
                                bank_account_item
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                        margin_top="20px",
                    ),
                    rx.fragment(),
                ),
                
                # Empty state
                rx.cond(
                    (PaymentState.credit_cards.length() == 0) & (PaymentState.bank_accounts.length() == 0),
                    rx.center(
                        rx.vstack(
                            rx.icon("wallet", size=48, color="#9CA3AF"),
                            rx.text(
                                "No payment methods yet",
                                font_size="18px",
                                font_weight="600",
                                color="#6B7280",
                            ),
                            rx.text(
                                "Add a credit card or bank account to get started",
                                font_size="14px",
                                color="#9CA3AF",
                            ),
                            spacing="2",
                            align_items="center",
                        ),
                        padding="60px 20px",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                
                spacing="4",
                width="100%",
            ),
        ),
        
        # Modals
        new_card_modal(),
        new_bank_model(),
        
        spacing="4",
        width="100%",
        padding="20px",
        on_mount=PaymentState.load_payment_methods,
    )


def new_card_modal() -> rx.Component:
    return rx.cond(
        PaymentState.show_card_form,
        rx.box(
            rx.box(
                rx.vstack(
                    # Close button
                    rx.box(
                        rx.icon(
                            tag="x",
                            size=28,
                            color="#6B7280",
                            cursor="pointer",
                            on_click=PaymentState.close_card_form,
                            _hover={"color": "#22282C"},
                        ),
                        width="100%",
                        display="flex",
                        justify_content="flex-end",
                    ),
                    
                    rx.center(
                        rx.text(
                            "Add Credit Card",
                            font_size="24px",
                            font_weight="bold",
                            color="#22282C",
                        ),
                        width="100%",
                    ),
                    
                    rx.text(
                        "Enter your card details (mock data for testing)",
                        font_size="14px",
                        color="#929FA7",
                        margin_bottom="10px",
                    ),
                    
                    # Card Number
                    rx.vstack(
                        rx.text("Card Number", font_size="14px", font_weight="500", color="#22282c"),
                        rx.input(
                            placeholder="1234 5678 9012 3456",
                            value=PaymentState.card_number,
                            on_change=PaymentState.set_card_number,
                            style=input_style,
                        ),
                        spacing="1",
                        align_items="start",
                        width="100%",
                    ),
                    
                    # Cardholder Name
                    rx.vstack(
                        rx.text("Cardholder Name", font_size="14px", font_weight="500", color="#22282c"),
                        rx.input(
                            placeholder="John Smith",
                            value=PaymentState.card_holder_name,
                            on_change=PaymentState.set_card_holder_name,
                            style=input_style,
                        ),
                        spacing="1",
                        align_items="start",
                        width="100%",
                    ),
                    
                    # Expiration and CVV
                    rx.hstack(
                        rx.vstack(
                            rx.text("Exp. Month", font_size="14px", font_weight="500", color="#22282c"),
                            rx.input(
                                placeholder="12",
                                value=PaymentState.exp_month,
                                on_change=PaymentState.set_exp_month,
                                style=input_style,
                                max_length=2,
                            ),
                            spacing="1",
                            align_items="start",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.text("Exp. Year", font_size="14px", font_weight="500", color="#22282c"),
                            rx.input(
                                placeholder="2026",
                                value=PaymentState.exp_year,
                                on_change=PaymentState.set_exp_year,
                                style=input_style,
                                max_length=4,
                            ),
                            spacing="1",
                            align_items="start",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.text("CVV", font_size="14px", font_weight="500", color="#22282c"),
                            rx.input(
                                placeholder="123",
                                value=PaymentState.cvv,
                                on_change=PaymentState.set_cvv,
                                style=input_style,
                                max_length=4,
                                type="password",
                            ),
                            spacing="1",
                            align_items="start",
                            width="100%",
                        ),
                        width="100%",
                        spacing="3",
                    ),
                    
                    # Set as default
                    rx.hstack(
                        rx.checkbox(
                            checked=PaymentState.is_default,
                            on_change=PaymentState.set_is_default,
                        ),
                        rx.text("Set as default payment method", font_size="14px", color="#22282c"),
                        align_items="center",
                    ),
                    
                    # Error message
                    rx.cond(
                        PaymentState.error_message != "",
                        rx.text(
                            PaymentState.error_message,
                            color="#EF4444",
                            font_size="14px",
                        ),
                        rx.fragment(),
                    ),
                    
                    # Submit button
                    rx.button(
                        "Add Card",
                        on_click=PaymentState.submit_card,
                        width="100%",
                        bg="#2E6FF2",
                        color="white",
                        border_radius="12px",
                        padding="15px",
                        font_size="16px",
                        font_weight="600",
                        cursor="pointer",
                        _hover={"opacity": "0.9"},
                        margin_top="10px",
                    ),
                    
                    spacing="4",
                    width="100%",
                ),
                bg="white",
                padding="20px 40px",
                border_radius="20px",
                width="500px",
                max_width="90vw",
                box_shadow="0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)",
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
    )

def new_bank_model() -> rx.Component:
    return rx.cond(
        PaymentState.show_bank_form,
        rx.box(
            rx.box(
                rx.vstack(
                    # Close button
                    rx.box(
                        rx.icon(
                            tag="x",
                            size=28,
                            color="#6B7280",
                            cursor="pointer",
                            on_click=PaymentState.close_bank_form,
                            _hover={"color": "#22282C"},
                        ),
                        width="100%",
                        display="flex",
                        justify_content="flex-end",
                    ),
                    
                    rx.center(
                        rx.text(
                            "Add Bank Account",
                            font_size="24px",
                            font_weight="bold",
                            color="#22282C",
                        ),
                        width="100%",
                    ),
                    
                    rx.text(
                        "Enter your bank account details (mock data for testing)",
                        font_size="14px",
                        color="#929FA7",
                        margin_bottom="10px",
                    ),
                    
                    rx.vstack(
                        rx.text("Provider", color="#22282c", font_size="14px", font_weight="500"),    
                        rx.input(
                            placeholder="Provider (e.g. scb, kbank, bbl)",
                            value=PaymentState.bank_provider,
                            on_change=PaymentState.set_bank_provider,
                            style=input_style
                        ),
                        
                        rx.text("Bank Name", color="#22282c", font_size="14px", font_weight="500"),
                        rx.input(
                            placeholder="Bank Name (e.g. Siam Commercial Bank)",
                            value=PaymentState.bank_name,
                            on_change=PaymentState.set_bank_name,
                            style=input_style
                        ),
                        
                        rx.text("Account Holder", color="#22282c", font_size="14px", font_weight="500"),
                        rx.input(
                            placeholder="Account Holder Name",
                            value=PaymentState.account_holder,
                            on_change=PaymentState.set_account_holder,
                            style=input_style
                        ),
                        
                        rx.text("Last 4 Digits", color="#22282c", font_size="14px", font_weight="500"),
                        rx.input(
                            placeholder="Last 4 Digits of Account Number",
                            value=PaymentState.bank_last4,
                            on_change=PaymentState.set_bank_last4,
                            style=input_style,
                            max_length=4
                        ),
                        
                        rx.text("Provider Token (Optional)", color="#22282c", font_size="14px", font_weight="500"),
                        rx.input(
                            placeholder="Auto-generated if left empty",
                            value=PaymentState.bank_provider_token,
                            on_change=PaymentState.set_bank_provider_token,
                            style=input_style
                        ),
                        
                        rx.hstack(
                            rx.checkbox(
                                checked=PaymentState.bank_is_default,
                                on_change=PaymentState.set_bank_is_default
                            ),
                            rx.text("Set as Default", color="#22282c", font_size="14px"),
                            align_items="center",
                        ),
                        
                        # Error message
                        rx.cond(
                            PaymentState.error_message != "",
                            rx.text(
                                PaymentState.error_message,
                                color="#EF4444",
                                font_size="14px",
                            ),
                            rx.fragment(),
                        ),
                        
                        rx.button(
                            "Add Bank Account",
                            on_click=PaymentState.submit_bank,
                            color_scheme="green",
                            width="100%",
                            padding="15px",
                            font_size="16px",
                            font_weight="600",
                            cursor="pointer",
                            _hover={"opacity": "0.9"},
                            margin_top="10px",
                        ),
                        
                        spacing="3",
                        padding="10px",
                        width="100%"
                    ),
                    
                    spacing="4",
                    width="100%",
                ),
                bg="white",
                padding="20px 40px",
                border_radius="20px",
                width="500px",
                max_width="90vw",
                box_shadow="0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)",
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
    )
    

def wishlist_content() -> rx.Component:
    return rx.vstack(
        rx.center(
            rx.text(
                "Wishlist",
                font_size="20px",
                font_weight="bold",
                margin_bottom="20px",
                color="#22282c",
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
                color="#22282c",
            ),
            width="100%",
        ),
        rx.text("Your order history will appear here...", color="#22282c"),
        spacing="5",
        width="100%",
    )



def review_form_modal() -> rx.Component:
    """Modal for editing reviews."""
    return rx.cond(
        ReviewState.show_edit_form,
        rx.box(
            rx.box(
                rx.vstack(
                    # Close button
                    rx.box(
                        rx.icon(
                            tag="x",
                            size=28,
                            color="#6B7280",
                            cursor="pointer",
                            on_click=ReviewState.close_form,
                            _hover={"color": "#22282C"},
                        ),
                        width="100%",
                        display="flex",
                        justify_content="flex-end",
                    ),
                    
                    # Title
                    rx.center(
                        rx.text(
                            "Edit Review",
                            font_size="24px",
                            font_weight="bold",
                            color="#22282C",
                        ),
                        width="100%",
                    ),
                    
                    # Product ID (read-only)
                    rx.vstack(
                        rx.text("Product ID", font_size="14px", font_weight="500", color="#22282c"),
                        rx.input(
                            value=ReviewState.product_id,
                            width="100%",
                            padding="5px",
                            border="1px solid #D1D5DB",
                            border_radius="12px",
                            background_color="#F3F4F6",
                            is_read_only=True,
                        ),
                        spacing="1",
                        width="100%",
                        align_items="start",
                    ),
                    
                    # Rating
                    rx.vstack(
                        rx.text("Rating", font_size="14px", font_weight="500", color="#22282c"),
                        rx.select(
                            ["1", "2", "3", "4", "5"],
                            value=ReviewState.rating,
                            on_change=ReviewState.set_rating,
                            width="100%",
                        ),
                        spacing="1",
                        width="100%",
                        align_items="start",
                    ),
                    
                    # Comment
                    rx.vstack(
                        rx.text("Comment", font_size="14px", font_weight="500", color="#22282c"),
                        rx.text_area(
                            placeholder="Write your review...",
                            value=ReviewState.comment,
                            on_change=ReviewState.set_comment,
                            width="100%",
                            min_height="100px",
                            padding="5px",
                            border="1px solid #D1D5DB",
                            border_radius="12px",
                            background_color="#ffffff",
                        ),
                        spacing="1",
                        width="100%",
                        align_items="start",
                    ),
                    
                    # Image Upload
                    rx.vstack(
                        rx.text("Image (Optional)", font_size="14px", font_weight="500", color="#22282c"),
                        rx.cond(
                            ReviewState.review_image,
                            rx.vstack(
                                rx.image(
                                    src=f"data:image/jpeg;base64,{ReviewState.review_image}",
                                    width="200px",
                                    height="200px",
                                    object_fit="cover",
                                    border_radius="8px",
                                ),
                                rx.button(
                                    "Remove Image",
                                    on_click=ReviewState.remove_image,
                                    variant="soft",
                                    color_scheme="red",
                                    size="2",
                                ),
                                spacing="2",
                                align_items="center",
                            ),
                            rx.upload(
                                rx.button(
                                    rx.icon("image", size=16),
                                    "Upload Image",
                                    size="2",
                                    variant="soft",
                                    cursor="pointer",
                                ),
                                accept={
                                    "image/png": [".png"],
                                    "image/jpeg": [".jpg", ".jpeg"],
                                },
                                max_files=1,
                                on_drop=ReviewState.handle_image_upload,
                            ),
                        ),
                        rx.cond(
                            ReviewState.upload_image_error != "",
                            rx.text(
                                ReviewState.upload_image_error,
                                color="#EF4444",
                                font_size="12px",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                        width="100%",
                        align_items="start",
                    ),
                    
                    # Error Messages
                    rx.cond(
                        ReviewState.error_message != "",
                        rx.text(
                            ReviewState.error_message,
                            color="#EF4444",
                            font_size="14px",
                        ),
                        rx.fragment(),
                    ),
                    
                    # Submit Button
                    rx.button(
                        "Update Review",
                        on_click=ReviewState.edit_review,
                        width="100%",
                        bg="#2E6FF2",
                        color="white",
                        border_radius="12px",
                        padding="15px",
                        font_size="16px",
                        font_weight="600",
                        cursor="pointer",
                        _hover={"opacity": "0.9"},
                    ),
                    
                    spacing="4",
                    width="100%",
                ),
                bg="white",
                padding="20px 40px",
                border_radius="20px",
                width="600px",
                max_width="90vw",
                max_height="90vh",
                overflow_y="auto",
                box_shadow="0 20px 25px -5px rgba(0,0,0,0.1)",
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
    )


def render_stars(rating):
    return rx.hstack(
        *[
            rx.icon(
                "star",
                color=rx.cond(i < rating, "#FCD34D", "#D1D5DB"),
                size=20,
            )
            for i in range(5)
        ]
    )


def review_card(review: Review) -> rx.Component:
    """Display a single review card."""
    return rx.box(
        rx.vstack(
       
            rx.hstack(
                render_stars(review.rating),
                rx.spacer(),
                rx.hstack(
                    rx.icon(
                        "pencil",
                        size=18,
                        color="#2E6FF2",
                        cursor="pointer",
                        on_click=lambda: ReviewState.open_edit_form(review),
                    ),
                    rx.text(
                        "Edit",
                        font_weight="semibold",
                        color="#2E6FF2",
                        cursor="pointer",
                        on_click=lambda: ReviewState.open_edit_form(review),
                    ),
                    rx.icon(
                        "trash",
                        size=18,
                        color="#FF4D4D",
                        cursor="pointer",
                        on_click=lambda: ReviewState.delete_review(review.id),
                    ),
                    rx.text(
                        "Delete",
                        font_weight="semibold",
                        color="#FF4D4D",
                        cursor="pointer",
                        on_click=lambda: ReviewState.delete_review(review.id),
                    ),
                    spacing="3",
                    align="center",
                ),
                width="100%",
                align_items="center",
            ),
            
            rx.text(
                f"Product ID: {review.product_id}",
                font_size="14px",
                color="#6B7280",
            ),
            
            rx.cond(
                review.comment != "",
                rx.text(
                    review.comment,
                    font_size="14px",
                    color="#22282C",
                ),
                rx.fragment(),
            ),
            
            # Image if exists
            rx.cond(
                review.image,
                rx.image(
                    src=f"data:image/jpeg;base64,{review.image}",
                    width="200px",
                    height="200px",
                    object_fit="cover",
                    border_radius="8px",
                ),
                rx.fragment(),
            ),
            
            # Dates
            rx.hstack(
                rx.text(
                    f"Created: {review.created_at}",
                    font_size="12px",
                    color="#9CA3AF",
                ),
                rx.text(
                    f"Updated: {review.updated_at}",
                    font_size="12px",
                    color="#9CA3AF",
                ),
                spacing="4",
            ),
            
            spacing="3",
            width="100%",
            align_items="start",
        ),
        padding="20px",
        border="1px solid #E5E7EB",
        border_radius="12px",
        bg="white",
        width="100%",
        _hover={
            "box_shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
            "border_color": "#2E6FF2",
        },
        transition="all 0.2s ease",
    )



def reviews_content() -> rx.Component:
    """Main reviews content component - Load, Edit, and Delete only."""
    return rx.vstack(
      
        rx.center(
            rx.heading("My Reviews", size="6", color="#22282c"),
            width="100%",
            margin_bottom="20px",
        ),
        
        # Error message
        rx.cond(
            ReviewState.error_message != "",
            rx.box(
                rx.text(
                    ReviewState.error_message,
                    color="#EF4444",
                    font_size="14px",
                ),
                padding="10px",
                bg="#FEE2E2",
                border_radius="8px",
                width="100%",
            ),
            rx.fragment(),
        ),
        
     
        rx.cond(
            ReviewState.is_loading,
            rx.center(
                rx.spinner(size="3"),
                padding="40px",
                width="100%",
            ),
            rx.cond(
                ReviewState.reviews.length() > 0,
                rx.vstack(
                    rx.foreach(ReviewState.reviews, review_card),
                    spacing="4",
                    width="100%",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("message-square", size=48, color="#9CA3AF"),
                        rx.text(
                            "No reviews yet",
                            font_size="18px",
                            font_weight="600",
                            color="#6B7280",
                        ),
                        rx.text(
                            "Your reviews will appear here",
                            font_size="14px",
                            color="#9CA3AF",
                        ),
                        spacing="2",
                        align_items="center",
                    ),
                    padding="60px 20px",
                    width="100%",
                ),
            ),
        ),
        
        # Form Modal
        review_form_modal(),
        
        spacing="5",
        width="100%",
        padding="20px",
    )


def notification_content() -> rx.Component:
    return rx.vstack(
        rx.center(
            rx.text(
                "Notifications",
                font_size="20px",
                font_weight="bold",
                margin_bottom="20px",
                color="#22282c",
            ),
            width="100%",
        ),
        rx.text("Your notifications will appear here...", color="#22282c"),
        spacing="5",
        width="100%",
    )


def input_with_label(
    label: str, value: str = "", on_change: Optional[Callable] = None
) -> rx.Component:
    return rx.vstack(
        rx.text(label, font_size="14px", font_weight="500", margin_bottom="4px"),
        rx.input(
            value=value,  # reactive binding
            placeholder=label,
            width="100%",
            style=input_style,
            on_change=on_change,  # update state on user input
        ),
        spacing="1",
        width="100%",
        color="#22282c",
    )


def input_with_label_date(
    label: str, value: str = "", on_change: Optional[Callable] = None
) -> rx.Component:
    return rx.vstack(
        rx.text(label, font_size="14px", font_weight="500", margin_bottom="4px"),
        rx.input(
            type="date",
            value=value,  # use `value` instead of default_value
            placeholder=label,
            width="100%",
            style=input_style,
            on_change=on_change,  # reactive binding
        ),
        spacing="1",
        width="100%",
        color="#22282c",
    )


def select_with_label(
    label: str,
    options: list[str],
    value: str = "",
    on_change: Optional[Callable] = None,
) -> rx.Component:
    return rx.vstack(
        rx.text(label, font_size="14px", font_weight="500", margin_bottom="4px"),
        rx.select(
            options, value=value, placeholder=label, width="100%", on_change=on_change
        ),
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
        "font_weight": "600" if active else "400",
        "_hover": {"background_color": "#F3F4F6", "color": "#22282C"},
    }


def profile_page() -> rx.Component:
    return rx.box(template(profile_content), on_mount=ProfileState.load_user_data)


input_style = {
    "color": "#22282C",
    "background_color": "white",
    "border": "1px solid #929FA7",
    "border_radius": "8px",
    "width": "100%"
}


def get_card_brand_icon(brand: str) -> str:
    """Return icon for card brand."""
    brand_lower = brand.lower() if brand else ""
    if "visa" in brand_lower:
        return "credit-card"
    elif "mastercard" in brand_lower:
        return "credit-card"
    elif "amex" in brand_lower or "american express" in brand_lower:
        return "credit-card"
    else:
        return "credit-card"


def credit_card_item(card: CreditCard) -> rx.Component:
    """Display a single credit card."""
    return rx.box(
        rx.hstack(
            # Left side - Card info
            rx.hstack(
                rx.box(
                    rx.icon(
                        "credit-card",  # Simplified - just use one icon
                        size=32,
                        color="#2E6FF2",
                    ),
                    padding="10px",
                    border_radius="8px",
                    bg="#EFF6FF",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            card.card_brand,
                            font_size="16px",
                            font_weight="600",
                            color="#22282C",
                        ),
                        rx.cond(
                            card.is_default,
                            rx.badge(
                                "Default",
                                color_scheme="green",
                                variant="soft",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                        align_items="center",
                    ),
                    rx.text(
                        f"•••• •••• •••• {card.last4}",
                        font_size="14px",
                        color="#6B7280",
                    ),
                    rx.text(
                        f"Expires {card.exp_month}/{card.exp_year}",
                        font_size="12px",
                        color="#9CA3AF",
                    ),
                    spacing="1",
                    align_items="start",
                ),
                spacing="3",
                align_items="center",
            ),
            
            rx.spacer(),
            
            # Right side - Actions
            rx.hstack(
                rx.cond(
                    ~card.is_default,
                    rx.button(
                        "Set Default",
                        size="2",
                        variant="soft",
                        color_scheme="blue",
                        on_click=lambda: PaymentState.set_default_card(card.id)
                    ),
                    rx.fragment(),
                ),
                rx.icon_button(
                    rx.icon("trash-2", size=18),
                    size="2",
                    variant="soft",
                    color_scheme="red",
                    on_click=lambda: PaymentState.delete_credit_card(card.id),
                ),
                spacing="2",
            ),
            
            width="100%",
            align_items="center",
        ),
        padding="20px",
        border="1px solid #E5E7EB",
        border_radius="12px",
        bg="white",
        width="100%",
        _hover={
            "box_shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
            "border_color": "#2E6FF2",
        },
        transition="all 0.2s ease",
    )


def bank_account_item(account: BankAccount) -> rx.Component:
    """Display a single bank account."""
    return rx.box(
        rx.hstack(
            # Left side - Bank info
            rx.hstack(
                rx.box(
                    rx.icon(
                        "landmark",
                        size=32,
                        color="#10B981",
                    ),
                    padding="10px",
                    border_radius="8px",
                    bg="#D1FAE5",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            account.bank_name,
                            font_size="16px",
                            font_weight="600",
                            color="#22282C",
                        ),
                        rx.cond(
                            account.is_default,
                            rx.badge(
                                "Default",
                                color_scheme="green",
                                variant="soft",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                        align_items="center",
                    ),
                    rx.text(
                        account.account_holder,
                        font_size="14px",
                        color="#6B7280",
                    ),
                    rx.text(
                        f"•••• •••• •••• {account.last4}",
                        font_size="12px",
                        color="#9CA3AF",
                    ),
                    spacing="1",
                    align_items="start",
                ),
                spacing="3",
                align_items="center",
            ),
            
            rx.spacer(),
            
            # Right side - Actions
            rx.hstack(
                rx.cond(
                    ~account.is_default,
                    rx.button(
                        "Set Default",
                        size="2",
                        variant="soft",
                        color_scheme="green",
                        on_click=lambda: PaymentState.set_default_bank(account.id),
                    ),
                    rx.fragment(),
                ),
                rx.icon_button(
                    rx.icon("trash-2", size=18),
                    size="2",
                    variant="soft",
                    color_scheme="red",
                    on_click=lambda: PaymentState.delete_bank_account(account.id),
                ),
                spacing="2",
            ),
            
            width="100%",
            align_items="center",
        ),
        padding="20px",
        border="1px solid #E5E7EB",
        border_radius="12px",
        bg="white",
        width="100%",
        _hover={
            "box_shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
            "border_color": "#10B981",
        },
        transition="all 0.2s ease",
    )


@rx.page(route="/profile", on_load=[PaymentState.load_payment_methods,ReviewState.load_reviews])
def profile_page() -> rx.Component:

    return rx.box(
        template(profile_content),
        on_mount=ProfileState.load_user_data  
    )