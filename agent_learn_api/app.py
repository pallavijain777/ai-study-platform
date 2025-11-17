from agent_learn_api import create_app
from agent_learn_api.config import Config
from agent_learn_api import socket_io
from flask_cors import CORS

app = create_app()

# Enable CORS for the frontend
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)


if __name__ == "__main__":
    socket_io.run(app=app, debug=True, port=5000)
