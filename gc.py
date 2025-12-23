import streamlit as st
import json
import os
from datetime import datetime
from uuid import uuid4
import time

# Page configuration
st.set_page_config(
    page_title="Anonymous Chat",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)


def format_message_time():
    return datetime.now().strftime("%H:%M:%S")


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
    if "current_user" not in st.session_state:
        st.session_state.current_user = f"User_{str(uuid4())[:8]}"
    if "last_global_check" not in st.session_state:
        st.session_state.last_global_check = time.time()


def main():
    initialize_session()

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
        st.title("🌐 Anonymous Chat")
        st.caption("Chat with all users in real-time • Your messages on right, others on left")
    with col2:
        if st.button("Clear Chat", use_container_width=True):
            clear_global_chat()
            st.success("Chat cleared!")
            st.rerun()

    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.title("Settings")

        # User identification
        current_user = st.text_input("Your Username", value=st.session_state.current_user)
        if current_user != st.session_state.current_user:
            st.session_state.current_user = current_user
            st.rerun()

        st.markdown("---")

        # Chat statistics
        global_messages = load_global_chat()
        st.metric("Total Messages", len(global_messages))

        # Auto-refresh control
        auto_refresh = st.checkbox("Auto-refresh (3s)", value=True)

        if st.button("Refresh Now"):
            st.rerun()

    # Auto-refresh logic
    current_time = time.time()
    time_since_last_check = current_time - st.session_state.last_global_check

    if auto_refresh and time_since_last_check >= 3:
        st.session_state.last_global_check = current_time
        st.rerun()

    # Load and display messages
    global_messages = load_global_chat()
    current_user = st.session_state.current_user

    if global_messages:
        st.subheader("💬 Global Conversation")

        # Status info
        col1_status, col2_status = st.columns([2, 1])
        with col1_status:
            refresh_status = "ON" if auto_refresh else "OFF"
            st.info(f"📊 {len(global_messages)} messages • 🔄 Auto-refresh: {refresh_status}")
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
                        <div class="message-time">🕐 {timestamp}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="message-row-left">
                    <div class="message-content">
                        <div><strong>{message_user}:</strong> {content}</div>
                        <div class="message-time">🕐 {timestamp}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    else:
        st.info("🌟 Be the first to start the global conversation!")
        st.markdown("**Welcome to Anonymous Chat!**")
        st.markdown("- Chat with all users in real-time")
        st.markdown("- Your messages appear on the right")
        st.markdown("- Others' messages appear on the left")
        st.markdown("- Messages refresh automatically every 3 seconds")

    # Chat input
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
    if auto_refresh:
        time.sleep(3)
        st.rerun()


if __name__ == "__main__":
    main()