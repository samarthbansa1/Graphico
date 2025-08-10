import streamlit as st
import asyncio
import os
import re
import subprocess
import sys
from pathlib import Path
from team.analyzer_gpt import getDataAnalyzerTeam
from agents.Code_Executor_Agent import getCodeExecutorAgent

from autogen_agentchat.messages import TextMessage
from autogen_agentchat.base import TaskResult

from config.openai_model_client import get_model_client
from config.docker_utils import getDockerCommandLineExecutor,start_docker_container,stop_docker_container

st.title('Graphico - Digital Data Analyzer')

# Ensure temp directory exists at the repository root (align with main.py behavior)
REPO_ROOT = Path(__file__).resolve().parent.parent
TEMP_DIR = REPO_ROOT / 'temp'
TEMP_DIR.mkdir(parents=True, exist_ok=True)

uploaded_file = st.file_uploader('Upload your CSV file',type='csv')

if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'autogen_team_state' not in st.session_state:
    st.session_state.autogen_team_state = None

# task = st.text_input("Enter your task",value = 'Can you give me number of columns in my data (file is data.csv)')

task = st.chat_input("Enter your Task.")

async def run_analyzer_gpt(docker,openai_model_client,task):

    try:
        await start_docker_container(docker)
        team = getDataAnalyzerTeam(docker,openai_model_client)

        if st.session_state.autogen_team_state is not None:
            await team.load_state(st.session_state.autogen_team_state)
        
        
        streamed_contents = []
        async for message in team.run_stream(task=task):
            if isinstance(message,TextMessage):
                print(msg := f"{message.source} : {message.content}")
                # yield msg
                if msg.startswith('user'):
                    with st.chat_message('user',avatar='👨'):
                        st.markdown(msg)
                elif msg.startswith('Data_Analyzer_Agent'):
                    with st.chat_message('Data Analyst',avatar='🤖'):
                        st.markdown(msg)                
                elif msg.startswith('CodeExecutor'):
                    with st.chat_message('Code Runner',avatar='🧑🏻‍💻'):
                        st.markdown(msg)
                st.session_state.messages.append(msg)
                streamed_contents.append(str(message.content))

            elif isinstance(message,TaskResult):
                print(msg:= f"Stop Reason: {message.stop_reason}")
                # yield msg
                st.markdown(msg)
                st.session_state.messages.append(msg)

        st.session_state.autogen_team_state = await team.save_state()

        # Fallback: if no output.png, try to extract and execute the last Python code block
        output_png = TEMP_DIR / 'output.png'
        if not output_png.exists():
            combined = "\n\n".join(streamed_contents)
            code_blocks = re.findall(r"```python\s*([\s\S]*?)```", combined, flags=re.IGNORECASE)
            if not code_blocks:
                # also match generic fenced block if language tag omitted
                code_blocks = re.findall(r"```\s*([\s\S]*?)```", combined)
            if code_blocks:
                last_code = code_blocks[-1].strip()
                # Rewrite any CSV filename in the code to 'data.csv' to match uploaded file
                last_code = re.sub(r"(['\"])\s*[^'\"\n]+\.csv\s*(['\"])", "'data.csv'", last_code, flags=re.IGNORECASE)
                code_executor_agent = getCodeExecutorAgent(docker)
                # Try installing common libs in docker env
                install_msg = TextMessage(
                    content=(
                        "Please install the required Python packages before running the code.\n"
                        "```bash\n"
                        "pip install --quiet pandas matplotlib seaborn\n"
                        "```"
                    ),
                    source='User'
                )
                try:
                    await code_executor_agent.on_messages(messages=[install_msg])
                except Exception:
                    pass

                task_msg = TextMessage(
                    content=f"Here is the python code which you have to run\n```python\n{last_code}\n```",
                    source='User'
                )
                try:
                    await code_executor_agent.on_messages(messages=[task_msg])
                except Exception:
                    pass

                # If still not present, run locally as a last resort
                if not output_png.exists():
                    try:
                        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', 'pandas', 'matplotlib', 'seaborn'], check=False)
                        code_file = TEMP_DIR / '_agent_code.py'
                        code_file.write_text(last_code, encoding='utf-8')
                        subprocess.run([sys.executable, str(code_file.resolve())], cwd=str(TEMP_DIR.resolve()), check=False)
                    except Exception:
                        pass

        return None
    except Exception as e:
        print(e)
        return e
    finally:
        await stop_docker_container(docker)
                
if st.session_state.messages:
    for msg in st.session_state.messages:
        st.markdown(msg)


if task:
    # Handle file upload (write to temp/data.csv only)
    if uploaded_file is not None:
        data_bytes = uploaded_file.getbuffer()
        with open(TEMP_DIR / 'data.csv', 'wb') as f:
            f.write(data_bytes)
        # Ensure no stale titanic.csv remains
        try:
            stale_titanic = TEMP_DIR / 'titanic.csv'
            if stale_titanic.exists():
                stale_titanic.unlink()
        except Exception:
            pass
    else:
        # If no upload, but titanic.csv exists and data.csv does not, create data.csv from titanic.csv
        titanic_csv = TEMP_DIR / 'titanic.csv'
        data_csv = TEMP_DIR / 'data.csv'
        if titanic_csv.exists() and not data_csv.exists():
            try:
                data_csv.write_bytes(titanic_csv.read_bytes())
            except Exception:
                pass

    # Always delete old output so the next image is fresh
    try:
        old_output = TEMP_DIR / 'output.png'
        if old_output.exists():
            old_output.unlink()
    except Exception:
        pass
    # Also delete any leftover local fallback code file
    try:
        leftover_code = TEMP_DIR / '_agent_code.py'
        if leftover_code.exists():
            leftover_code.unlink()
    except Exception:
        pass
    # Remove any stale titanic.csv to force the agent/code to use data.csv
    try:
        stale_titanic = TEMP_DIR / 'titanic.csv'
        if stale_titanic.exists():
            stale_titanic.unlink()
    except Exception:
        pass

    # Ensure the task explicitly asks to save as output.png and targets the uploaded file
    task_to_run = task.strip() if isinstance(task, str) else str(task)
    # Normalize any CSV filename in the task to data.csv (handles arbitrary names and titanic.csv)
    task_to_run = re.sub(r"(['\"])\s*[^'\"\n]+\.csv\s*(['\"])", "'data.csv'", task_to_run, flags=re.IGNORECASE)
    # Append save instruction if missing
    if 'output.png' not in task_to_run.lower():
        if task_to_run.endswith('.'):
            task_to_run = task_to_run[:-1]
        task_to_run = f"{task_to_run} and save it as output.png"
    # Add adaptive guidance so agent works with arbitrary schemas
    guidance = (
        "Use the provided CSV file named data.csv located in the working directory. "
        "Do not assume Titanic-specific columns. If any requested columns are missing, first inspect the available columns (e.g., df.columns) "
        "and choose appropriate available columns to produce a similar visualization. Always save the figure strictly as output.png."
    )
    task_to_run = f"{guidance}\n\n{task_to_run}"

    openai_model_client = get_model_client()
    docker = getDockerCommandLineExecutor()

    error = asyncio.run(run_analyzer_gpt(docker, openai_model_client, task_to_run))

    if error:
        st.error(f"An error occurred: {error}")

    if (TEMP_DIR / 'output.png').exists():
        st.image(str(TEMP_DIR / 'output.png'), caption='Analysis File')
else:
    st.info("Enter a task in the chat input to start. Optionally upload a CSV (defaults to temp/titanic.csv if present).")

