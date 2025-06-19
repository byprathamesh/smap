import reflex as rx

config = rx.Config(
    app_name="surveillance",
    backend_port=8000,
    api_url="http://localhost:8000",
    frontend_port=3000,
    
    # Database configuration for Reflex ORM
    db_url="sqlite:///surveillance.db",
    
    # Disable tailwind deprecation warning
    tailwind=None,
)