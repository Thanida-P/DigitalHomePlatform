import reflex as rx
from .pages.home import home_page

# from .pages.about import about_page
from .pages.shop import shop_page
from .pages.signup import signup_page
from .pages.login import login_page
from .pages.profile import profile_page
from .pages.cart import cart_page
from .pages.admin_dashboard import admin_dashboard
from .pages.my_home import my_digital_home_page
from .pages.rooms.room import room_page
from .pages.signup_admin import adminsignup_page
from .state import DynamicState
from .pages.details.product_detail import product_detail_page
from .pages.orders import orders_page

app = rx.App()


app.add_page(
    room_page,
    route="/rooms/[room]",
    on_load=DynamicState.on_load,
)
app.add_page(room_page, route="/static/x", on_load=DynamicState.on_load)
app.add_page(room_page)

app.add_page(product_detail_page,route="/details/[product_Id]")

app.add_page(home_page, route="/")
# app.add_page(about_page, route="/about")
app.add_page(shop_page, route="/shop")
app.add_page(signup_page, route="/signup")
app.add_page(login_page, route="/login")
app.add_page(profile_page, route="/profile")
app.add_page(product_detail_page, route="/product_detail")
app.add_page(cart_page, route="/cart")
app.add_page(admin_dashboard, route="/admin_dashboard")
app.add_page(adminsignup_page, route="/signup_admin")
# app.add_page(my_digital_home_page,route="/my_home")
app.add_page(room_page, route="/room")
app.add_page(orders_page,route="/orders")

if __name__ == "__main__":
    app.run()
