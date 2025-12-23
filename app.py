import streamlit as st
import json
import os
from datetime import datetime
from uuid import uuid4
import time
import hashlib

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
    try:
        if not os.path.exists("database"):
            os.makedirs("database")
        if os.path.exists("database/users.json"):
            with open("database/users.json", "r") as f:
                return json.load(f)
        return {}
    except Exception:
        return {}


def load_admin_settings():
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
    try:
        if not os.path.exists("database"):
            os.makedirs("database")
        with open("database/admin_settings.json", "w") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass


def save_users(users):
    try:
        if not os.path.exists("database"):
            os.makedirs("database")
        with open("database/users.json", "w") as f:
            json.dump(users, f, indent=2)
    except Exception:
        pass


def save_global_chat_message(message):
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
    try:
        global_chat_file = "database/global_chat.json"
        if os.path.exists(global_chat_file):
            with open(global_chat_file, "w") as f:
                json.dump({"messages": []}, f, indent=2)
    except Exception:
        pass


def initialize_session():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "current_user" not in st.session_state:
        st.session_state.current_user = None
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "last_global_check" not in st.session_state:
        st.session_state.last_global_check = time.time()


def login_form():
    st.markdown("""
        <div style='text-align: center; margin-bottom: 2rem;'>
            <h1>🌐 Anonymous Chat</h1>
            <p style='color: #666; font-size: 1.1rem;'>Please login or signup to access Anonymous Chat</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2, tab3 = st.tabs(["Login", "Sign Up", "Admin"])

        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter username")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                login_button = st.form_submit_button("Login", use_container_width=True)

                if login_button:
                    users = load_users()
                    if username in users:
                        stored_password = users[username]["password"]
                        if stored_password == hash_password(password):
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
                            st.error("Invalid username or password")
                    else:
                        st.error("Invalid username or password")

        with tab2:
            with st.form("signup_form"):
                new_name = st.text_input("Full Name", placeholder="Enter your full name")
                new_email = st.text_input("Email", placeholder="Enter your email")
                new_username = st.text_input("Username", placeholder="Choose a username")
                new_password = st.text_input("Password", type="password", placeholder="Choose a password")
                signup_button = st.form_submit_button("Sign Up", use_container_width=True)

                if signup_button:
                    if new_name and new_email and new_username and new_password:
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
                            st.success("Account created successfully! Logging you in...")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Username already exists")
                    else:
                        st.error("Please fill in all fields")

        with tab3:
            with st.form("admin_form"):
                admin_username = st.text_input("Admin Username", placeholder="Enter admin username")
                admin_password = st.text_input("Admin Password", type="password", placeholder="Enter admin password")
                admin_login_button = st.form_submit_button("Admin Login", use_container_width=True)

                if admin_login_button:
                    if admin_username == "Admin" and admin_password == "Shuvo@123":
                        st.session_state.authenticated = True
                        st.session_state.current_user = "Admin"
                        st.session_state.is_admin = True
                        st.success("Admin login successful! Redirecting...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid admin credentials")


def logout():
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.is_admin = False
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
        st.caption("Your messages on right, others on left")
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
                        <div>{content}</div>
                        <div class="message-time">{timestamp}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="message-row-left">
                    <div class="message-content">
                        <div><strong>{message_user}:</strong> {content}</div>
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