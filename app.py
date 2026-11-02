import hashlib
from io import BytesIO
from pathlib import Path

import streamlit as st
from pypdf import PdfReader

from twin import chat


# --------------------------------------------------
# Page setup
# --------------------------------------------------

st.set_page_config(
    page_title="Digital Twin",
    page_icon="🤖",
    layout="centered",
)

BASE_DIR = Path(__file__).resolve().parent

USER_DETAILS_FILE = BASE_DIR / "user_details.txt"
UNKNOWN_QUESTIONS_FILE = BASE_DIR / "unknown_questions.txt"


# --------------------------------------------------
# Sidebar navigation
# --------------------------------------------------

page = st.sidebar.radio(
    "Navigation",
    ["Digital Twin", "Admin Centre"],
)


# ==================================================
# ADMIN CENTRE
# ==================================================

if page == "Admin Centre":

    st.title("🔐 Admin Centre")
    st.write("Download visitor details and unanswered questions.")

    # Read admin password from Streamlit Cloud Secrets
    admin_password = st.secrets.get("ADMIN_PASSWORD", "")

    if not admin_password:
        st.error(
            "Admin password is not configured. "
            "Add ADMIN_PASSWORD to your Streamlit secrets."
        )
        st.stop()

    # --------------------------------------------------
    # Admin login
    # --------------------------------------------------

    if not st.session_state.get("admin_authenticated", False):

        with st.form("admin_login_form"):

            entered_password = st.text_input(
                "Admin password",
                type="password",
            )

            login_clicked = st.form_submit_button("Login")

        if login_clicked:

            if entered_password == admin_password:
                st.session_state.admin_authenticated = True
                st.rerun()

            else:
                st.error("Incorrect password.")

        st.stop()

    # --------------------------------------------------
    # Admin dashboard
    # --------------------------------------------------

    st.success("Admin access granted.")

    if st.button("Logout"):
        st.session_state.admin_authenticated = False
        st.rerun()

    st.divider()

    # --------------------------------------------------
    # Download visitor details
    # --------------------------------------------------

    st.subheader("Visitor Details")

    if USER_DETAILS_FILE.exists():

        user_data = USER_DETAILS_FILE.read_text(
            encoding="utf-8"
        )

        st.caption(
            f"File size: {len(user_data)} characters"
        )

        st.download_button(
            label="Download user_details.txt",
            data=user_data,
            file_name="user_details.txt",
            mime="text/plain",
            key="download_user_details",
        )

    else:
        st.info("No visitor details have been saved yet.")

    st.divider()

    # --------------------------------------------------
    # Download unanswered questions
    # --------------------------------------------------

    st.subheader("Unanswered Questions")

    if UNKNOWN_QUESTIONS_FILE.exists():

        question_data = UNKNOWN_QUESTIONS_FILE.read_text(
            encoding="utf-8"
        )

        st.caption(
            f"File size: {len(question_data)} characters"
        )

        st.download_button(
            label="Download unknown_questions.txt",
            data=question_data,
            file_name="unknown_questions.txt",
            mime="text/plain",
            key="download_unknown_questions",
        )

    else:
        st.info("No unanswered questions have been saved yet.")

    st.stop()


# ==================================================
# DIGITAL TWIN
# ==================================================

st.title("🤖 Build Your Digital Twin")

st.write(
    """
    Upload your professional information and create an AI digital twin
    that can answer questions about your career, skills, and experience.
    """
)


# --------------------------------------------------
# Explain upload requirements
# --------------------------------------------------

st.subheader("Step 1: Upload your information")

with st.expander("What files should I upload?", expanded=True):

    st.markdown(
        """
        **Resume PDF**

        Upload your current resume as a PDF.

        It should ideally include:
        - Work experience
        - Education
        - Skills
        - Projects
        - Certifications
        - Achievements

        **Supporting TXT document**

        Upload a plain text file (`.txt`) with extra information
        you want your digital twin to know.

        You can include:
        - Career goals
        - Important achievements
        - Professional stories
        - Work preferences
        - Information missing from your resume
        - How you want your digital twin to describe you

        **Example supporting text:**

        `I am passionate about AI and software development.
        I enjoy solving practical problems and building useful products.
        My long-term goal is to become an AI engineer.`
        """
    )


# --------------------------------------------------
# File uploaders
# --------------------------------------------------

resume_file = st.file_uploader(
    "Upload your resume (PDF)",
    type=["pdf"],
    help="Upload a PDF containing your professional background.",
)

supporting_file = st.file_uploader(
    "Upload your supporting information (TXT)",
    type=["txt"],
    help="Upload a text file containing additional information.",
)


# --------------------------------------------------
# Process uploaded files
# --------------------------------------------------

if resume_file and supporting_file:

    try:

        # Extract resume text
        reader = PdfReader(
            BytesIO(resume_file.getvalue())
        )

        resume_text = ""

        for page_content in reader.pages:
            resume_text += page_content.extract_text() or ""
            resume_text += "\n"

        # Extract supporting text
        supporting_text = supporting_file.getvalue().decode(
            "utf-8",
            errors="replace",
        )

        # Combine uploaded information
        twin_context = f"""
        RESUME:

        {resume_text}

        SUPPORTING INFORMATION:

        {supporting_text}
        """

        # Fingerprint the uploaded files
        file_hash = hashlib.sha256(
            resume_file.getvalue()
            + supporting_file.getvalue()
        ).hexdigest()

        # Reset chat when uploaded files change
        if st.session_state.get("file_hash") != file_hash:

            st.session_state.file_hash = file_hash
            st.session_state.twin_context = twin_context
            st.session_state.history = []
            st.session_state.messages = []

        st.success("Your digital twin is ready!")

        st.subheader("Step 2: Chat with your digital twin")

        st.caption(
            "Ask questions about the person's career, skills, "
            "experience, or professional background."
        )

        # --------------------------------------------------
        # Initialize chat state
        # --------------------------------------------------

        if "history" not in st.session_state:
            st.session_state.history = []

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # --------------------------------------------------
        # Display conversation
        # --------------------------------------------------

        for message in st.session_state.messages:

            with st.chat_message(message["role"]):
                st.write(message["content"])

        # --------------------------------------------------
        # Chat input
        # --------------------------------------------------

        if prompt := st.chat_input("Ask your digital twin..."):

            # Display user message
            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": prompt,
                }
            )

            with st.chat_message("user"):
                st.write(prompt)

            # Get assistant response
            with st.chat_message("assistant"):

                with st.spinner("Thinking..."):

                    try:

                        answer = chat(
                            prompt,
                            st.session_state.history,
                            st.session_state.twin_context,
                        )

                        st.write(answer)

                    except Exception as e:

                        answer = "Sorry, something went wrong."

                        st.error(
                            f"{answer}\n\nError: {e}"
                        )

            # Save assistant response
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

    except Exception as e:

        st.error(
            "I couldn't read those files. "
            "Please check that your PDF and TXT files are valid."
        )

        st.exception(e)

else:

    st.info(
        "Upload both your resume PDF and supporting TXT file "
        "to start chatting."
    )