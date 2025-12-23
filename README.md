# 🌐 Anonymous Chat

A real-time anonymous chat application built with **Python** and **Streamlit**. This project provides a simple yet powerful interface for users to communicate globally, complete with user authentication and an admin panel for management.

## ✨ Features

*   **🔐 User Validations**: Secure sign-up and login system using hashed passwords.
*   **💬 Anonymous Chat**: Real-time messaging interface accessible to all registered users.
*   **💾 Message Persistence**: Messages are stored locally, ensuring conversations aren't lost on reload (persists last 1000 messages).
*   **⚡ Auto-Refresh**: Chat interface automatically updates to show new messages.
*   **🛠️ Admin Panel**: Dedicated interface for system administrators to manage settings (e.g., chat refresh rate).
*   **📱 Responsive Design**: Built with Streamlit's responsive layout adaptation.

## 🚀 Getting Started

Follow these steps to set up and run the project locally.

### Prerequisites

*   Python 3.8 or higher
*   pip (Python package manager)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/sohanur-shuvo/anonymous-chat.git
    cd anonymous-chat
    ```

2.  **Create a virtual environment (optional but recommended):**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### ▶️ Usage

1.  **Run the application:**
    ```bash
    streamlit run app.py
    ```

2.  **Access the app:**
    The application will open automatically in your default web browser. If not, utilize the URL provided in the terminal (usually `http://localhost:8501`).

3.  **Default Admin credentials:**
    *   *Note: If you need to set up an admin account, check the `load_users` functions or the database initialization logic.*

## 📂 Project Structure

*   `app.py`: The main entry point and logic for the full feature application.
*   `gc.py`: A lightweight version of the chat interface.
*   `database/`: Directory where JSON files for `users`, `messages`, and `settings` are stored (created automatically).

## 🛠️ Technologies Used

*   **[Streamlit](https://streamlit.io/)**: For the frontend user interface.
*   **Python**: Backend logic.
*   **JSON**: Lightweight local database.