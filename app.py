import hashlib
from io import BytesIO

import streamlit as st
from pypdf import PdfReader

from twin import chat


st.set_page_config(
    page_title="Build Your Digital Twin",
    page_icon="🤖",
)

st.title("Build Your Digital Twin")

st.write(
    """
    Create an AI version of yourself that can answer questions
    about your career, skills, and experience.
    """
)


st.subheader("Step 1: Upload your information")
with st.expander("What files should I upload?", expanded=True):
    st.markdown(
        """
        **1. Resume PDF**

        Upload your current resume as a PDF.

        It should ideally include:
        - Work experience
        - Education
        - Skills
        - Projects
        - Certifications
        - Achievements

        **2. Supporting TXT document**

        Upload a plain text file (`.txt`) with extra information
        you want your digital twin to know.

        You can include:
        - Career goals
        - Important achievements
        - Personal professional stories
        - Work preferences
        - Information missing from your resume
        - How you want your digital twin to describe you

        Example supporting text:

        `I am passionate about AI and software development.
        I enjoy solving practical problems and building useful products.
        My long-term goal is to become an AI engineer.`
        """
    )


resume_file = st.file_uploader(
    "Upload your resume (PDF)",
    type=["pdf"],
    help="Upload a PDF containing your professional background.",
)

supporting_file = st.file_uploader(
    "Upload your supporting information (TXT)",
    type=["txt"],
    help="Upload a plain text file with additional information.",
)


if resume_file and supporting_file:
    try:
        # Extract resume text
        reader = PdfReader(BytesIO(resume_file.getvalue()))

        resume_text = ""

        for page in reader.pages:
            resume_text += page.extract_text() or ""
            resume_text += "\n"

        # Extract supporting text
        supporting_text = supporting_file.getvalue().decode(
            "utf-8",
            errors="replace",
        )

        # Combine the uploaded data
        twin_context = f"""
        RESUME:

        {resume_text}

        SUPPORTING INFORMATION:

        {supporting_text}
        """

        # Create a fingerprint for these uploaded files
        file_hash = hashlib.sha256(
            resume_file.getvalue() + supporting_file.getvalue()
        ).hexdigest()

        # Reset chat when new files are uploaded
        if st.session_state.get("file_hash") != file_hash:

            st.session_state.file_hash = file_hash
            st.session_state.twin_context = twin_context
            st.session_state.history = []
            st.session_state.messages = []

        st.success("Your digital twin is ready!")

        st.subheader("Step 2: Chat with your digital twin")

        st.caption(
            "Ask questions about the person's career, skills, "
            "experience, or background."
        )

        # Display previous messages
        for message in st.session_state.messages:

            with st.chat_message(message["role"]):
                st.write(message["content"])


        # Chat input
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

            # Get response
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
                        st.error(f"{answer}\n\n{e}")

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