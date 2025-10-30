import reflex as rx

config = rx.Config(
    app_name="frontend",
    backend_port=8080,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)
