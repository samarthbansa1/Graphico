import asyncio
import re
import subprocess
import sys
from pathlib import Path
from autogen_core import CancellationToken
from team.analyzer_gpt import getDataAnalyzerTeam
from agents.Code_Executor_Agent import getCodeExecutorAgent
from agents.Data_analyzer_agent import getDataAnalyzerAgent
from config.openai_model_client import get_model_client
from config.docker_utils import getDockerCommandLineExecutor,start_docker_container,stop_docker_container
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.base import TaskResult

async def main():
    openai_model_client = get_model_client()
    docker = getDockerCommandLineExecutor()

    team = getDataAnalyzerTeam(docker,openai_model_client)

    try:
        task = 'Create a violin plot of Fare by Survived from titanic.csv and save it as output.png'

        # Ensure temp/data.csv exists for the agent (some prompts expect data.csv)
        repo_root = Path(__file__).resolve().parent.parent
        temp_dir = repo_root / 'temp'
        temp_dir.mkdir(parents=True, exist_ok=True)
        titanic_csv = temp_dir / 'titanic.csv'
        data_csv = temp_dir / 'data.csv'
        if titanic_csv.exists() and not data_csv.exists():
            try:
                data_csv.write_bytes(titanic_csv.read_bytes())
            except Exception:
                pass

        # Always delete any existing output.png before running so the result is fresh
        old_output = temp_dir / 'output.png'
        try:
            if old_output.exists():
                old_output.unlink()
        except Exception:
            pass

        # Also remove any leftover local fallback code file
        leftover_code = temp_dir / '_agent_code.py'
        try:
            if leftover_code.exists():
                leftover_code.unlink()
        except Exception:
            pass

        await start_docker_container(docker)

        streamed_contents = []
        async for message in team.run_stream(task=task):
            print('='*40)
            if isinstance(message,TextMessage):
                print(message.source, ":", message.content)
                streamed_contents.append(str(message.content))
                
            elif isinstance(message,TaskResult):
                print("Stop Reason :" , message.stop_reason) 

        # If the code executed correctly, output.png should exist in temp
        output_png = temp_dir / 'output.png'
        if output_png.exists():
            print(f"Graph saved to: {output_png.resolve()}")
        else:
            # Fallback: extract last Python code block and execute explicitly via CodeExecutor
            combined = "\n\n".join(streamed_contents)
            code_blocks = re.findall(r"```python\s*([\s\S]*?)```", combined, flags=re.IGNORECASE)
            if code_blocks:
                last_code = code_blocks[-1].strip()
                code_executor_agent = getCodeExecutorAgent(docker)
                # First try to ensure common data/plot libs are available inside the docker env
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
                    await code_executor_agent.on_messages(
                        messages=[install_msg],
                        cancellation_token=CancellationToken()
                    )
                except Exception:
                    pass
                task_msg = TextMessage(
                    content=f"Here is the python code which you have to run\n```python\n{last_code}\n```",
                    source='User'
                )
                try:
                    await code_executor_agent.on_messages(
                        messages=[task_msg],
                        cancellation_token=CancellationToken()
                    )
                except Exception:
                    pass
                # Re-check for output
                if (temp_dir / 'output.png').exists():
                    print(f"Graph saved to: {(temp_dir / 'output.png').resolve()}")
                else:
                    # As a final fallback, try running the extracted code locally in this Python env
                    try:
                        # Ensure common libs are installed locally
                        subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', 'pandas', 'matplotlib', 'seaborn'], check=False)
                        code_file = temp_dir / '_agent_code.py'
                        code_file.write_text(last_code, encoding='utf-8')
                        subprocess.run([sys.executable, str(code_file)], cwd=str(temp_dir), check=False)
                    except Exception:
                        pass
                    if (temp_dir / 'output.png').exists():
                        print(f"Graph saved to: {(temp_dir / 'output.png').resolve()}")

    except Exception as e:
        print(e)
    finally:
        await stop_docker_container(docker)


if (__name__=='__main__'):
    asyncio.run(main())
