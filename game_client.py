import time
import threading
import requests
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

SERVER_URL = "http://localhost:5000"

current_user = None
player_entity = None
other_players = {}
stop_threads = False


def logout_user():
    global current_user
    if current_user:
        try:
            requests.post(f"{SERVER_URL}/logout", json={"username": current_user}, timeout=2)
        except Exception:
            pass
        current_user = None


class LoginScreen:
    def __init__(self):
        self.root = Entity(parent=camera.ui)

        self.title = Text(
            text="DEV-CLAN",
            origin=(0, 0),
            y=0.28,
            scale=2,
            parent=self.root,
        )

        self.subtitle = Text(
            text="Login or Register",
            origin=(0, 0),
            y=0.15,
            scale=1.1,
            parent=self.root,
        )

        self.username_field = InputField(
            default_value="player1",
            x=-0.28,
            y=0.02,
            width=0.55,
            parent=self.root,
        )

        self.password_field = InputField(
            default_value="123456",
            x=-0.28,
            y=-0.12,
            width=0.55,
            hide_input=True,
            parent=self.root,
        )

        self.status_text = Text(
            text="",
            origin=(0, 0),
            y=-0.27,
            scale=0.9,
            color=color.yellow,
            parent=self.root,
        )

        self.login_btn = Button(
            text="Login",
            color=color.green,
            x=-0.18,
            y=-0.4,
            scale=(0.18, 0.07),
            parent=self.root,
            on_click=self.login,
        )

        self.register_btn = Button(
            text="Register",
            color=color.azure,
            x=0.18,
            y=-0.4,
            scale=(0.18, 0.07),
            parent=self.root,
            on_click=self.register,
        )

    def login(self):
        username = self.username_field.text.strip()
        password = self.password_field.text.strip()

        if not username or not password:
            self.status_text.text = "Please enter a username and password."
            return

        try:
            response = requests.post(
                f"{SERVER_URL}/login",
                json={"username": username, "password": password},
                timeout=3,
            )

            if response.status_code == 200:
                self.status_text.text = "Login successful!"
                self.cleanup()
                start_game(username)
            else:
                self.status_text.text = response.json().get("error", "Login failed")
        except Exception as e:
            self.status_text.text = f"Server error: {e}"

    def register(self):
        username = self.username_field.text.strip()
        password = self.password_field.text.strip()

        if not username or not password:
            self.status_text.text = "Please enter a username and password."
            return

        try:
            response = requests.post(
                f"{SERVER_URL}/register",
                json={"username": username, "password": password},
                timeout=3,
            )

            if response.status_code == 201:
                self.status_text.text = "Account created! You can now log in."
            else:
                self.status_text.text = response.json().get("error", "Registration failed")
        except Exception as e:
            self.status_text.text = f"Server error: {e}"

    def cleanup(self):
        destroy(self.root)


def update_server_position():
    global player_entity, current_user
    while not stop_threads:
        if current_user and player_entity:
            try:
                pos = player_entity.position
                requests.post(
                    f"{SERVER_URL}/update_position",
                    json={
                        "username": current_user,
                        "x": round(pos.x, 2),
                        "y": round(pos.y, 2),
                        "z": round(pos.z, 2),
                    },
                    timeout=2,
                )
            except Exception:
                pass
        time.sleep(0.1)


def refresh_other_players():
    global other_players
    while not stop_threads:
        try:
            response = requests.get(f"{SERVER_URL}/players", timeout=2)
            if response.status_code != 200:
                time.sleep(0.5)
                continue

            players = response.json().get("players", [])
            online_names = set()

            for player_data in players:
                username = player_data["username"]
                online_names.add(username)

                if username == current_user:
                    continue

                if username not in other_players:
                    avatar = Entity(
                        model="cube",
                        color=color.cyan,
                        scale=(0.8, 1.8, 0.8),
                        collider="box",
                    )
                    other_players[username] = avatar

                other_players[username].position = (
                    player_data["x"],
                    player_data["y"],
                    player_data["z"],
                )

            for username in list(other_players.keys()):
                if username not in online_names:
                    destroy(other_players[username])
                    del other_players[username]

        except Exception:
            pass

        time.sleep(0.5)


def start_game(username):
    global current_user, player_entity, stop_threads
    current_user = username
    stop_threads = False

    Sky(color=color.rgba(120, 160, 255, 255))

    Entity(
        model="plane",
        scale=(40, 1, 40),
        texture="grass",
        texture_scale=(30, 30),
        collider="box",
        position=(0, -0.2, 0),
    )

    for x, y, z, sx, sy, sz in [
        (3, 1, 3, 3, 1, 3),
        (-4, 2, 0, 2, 4, 2),
        (0, 3, -5, 2, 1, 2),
    ]:
        Entity(
            model="cube",
            color=color.orange,
            position=(x, y, z),
            scale=(sx, sy, sz),
            collider="box",
        )

    for x, z in [(-6, -2), (6, 2)]:
        Entity(
            model="cube",
            color=color.azure,
            position=(x, 0.5, z),
            scale=(1.5, 1, 1.5),
            collider="box",
        )

    player_entity = FirstPersonController()
    player_entity.position = (0, 2, -8)
    player_entity.speed = 5
    player_entity.cursor.visible = False

    Text(text=f"Player: {current