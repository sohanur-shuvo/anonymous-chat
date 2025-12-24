import streamlit as st
import json
import os
from datetime import datetime
from uuid import uuid4
import time
import hashlib
from dotenv import load_dotenv
import requests
from streamlit_google_auth import Authenticate

# Load environment variables
load_dotenv()
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "anonymous--chats")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Shuvo@123")

if FIREBASE_DB_URL and FIREBASE_DB_URL.endswith("/"):
    FIREBASE_DB_URL = FIREBASE_DB_URL[:-1]


def get_google_authenticator():
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return None
        
    import tempfile
    import json as json_lib
    
    creds_data = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "project_id": GOOGLE_PROJECT_ID,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uris": ["http://localhost:8501"]
        }
    }
    
    creds_path = os.path.join(tempfile.gettempdir(), "google_creds.json")
    with open(creds_path, "w") as f:
        json_lib.dump(creds_data, f)

    return Authenticate(
        secret_credentials_path=creds_path,
        cookie_name='google_auth_cookie',
        cookie_key='this_is_a_secret_key', 
        cookie_expiry_days=30,
        redirect_uri="http://localhost:8501"
    )

# Page configuration
st.set_page_config(
    page_title="Anonymous Chat",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)


def format_message_time():
    return datetime.now().strftime("%H:%M:%S")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    # Try Firebase first
    if FIREBASE_DB_URL:
        try:
            response = requests.get(f"{FIREBASE_DB_URL}/users.json")
            if response.status_code == 200:
                users = response.json()
                return users if users else {}
        except Exception:
            pass
    
    # Fallback to local
    try:
        if not os.path.exists("database"):
            os.makedirs("database")
        if os.path.exists("database/users.json"):
            with open("database/users.json", "r") as f:
                return json.load(f)
        return {}
    except Exception:
        return {}


def firebase_auth(email, password, mode="login"):
    """
    mode can be 'login' or 'signup'
    """
    if not FIREBASE_API_KEY:
        return {"error": "Firebase API Key not found in environment variables."}

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:{'signInWithPassword' if mode == 'login' else 'signUp'}?key={FIREBASE_API_KEY}"
    
    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        
        if response.status_code == 200:
            return {"success": True, "localId": data["localId"], "email": data["email"]}
        else:
            error_message = data.get("error", {}).get("message", "Unknown error")
            return {"success": False, "error": error_message}
    except Exception as e:
        return {"success": False, "error": str(e)}


def firebase_google_login(id_token):
    """
    Authenticate with Firebase using a Google ID Token
    """
    if not FIREBASE_API_KEY:
        return {"error": "Firebase API Key not found"}

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={FIREBASE_API_KEY}"
    
    payload = {
        "postBody": f"id_token={id_token}&providerId=google.com",
        "requestUri": "http://localhost",
        "returnSecureToken": True
    }
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        
        if response.status_code == 200:
            return {
                "success": True, 
                "localId": data["localId"], 
                "email": data["email"],
                "displayName": data.get("displayName", "Google User")
            }
        else:
            return {"success": False, "error": data.get("error", {}).get("message", "Unknown error")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def load_admin_settings():
    # Try Firebase first
    if FIREBASE_DB_URL:
        try:
            response = requests.get(f"{FIREBASE_DB_URL}/admin_settings.json")
            if response.status_code == 200:
                settings = response.json()
                return settings if settings else {"auto_refresh_interval": 2}
        except Exception:
            pass

    # Fallback to local
    try:
        if not os.path.exists("database"):
            os.makedirs("database")
        if os.path.exists("database/admin_settings.json"):
            with open("database/admin_settings.json", "r") as f:
                return json.load(f)
        return {"auto_refresh_interval": 2}  # Default 2 seconds
    except Exception:
        return {"auto_refresh_interval": 2}


def save_admin_settings(settings):
    # Save to Firebase
    if FIREBASE_DB_URL:
        try:
            requests.put(f"{FIREBASE_DB_URL}/admin_settings.json", json=settings)
        except Exception:
            pass

    # Save to local
    try:
        if not os.path.exists("database"):
            os.makedirs("database")
        with open("database/admin_settings.json", "w") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass


def save_users(users):
    # Save to Firebase
    if FIREBASE_DB_URL:
        try:
            requests.put(f"{FIREBASE_DB_URL}/users.json", json=users)
        except Exception:
            pass

    # Save to local
    try:
        if not os.path.exists("database"):
            os.makedirs("database")
        with open("database/users.json", "w") as f:
            json.dump(users, f, indent=2)
    except Exception:
        pass


def save_global_chat_message(message):
    # Save to Firebase
    if FIREBASE_DB_URL:
        try:
            # In Realtime DB, we can use POST to push to a list
            requests.post(f"{FIREBASE_DB_URL}/messages.json", json=message)
        except Exception:
            pass

    # Save to local
    try:
        if not os.path.exists("database"):
            os.makedirs("database")

        global_chat_file = "database/global_chat.json"

        if os.path.exists(global_chat_file):
            with open(global_chat_file, "r") as f:
                global_chat = json.load(f)
        else:
            global_chat = {"messages": []}

        global_chat["messages"].append(message)

        # Keep only last 1000 messages
        if len(global_chat["messages"]) > 1000:
            global_chat["messages"] = global_chat["messages"][-1000:]

        with open(global_chat_file, "w") as f:
            json.dump(global_chat, f, indent=2)
    except Exception:
        pass


def load_global_chat():
    # Try Firebase first
    if FIREBASE_DB_URL:
        try:
            response = requests.get(f"{FIREBASE_DB_URL}/messages.json")
            if response.status_code == 200:
                messages_dict = response.json()
                if messages_dict:
                    # Convert dict values to list if it's a dict of pushed items
                    if isinstance(messages_dict, dict):
                        return list(messages_dict.values())
                    return messages_dict
        except Exception:
            pass

    # Fallback to local
    try:
        if not os.path.exists("database"):
            os.makedirs("database")

        global_chat_file = "database/global_chat.json"

        if os.path.exists(global_chat_file):
            with open(global_chat_file, "r") as f:
                global_chat = json.load(f)
            return global_chat.get("messages", [])
        return []
    except Exception:
        return []


def clear_global_chat():
    # Clear Firebase
    if FIREBASE_DB_URL:
        try:
            requests.delete(f"{FIREBASE_DB_URL}/messages.json")
        except Exception:
            pass

    # Clear Local
    try:
        global_chat_file = "database/global_chat.json"
        if os.path.exists(global_chat_file):
            with open(global_chat_file, "w") as f:
                json.dump({"messages": []}, f, indent=2)
    except Exception:
        pass


def initialize_session():
    # Immediate check for hard logout in URL
    if st.query_params.get("logout") == "true":
        st.session_state.authenticated = False
        st.session_state.manual_logout = True
        st.session_state.is_admin = False
        if 'connected' in st.session_state:
            st.session_state.connected = False
        # Clear the parameter so it doesn't block future login attempts
        st.query_params.clear()
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "last_global_check" not in st.session_state:
        st.session_state.last_global_check = time.time()
    if "manual_logout" not in st.session_state:
        st.session_state.manual_logout = False


def login_form():
    st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h1>🌐 Anonymous Chat</h1>
            <p style='color: #666; font-size: 1.1rem;'>Please login or signup to access Anonymous Chat</p>
        </div>
    """, unsafe_allow_html=True)

    if not FIREBASE_API_KEY:
        st.warning("⚠️ Firebase API Key is missing. Local authentication will be used. Please set FIREBASE_API_KEY in your .env file.")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2, tab3 = st.tabs(["Login", "Sign Up", "Admin"])

        with tab1:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="Enter your email")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                login_button = st.form_submit_button("Login", use_container_width=True)

                if login_button:
                    if FIREBASE_API_KEY:
                        result = firebase_auth(email, password, mode="login")
                        if result.get("success"):
                            # Find username by email
                            users = load_users()
                            username = None
                            for uname, udata in users.items():
                                if udata.get("email") == email:
                                    username = uname
                                    break
                            
                            if username:
                                if users[username].get("status", "active") == "banned":
                                    st.error("Your account has been banned. Please contact admin.")
                                else:
                                    st.session_state.authenticated = True
                                    st.session_state.current_user = username
                                    st.session_state.is_admin = False
                                    st.success("Login successful! Redirecting...")
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                # First time login with this email but no local profile
                                # Create a default username from email
                                username = email.split("@")[0]
                                users[username] = {
                                    "name": username,
                                    "email": email,
                                    "status": "active",
                                    "created_at": datetime.now().isoformat(),
                                    "last_login": datetime.now().isoformat()
                                }
                                save_users(users)
                                st.session_state.authenticated = True
                                st.session_state.current_user = username
                                st.session_state.is_admin = False
                                st.success("Logged in and profile created!")
                                time.sleep(1)
                                st.rerun()
                        else:
                            st.error(f"Login failed: {result.get('error')}")
                    else:
                        # Fallback to local authentication (username instead of email)
                        users = load_users()
                        username = email # Treatment of email field as username for fallback
                        if username in users:
                            stored_password = users[username].get("password")
                            if stored_password == hash_password(password):
                                if users[username].get("status", "active") == "banned":
                                    st.error("Your account has been banned.")
                                else:
                                    st.session_state.authenticated = True
                                    st.session_state.current_user = username
                                    st.session_state.is_admin = False
                                    st.success("Login successful!")
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                st.error("Invalid credentials")
                        else:
                            st.error("Invalid credentials")

        with tab2:
            with st.form("signup_form"):
                new_name = st.text_input("Full Name", placeholder="Enter your full name")
                new_email = st.text_input("Email", placeholder="Enter your email")
                new_username = st.text_input("Username", placeholder="Choose a username")
                new_password = st.text_input("Password", type="password", placeholder="Choose a password")
                signup_button = st.form_submit_button("Sign Up", use_container_width=True)

                if signup_button:
                    if new_name and new_email and new_username and new_password:
                        if FIREBASE_API_KEY:
                            result = firebase_auth(new_email, new_password, mode="signup")
                            if result.get("success"):
                                users = load_users()
                                if new_username not in users:
                                    users[new_username] = {
                                        "name": new_name,
                                        "email": new_email,
                                        "status": "active",
                                        "created_at": datetime.now().isoformat(),
                                        "last_login": datetime.now().isoformat()
                                    }
                                    save_users(users)
                                    st.session_state.authenticated = True
                                    st.session_state.current_user = new_username
                                    st.session_state.is_admin = False
                                    st.success("Account created successfully!")
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Username already exists locally. Please choose another.")
                            else:
                                st.error(f"SignUp failed: {result.get('error')}")
                        else:
                            # Fallback local signup
                            users = load_users()
                            if new_username not in users:
                                users[new_username] = {
                                    "name": new_name,
                                    "email": new_email,
                                    "password": hash_password(new_password),
                                    "status": "active",
                                    "created_at": datetime.now().isoformat(),
                                    "last_login": datetime.now().isoformat()
                                }
                                save_users(users)
                                st.session_state.authenticated = True
                                st.session_state.current_user = new_username
                                st.session_state.is_admin = False
                                st.success("Local account created!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Username already exists")
                    else:
                        st.error("Please fill in all fields")

        with tab3:
            with st.form("admin_form"):
                admin_user_input = st.text_input("Admin Username", placeholder="Enter admin username")
                admin_pass_input = st.text_input("Admin Password", type="password", placeholder="Enter admin password")
                admin_login_button = st.form_submit_button("Admin Login", use_container_width=True)

                if admin_login_button:
                    # Strip whitespace to prevent login failures
                    admin_user_input = admin_user_input.strip()
                    admin_pass_input = admin_pass_input.strip()
                    
                    if admin_user_input == ADMIN_USERNAME and admin_pass_input == ADMIN_PASSWORD:
                        st.session_state.authenticated = True
                        st.session_state.current_user = ADMIN_USERNAME
                        st.session_state.is_admin = True
                        st.session_state.manual_logout = False
                        st.success("Admin login successful! Redirecting...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid admin credentials")

        # Google Login Section
        authenticator = get_google_authenticator()
        if authenticator:
            # Force logout logic
            if st.query_params.get("logout") == "true":
                st.session_state.manual_logout = True
                st.session_state.authenticated = False
                if "connected" in st.session_state:
                    st.session_state.connected = False

            # ONLY run Google check if NOT in a manual logout state
            if not st.session_state.get('manual_logout', False):
                try:
                    authenticator.check_authentification()
                except Exception:
                    pass
            
            # Only show Google UI if NOT authenticated session-wise
            if not st.session_state.authenticated:
                st.markdown("<div style='text-align: center; margin: 1rem 0;'>OR</div>", unsafe_allow_html=True)
                
                # If we are connected but it's a manual logout, reset the 'connected' state
                if st.session_state.get('manual_logout', False):
                    if 'connected' in st.session_state:
                        st.session_state.connected = False
                    if 'user_info' in st.session_state:
                        st.session_state.user_info = None

                if not st.session_state.get('connected', False):
                    if st.button("🚀 Sign in with Google", use_container_width=True, type="primary"):
                        st.session_state.manual_logout = False
                        st.session_state.authenticated = False
                        st.query_params.clear() 
                        authenticator.login()
                else:
                    user_info = st.session_state.get('user_info')
                    if user_info:
                        st.session_state.manual_logout = False
                        st.query_params.clear()
                        
                        email = user_info.get('email')
                        name = user_info.get('name', user_info.get('given_name', email.split('@')[0]))
                        
                        users = load_users()
                        username = None
                        for uname, udata in users.items():
                            if udata.get("email") == email:
                                username = uname
                                break
                        
                        if not username:
                            username = email.split("@")[0]
                            users[username] = {
                                "name": name,
                                "email": email,
                                "status": "active",
                                "created_at": datetime.now().isoformat(),
                                "last_login": datetime.now().isoformat()
                            }
                            save_users(users)
                        
                        st.session_state.authenticated = True
                        st.session_state.current_user = username
                        st.session_state.is_admin = False
                        st.rerun()


def logout():
    # Call Google logout if applicable
    authenticator = get_google_authenticator()
    if authenticator:
        try:
            authenticator.logout()
        except:
            pass

    # Clear everything!
    st.session_state.clear()
        
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.is_admin = False
    st.session_state.manual_logout = True
    
    # Set query param to ensure next run knows we just logged out
    st.query_params.logout = "true"
    
    st.rerun()


def admin_panel():
    st.title("Admin Panel")

    tab1, tab2, tab3 = st.tabs(["User Management", "Chat Management", "Settings"])

    with tab1:
        st.subheader("User Management")

        users = load_users()

        if users:
            for username, user_data in users.items():
                col1, col2, col3, col4 = st.columns([2, 1.5, 1, 1])

                with col1:
                    st.write(f"**{user_data['name']}** ({username})")
                    st.caption(user_data['email'])
                    created_at = user_data.get('created_at', 'Unknown')
                    if created_at != 'Unknown':
                        try:
                            created_dt = datetime.fromisoformat(created_at)
                            created_at = created_dt.strftime('%m/%d/%Y %H:%M')
                        except:
                            pass
                    st.caption(f"Created: {created_at}")

                with col2:
                    status = user_data.get('status', 'active')
                    if status == 'active':
                        st.success("🟢 Active")
                    else:
                        st.error("🔴 Banned")

                with col3:
                    if user_data.get('status', 'active') == 'active':
                        if st.button("Ban", key=f"ban_{username}"):
                            users[username]['status'] = 'banned'
                            save_users(users)
                            st.success(f"User {username} has been banned")
                            st.rerun()
                    else:
                        if st.button("Unban", key=f"unban_{username}"):
                            users[username]['status'] = 'active'
                            save_users(users)
                            st.success(f"User {username} has been unbanned")
                            st.rerun()

                with col4:
                    if st.button("Delete", key=f"delete_{username}"):
                        del users[username]
                        save_users(users)
                        st.success(f"User {username} has been deleted")
                        st.rerun()

                st.divider()
        else:
            st.info("No users found")

    with tab2:
        st.subheader("Chat Management")

        global_messages = load_global_chat()

        col1, col2 = st.columns([1, 1])
        with col1:
            st.metric("Total Messages", len(global_messages))
        with col2:
            if st.button("Clear All Messages", type="secondary"):
                clear_global_chat()
                st.success("All messages cleared!")
                st.rerun()

        st.subheader("Recent Messages")
        if global_messages:
            # Show last 20 messages
            for msg in global_messages[-20:]:
                timestamp = msg.get("timestamp", "Unknown")
                user_id = msg.get("user_id", "Unknown")
                content = msg.get("content", "")

                col1, col2, col3 = st.columns([2, 3, 1])
                with col1:
                    st.text(f"[{timestamp}]")
                with col2:
                    st.text(f"{user_id}: {content[:50]}...")
                with col3:
                    if st.button("🗑️", key=f"del_msg_{msg.get('message_id', str(uuid4()))}"):
                        # Remove specific message (simplified implementation)
                        st.info("Message deletion feature can be implemented")

    with tab3:
        st.subheader("Application Settings")

        admin_settings = load_admin_settings()

        # Auto-refresh interval setting
        st.markdown("**Auto-Refresh Settings**")
        current_interval = admin_settings.get("auto_refresh_interval", 2)

        new_interval = st.slider(
            "Auto-refresh interval (seconds)",
            min_value=1,
            max_value=10,
            value=current_interval,
            step=1,
            help="How often the chat refreshes automatically for all users"
        )

        if new_interval != current_interval:
            admin_settings["auto_refresh_interval"] = new_interval
            save_admin_settings(admin_settings)
            st.success(f"Auto-refresh interval updated to {new_interval} seconds!")
            st.rerun()

        st.info(f"Current auto-refresh interval: {current_interval} seconds")

        st.markdown("---")
        st.markdown("System Information")
        st.metric("Current Refresh Rate", f"{current_interval}s")
        st.metric("Active Users", len(load_users()))
        st.metric("Total Messages", len(load_global_chat()))


def global_chat_interface():
    # Custom CSS for chat styling
    st.markdown("""
    <style>
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    .message-row-right {
        display: flex;
        justify-content: flex-end;
        width: 100%;
    }
    .message-row-left {
        display: flex;
        justify-content: flex-start;
        width: 100%;
    }
    .message-content {
        max-width: 70%;
        padding: 0.75rem;
        border-radius: 0.5rem;
        margin: 0.25rem;
        background-color: var(--background-color);
        border: 1px solid var(--border-color);
        color: var(--text-color);
    }
    .message-time {
        font-size: 0.8rem;
        color: var(--secondary-text-color);
        margin-top: 0.25rem;
    }

    /* Light mode */
    [data-theme="light"] .message-content {
        --background-color: #f8f9fa;
        --border-color: #e9ecef;
        --text-color: #333;
        --secondary-text-color: #666;
    }

    /* Dark mode */
    [data-theme="dark"] .message-content,
    .stApp[data-theme="dark"] .message-content,
    .message-content {
        background-color: #2b2b2b !important;
        border: 1px solid #404040 !important;
        color: #ffffff !important;
    }

    [data-theme="dark"] .message-time,
    .stApp[data-theme="dark"] .message-time,
    .message-time {
        color: #cccccc !important;
    }

    /* Fallback for any theme */
    @media (prefers-color-scheme: dark) {
        .message-content {
            background-color: #2b2b2b !important;
            border: 1px solid #404040 !important;
            color: #ffffff !important;
        }
        .message-time {
            color: #cccccc !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Anonymous Chat")
        st.caption("All messages are anonymous • Your messages on right, others on left")
    with col2:
        if st.button("Logout", use_container_width=True):
            logout()

    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.title("Chat Info")

        # User info
        users = load_users()
        if st.session_state.current_user in users:
            user_name = users[st.session_state.current_user]["name"]
            st.success(f"Welcome, {user_name}")
        else:
            st.success(f"Welcome, {st.session_state.current_user}")

        if st.session_state.is_admin:
            st.info("Admin Access")
            if st.button("Admin Panel", use_container_width=True):
                st.session_state.show_admin = True
                st.rerun()

        st.markdown("---")

        # Chat statistics
        global_messages = load_global_chat()
        st.metric("Total Messages", len(global_messages))
        st.metric("Online Users", len(users))

        # Admin can see auto-refresh settings, users cannot
        if st.session_state.is_admin:
            admin_settings = load_admin_settings()
            refresh_interval = admin_settings.get("auto_refresh_interval", 2)
            st.info(f"Auto-refresh: {refresh_interval}s")

        if st.button("Refresh Now"):
            st.rerun()

    # Check if user is banned
    users = load_users()
    if (st.session_state.current_user in users and
            users[st.session_state.current_user].get("status", "active") == "banned"):
        st.error("Your account has been banned. You cannot send messages.")
        st.stop()

    # Auto-refresh logic
    admin_settings = load_admin_settings()
    refresh_interval = admin_settings.get("auto_refresh_interval", 2)

    current_time = time.time()
    time_since_last_check = current_time - st.session_state.last_global_check

    if time_since_last_check >= refresh_interval:
        st.session_state.last_global_check = current_time
        st.rerun()

    # Load and display messages
    global_messages = load_global_chat()
    current_user = st.session_state.current_user

    if global_messages:
        st.subheader("")

        # Status info
        col1_status, col2_status = st.columns([2, 1])
        with col1_status:
            st.info(f" {len(global_messages)} messages • Auto-refresh: ON ({refresh_interval}s)")
        with col2_status:
            current_time_str = datetime.now().strftime("%H:%M:%S")
            st.caption(f"Last update: {current_time_str}")

        # Message display
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        # Show last 50 messages
        for message in global_messages[-50:]:
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")
            message_user = message.get("user_id", "")

            is_current_user = (message_user == current_user)

            if is_current_user:
                st.markdown(f"""
                <div class="message-row-right">
                    <div class="message-content">
                        <div><strong>You:</strong> {content}</div>
                        <div class="message-time">{timestamp}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="message-row-left">
                    <div class="message-content">
                        <div><strong>Anonymous:</strong> {content}</div>
                        <div class="message-time">{timestamp}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    else:
        st.markdown("Welcome to Anonymous Chat!")
    # Chat input (only if user is not banned)
    if global_prompt := st.chat_input("Type your message..."):
        user_message = {
            "role": "user",
            "content": global_prompt,
            "timestamp": format_message_time(),
            "message_id": str(uuid4()),
            "user_id": current_user
        }

        save_global_chat_message(user_message)
        st.session_state.last_global_check = time.time()
        st.rerun()

    # Auto-refresh at the end
    time.sleep(refresh_interval)
    st.rerun()


def main():
    initialize_session()

    # Check authentication
    if not st.session_state.authenticated:
        login_form()
        return

    # Check if admin panel should be shown
    if st.session_state.is_admin and st.session_state.get("show_admin", False):
        col1, col2 = st.columns([3, 1])
        with col1:
            pass
        with col2:
            if st.button("← Back", use_container_width=True):
                st.session_state.show_admin = False
                st.rerun()
        admin_panel()
        return

    # Show main chat interface
    global_chat_interface()


if __name__ == "__main__":
    main()