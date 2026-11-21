from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402  (load .env before the app reads config)

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
