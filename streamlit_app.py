import streamlit as st
import requests
from datetime import datetime
import json

# API Base URL
API_BASE_URL = "http://localhost:8000/api/v1"

# Page config
st.set_page_config(
    page_title="BOT GPT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #1976d2;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #7b1fa2;
    }
    .sidebar-button {
        width: 100%;
        margin: 0.25rem 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'current_conversation_id' not in st.session_state:
        st.session_state.current_conversation_id = None
    if 'conversations' not in st.session_state:
        st.session_state.conversations = []
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'documents' not in st.session_state:
        st.session_state.documents = []


def create_user(username: str, email: str):
    """Create a new user."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/users",
            json={"username": username, "email": email}
        )
        if response.status_code == 201:
            return response.json()
        else:
            st.error(f"Error creating user: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None


def create_conversation(user_id: str, title: str, mode: str = "open_chat", document_ids: list = None):
    """Create a new conversation."""
    try:
        payload = {
            "user_id": user_id,
            "title": title,
            "mode": mode,
            "document_ids": document_ids or []
        }
        response = requests.post(f"{API_BASE_URL}/conversations", json=payload)
        if response.status_code == 201:
            return response.json()
        else:
            st.error(f"Error creating conversation: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None


def get_conversations(user_id: str):
    """Get all conversations for a user."""
    try:
        response = requests.get(f"{API_BASE_URL}/conversations", params={"user_id": user_id})
        if response.status_code == 200:
            return response.json()['conversations']
        return []
    except Exception as e:
        st.error(f"Error loading conversations: {str(e)}")
        return []


def get_conversation_messages(conversation_id: str):
    """Get messages for a conversation."""
    try:
        response = requests.get(f"{API_BASE_URL}/conversations/{conversation_id}")
        if response.status_code == 200:
            return response.json()['messages']
        return []
    except Exception as e:
        st.error(f"Error loading messages: {str(e)}")
        return []


def send_message(conversation_id: str, content: str):
    """Send a message and get response."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/conversations/{conversation_id}/messages",
            json={"content": content}
        )
        if response.status_code == 201:
            return response.json()
        else:
            st.error(f"Error sending message: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None


def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    try:
        response = requests.delete(f"{API_BASE_URL}/conversations/{conversation_id}")
        if response.status_code == 200:
            return True
        else:
            st.error(f"Error deleting conversation: {response.json().get('detail', 'Unknown error')}")
            return False
    except Exception as e:
        st.error(f"Error deleting conversation: {str(e)}")
        return False


def upload_document(user_id: str, file):
    """Upload a document."""
    try:
        files = {"file": file}
        data = {"user_id": user_id}
        response = requests.post(f"{API_BASE_URL}/documents", files=files, data=data)
        if response.status_code == 201:
            return response.json()
        else:
            st.error(f"Error uploading document: {response.json().get('detail', 'Unknown error')}")
            return None
    except Exception as e:
        st.error(f"Error uploading document: {str(e)}")
        return None


def get_documents(user_id: str):
    """Get all documents for a user."""
    try:
        response = requests.get(f"{API_BASE_URL}/documents", params={"user_id": user_id})
        if response.status_code == 200:
            return response.json()['documents']
        return []
    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")
        return []


# Initialize session state
init_session_state()

# Header
st.markdown('<div class="main-header">🤖 BOT GPT</div>', unsafe_allow_html=True)
st.markdown("---")

# Login/Registration
if not st.session_state.user_id:
    st.subheader("Welcome! Please log in or register")

    col1, col2 = st.columns(2)

    with col1:
        st.write("### Register")
        reg_username = st.text_input("Username", key="reg_username")
        reg_email = st.text_input("Email", key="reg_email")
        if st.button("Register", key="register_btn"):
            if reg_username and reg_email:
                user = create_user(reg_username, reg_email)
                if user:
                    st.session_state.user_id = user['id']
                    st.session_state.username = user['username']
                    st.success("Registration successful!")
                    st.rerun()
            else:
                st.warning("Please fill in all fields")

    with col2:
        st.write("### Quick Demo Login")
        if st.button("Use Demo Account", key="demo_btn"):
            # Create demo user
            demo_username = f"demo_user_{datetime.now().strftime('%H%M%S')}"
            user = create_user(demo_username, f"{demo_username}@demo.com")
            if user:
                st.session_state.user_id = user['id']
                st.session_state.username = user['username']
                st.success(f"Logged in as {demo_username}")
                st.rerun()

else:
    # Sidebar
    with st.sidebar:
        st.write(f"### 👤 {st.session_state.username}")
        st.markdown("---")

        # New Chat Button
        if st.button("➕ New Chat", use_container_width=True):
            new_conv = create_conversation(
                st.session_state.user_id,
                f"New Chat {datetime.now().strftime('%H:%M')}",
                mode="open_chat"
            )
            if new_conv:
                st.session_state.current_conversation_id = new_conv['id']
                st.session_state.messages = []
                st.session_state.conversations = get_conversations(st.session_state.user_id)
                st.rerun()

        # Document Upload
        with st.expander("📄 Upload Document (RAG)"):
            uploaded_file = st.file_uploader("Choose PDF", type=['pdf'], key="file_uploader")
            if uploaded_file and st.button("Upload", key="upload_btn"):
                with st.spinner("Processing document..."):
                    doc = upload_document(st.session_state.user_id, uploaded_file)
                    if doc:
                        st.success(f"Uploaded: {doc['filename']}")
                        st.session_state.documents = get_documents(st.session_state.user_id)

            # Show uploaded documents
            st.session_state.documents = get_documents(st.session_state.user_id)
            if st.session_state.documents:
                st.write("**Your Documents:**")
                for doc in st.session_state.documents:
                    st.write(f"- {doc['filename']} ({doc['chunk_count']} chunks)")

                # New Grounded Chat
                selected_docs = st.multiselect(
                    "Select documents",
                    options=[doc['id'] for doc in st.session_state.documents],
                    format_func=lambda x: next(d['filename'] for d in st.session_state.documents if d['id'] == x)
                )
                if selected_docs and st.button("Start RAG Chat", key="rag_chat_btn"):
                    new_conv = create_conversation(
                        st.session_state.user_id,
                        f"RAG Chat {datetime.now().strftime('%H:%M')}",
                        mode="grounded",
                        document_ids=selected_docs
                    )
                    if new_conv:
                        st.session_state.current_conversation_id = new_conv['id']
                        st.session_state.messages = []
                        st.session_state.conversations = get_conversations(st.session_state.user_id)
                        st.rerun()

        st.markdown("---")
        st.write("### 💬 Conversations")

        # Load conversations
        st.session_state.conversations = get_conversations(st.session_state.user_id)

        # Display conversations
        for conv in st.session_state.conversations:
            col1, col2 = st.columns([4, 1])

            with col1:
                conv_title = conv['title'][:30] + "..." if len(conv['title']) > 30 else conv['title']
                mode_emoji = "📚" if conv['mode'] == "grounded" else "💭"
                if st.button(f"{mode_emoji} {conv_title}", key=f"conv_{conv['id']}", use_container_width=True):
                    st.session_state.current_conversation_id = conv['id']
                    st.session_state.messages = get_conversation_messages(conv['id'])
                    st.rerun()

            with col2:
                if st.button("🗑️", key=f"del_{conv['id']}"):
                    if delete_conversation(conv['id']):
                        if st.session_state.current_conversation_id == conv['id']:
                            st.session_state.current_conversation_id = None
                            st.session_state.messages = []
                        st.session_state.conversations = get_conversations(st.session_state.user_id)
                        st.rerun()

        # Logout
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.current_conversation_id = None
            st.session_state.conversations = []
            st.session_state.messages = []
            st.rerun()

    # Main chat area
    if st.session_state.current_conversation_id:
        # Display messages
        for msg in st.session_state.messages:
            with st.container():
                if msg['role'] == 'user':
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>You:</strong><br>{msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
                elif msg['role'] == 'assistant':
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <strong>🤖 BOT GPT:</strong><br>{msg['content']}
                    </div>
                    """, unsafe_allow_html=True)

        # Chat input
        user_input = st.chat_input("Type your message here...")

        if user_input:
            # Send message
            with st.spinner("Thinking..."):
                result = send_message(st.session_state.current_conversation_id, user_input)
                if result:
                    # Update messages
                    st.session_state.messages.append(result['user_message'])
                    st.session_state.messages.append(result['assistant_message'])
                    st.rerun()

    else:
        # No conversation selected
        st.info("👈 Select a conversation or create a new chat to get started!")
        st.markdown("""
        ### Features:
        - **💭 Open Chat**: General conversation with the AI
        - **📚 RAG Mode**: Chat with your documents
        - **🗑️ Delete**: Remove old conversations
        - **📄 Upload**: Add PDF documents for grounded conversations
        """)
