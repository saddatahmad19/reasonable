import streamlit as st
from utils import validate_markdown_file, batch_similar_tasks, optimize_context_for_task, format_single_task_result_for_export
from agent_system import AgentSystem
from llm_config import LLMConfig

# Sidebar navigation
with st.sidebar:
    st.header("Navigation")
    st.page_link("main.py", label="🏠 Main")
    st.page_link("pages/Chat.py", label="💬 Chat")
    st.page_link("pages/TaskProcessor.py", label="📝 Task Processor", disabled=True)
    st.page_link("pages/Config.py", label="⚙️ Config")

st.set_page_config(page_title="Task Processor", page_icon="📝")
st.title("📝 Task Processor")

# Check if LLM is configured
agent_system = st.session_state.get("agent_system", None)
llm_config = getattr(agent_system, "config", None)

if not agent_system or not llm_config:
    st.warning("Please configure your LLM provider in the Config page before using the Task Processor.")
    st.stop()

# File upload section
st.header("📁 Upload Context Files")
if 'uploaded_context' not in st.session_state:
    st.session_state.uploaded_context = ""

uploaded_files = st.file_uploader(
    "Upload Markdown files (.md)",
    type=['md'],
    accept_multiple_files=True,
    help="Upload one or more markdown files that will serve as context for answering tasks"
)

if uploaded_files:
    context_content = ""
    for uploaded_file in uploaded_files:
        if validate_markdown_file(uploaded_file):
            content = uploaded_file.read().decode('utf-8')
            context_content += f"\n## {uploaded_file.name}\n\n{content}\n\n"
        else:
            st.error(f"❌ Invalid file: {uploaded_file.name}")
    if context_content:
        st.session_state.uploaded_context = context_content
        st.success(f"✅ Successfully loaded {len(uploaded_files)} file(s)")
        with st.expander("📖 Context Preview"):
            st.markdown(context_content[:1000] + "..." if len(context_content) > 1000 else context_content)

# System prompt input
if 'system_prompt' not in st.session_state:
    st.session_state.system_prompt = "You are an intelligent assistant that helps users complete tasks using the provided context."
st.header("🛠️ System Prompt (Optional)")
st.session_state.system_prompt = st.text_area(
    "Set a custom system prompt for this run:",
    value=st.session_state.system_prompt,
    height=80
)

# Task input section
st.header("📝 Task Input")
if 'task_boxes' not in st.session_state:
    st.session_state.task_boxes = []
if 'task_statuses' not in st.session_state:
    st.session_state.task_statuses = []
if 'task_results' not in st.session_state:
    st.session_state.task_results = []
if 'task_report_names' not in st.session_state:
    st.session_state.task_report_names = []
if 'current_task_idx' not in st.session_state:
    st.session_state.current_task_idx = 0
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'stopped' not in st.session_state:
    st.session_state.stopped = False

# Task input UI
num_boxes = max(len(st.session_state.task_boxes), 1)
for i in range(num_boxes):
    with st.container():
        st.markdown(f"### Task {i+1}")
        task_text = st.text_area(f"Task/Question {i+1}", value=st.session_state.task_boxes[i] if i < len(st.session_state.task_boxes) else "", key=f"task_text_{i}")
        if i >= len(st.session_state.task_boxes):
            st.session_state.task_boxes.append(task_text)
            st.session_state.task_statuses.append('pending')
            st.session_state.task_results.append(None)
            st.session_state.task_report_names.append("")
        else:
            st.session_state.task_boxes[i] = task_text
        report_name = st.text_input(f"Report filename (with or without .md) for Task {i+1}", value=st.session_state.task_report_names[i], key=f"report_name_{i}")
        st.session_state.task_report_names[i] = report_name
        # Status display
        status = st.session_state.task_statuses[i]
        st.markdown(f"**Status:** {status.capitalize()}")
        # Show result if completed
        if status == 'completed' and st.session_state.task_results[i]:
            st.markdown("**Answer:**")
            st.markdown(st.session_state.task_results[i]['answer'])
        elif status == 'skipped':
            st.info("Task was skipped.")
        elif status == 'stopped':
            st.warning("Task was stopped.")
        # Download button for completed tasks
        if status == 'completed' and st.session_state.task_results[i]:
            filename = report_name if report_name.endswith('.md') else report_name + '.md'
            markdown_content = format_single_task_result_for_export(st.session_state.task_results[i])
            st.download_button(
                label="Download Markdown Report",
                data=markdown_content,
                file_name=filename,
                mime="text/markdown",
                key=f"download_{i}"
            )

# Add/Remove task boxes
col_add, col_remove = st.columns(2)
with col_add:
    if st.button("➕ Add Task"):
        st.session_state.task_boxes.append("")
        st.session_state.task_statuses.append('pending')
        st.session_state.task_results.append(None)
        st.session_state.task_report_names.append("")
        st.rerun()
with col_remove:
    if num_boxes > 1 and st.button("➖ Remove Last Task"):
        st.session_state.task_boxes.pop()
        st.session_state.task_statuses.pop()
        st.session_state.task_results.pop()
        st.session_state.task_report_names.pop()
        st.rerun()

# --- Pipeline Control Panel ---
st.markdown("---")
st.header("🚦 Pipeline Controls")
col_start, col_stop, col_skip, col_clear = st.columns(4)
with col_start:
    if not st.session_state.processing and any(s == 'pending' for s in st.session_state.task_statuses):
        if st.button("▶️ Start Pipeline", key="start_pipeline"):
            st.session_state.processing = True
            # Start from first pending task
            try:
                st.session_state.current_task_idx = st.session_state.task_statuses.index('pending')
            except ValueError:
                st.session_state.current_task_idx = 0
            st.session_state.stopped = False
            st.rerun()
with col_stop:
    if st.session_state.processing:
        if st.button("⏹️ Stop Pipeline", key="stop_pipeline"):
            st.session_state.stopped = True
            st.session_state.processing = False
            # Mark current running task as stopped if running
            idx = st.session_state.current_task_idx
            if idx < len(st.session_state.task_statuses) and st.session_state.task_statuses[idx] == 'running':
                st.session_state.task_statuses[idx] = 'stopped'
            st.rerun()
with col_skip:
    if st.session_state.processing:
        if st.button("⏭️ Skip Task", key="skip_task"):
            idx = st.session_state.current_task_idx
            if idx < len(st.session_state.task_statuses):
                st.session_state.task_statuses[idx] = 'skipped'
                st.session_state.processing = False
                st.session_state.current_task_idx = idx + 1
                # If next task is pending, auto-start it
                if st.session_state.current_task_idx < len(st.session_state.task_boxes) and st.session_state.task_statuses[st.session_state.current_task_idx] == 'pending':
                    st.session_state.processing = True
                st.rerun()
with col_clear:
    if st.button("🗑️ Clear", key="clear_pipeline"):
        # Reset all pipeline states except uploaded files
        st.session_state.task_boxes = [""]
        st.session_state.task_statuses = ['pending']
        st.session_state.task_results = [None]
        st.session_state.task_report_names = [""]
        st.session_state.current_task_idx = 0
        st.session_state.processing = False
        st.session_state.stopped = False
        # Do not clear uploaded_context
        st.rerun()

# --- Sequential processing logic (pipeline) ---
if st.session_state.processing and not st.session_state.stopped:
    idx = st.session_state.current_task_idx
    if idx < len(st.session_state.task_boxes):
        if st.session_state.task_statuses[idx] in ['pending', 'running']:
            st.session_state.task_statuses[idx] = 'running'
            task = st.session_state.task_boxes[idx]
            report_name = st.session_state.task_report_names[idx]
            optimized_context = optimize_context_for_task(st.session_state.uploaded_context, task)
            # Call agent_system with system prompt
            results = agent_system.process_tasks(
                tasks=[task],
                context=optimized_context,
                session_id=f"task_{idx}_session",
                system_prompt=st.session_state.system_prompt
            )
            st.session_state.task_results[idx] = results[0]
            st.session_state.task_statuses[idx] = 'completed'
            st.session_state.processing = False
            st.session_state.current_task_idx = idx + 1
            # If next task is pending, auto-start it
            if st.session_state.current_task_idx < len(st.session_state.task_boxes) and st.session_state.task_statuses[st.session_state.current_task_idx] == 'pending':
                st.session_state.processing = True
            st.rerun()

# Results display
if 'task_results' not in st.session_state:
    st.session_state.task_results = []
if st.session_state.task_results:
    st.header(" Task Results")
    completed_results = [r for r in st.session_state.task_results if r is not None]
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tasks", len(completed_results))
    with col2:
        avg_confidence = sum(r.get('confidence', 0) for r in completed_results) / len(completed_results) if completed_results else 0
        st.metric("Avg Confidence", f"{avg_confidence:.1%}")
    with col3:
        total_tokens = sum(r.get('tokens_used', 0) for r in completed_results)
        st.metric("Total Tokens", total_tokens)
    for i, result in enumerate(completed_results, 1):
        with st.expander(f"📝 Task {i}: {result['task'][:50]}..."):
            st.markdown("**Task:**")
            st.info(result['task'])
            st.markdown("**Answer:**")
            st.markdown(result['answer'])
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Confidence", f"{result.get('confidence', 0):.1%}")
            with col2:
                st.metric("Tokens Used", result.get('tokens_used', 0))
            with col3:
                st.metric("Processing Time", f"{result.get('processing_time', 0):.2f}s")
            if result.get('sources'):
                st.markdown("**Sources Used:**")
                for source in result['sources']:
                    st.markdown(f"- {source}")
            if result.get('reasoning_steps'):
                with st.expander("🧠 View Reasoning Steps"):
                    for step in result['reasoning_steps']:
                        st.markdown(f"**{step['step']}:** {step['description']}")
            # --- Report Generation UI ---
            report_key = f"report_{i}"  # Unique key for each report UI
            if st.button("📝 Generate Report?", key=report_key):
                st.session_state[f"show_report_input_{i}"] = True
            if st.session_state.get(f"show_report_input_{i}", False):
                filename = st.text_input("Enter filename for report (with or without .md):", key=f"filename_{i}")
                if filename:
                    if not filename.endswith(".md"):
                        filename += ".md"
                    markdown_content = format_single_task_result_for_export(result)
                    st.download_button(
                        label="Download Markdown Report",
                        data=markdown_content,
                        file_name=filename,
                        mime="text/markdown",
                        key=f"download_{i}"
                    )
    st.markdown("---")
    if st.button("🗑️ Clear Results"):
        st.session_state.task_results = []
        st.rerun() 