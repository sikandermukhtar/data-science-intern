import json
from pathlib import Path
from typing import List, Dict, Any
from agent.configs.config import agent_settings

DEFAULT_SUPERVISOR_PROMPT = """You are a Lead Data Science Supervisor. Your job is to orchestrate a team of Data Science Workers to solve the user's data science goals.
When a user asks a question or provides a dataset, follow this process:
1. Analyze the overall goal and any uploaded files.
2. Break it down into a list of sequential, concrete tasks (e.g., Task 1: EDA, Task 2: Data Preprocessing, Task 3: Model Training and Evaluation).
4. For each task, trigger the appropriate Worker Agent to execute it.
5. Review the Worker's code outputs and generated charts.
6. Compile and synthesize the results, then provide a comprehensive final answer to the user containing markdown tables, summaries, and lists of output files.
You must only keep high-level summaries of worker results in your main context. Do not clutter your history with all code trial-and-error logs; keep those isolated in the workers' contexts.
"""
DEFAULT_WORKER_PROMPT = """You are an expert Data Science Worker. Your task is to write and execute python code to accomplish: {task_description}.

You have access to a Local Python Sandbox where you can run code.
Your output must include:
1. The python code block you want to execute (wrapped in ```python ... ```).
2. A explanation of what the code is doing.

Guidelines for your code:
- Import all necessary libraries (pandas, numpy, sklearn, matplotlib, seaborn, etc.).
- Always import matplotlib and call `matplotlib.use('Agg')` BEFORE importing pyplot (e.g. `import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt`) to prevent GUI hanging.
- Save all plots, charts, images, and data files (like CSVs) directly in the current working directory (e.g. write files as `plt.savefig('plot.png')` or `df.to_csv('data.csv')` without any path prefix). Do NOT write or prefix them with '{output_dir}'.
- Do not use interactive plotting (e.g., do not call `plt.show()`). Save files using `plt.savefig()` instead.
- Print clear summaries, shapes, missing counts, and performance metrics (confusion matrix, classification report, MSE, etc.) to stdout so they can be inspected.

If your code fails, you will receive the error message. Analyze the error and correct your code.
"""

class ContextManager:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_dir = agent_settings.BASE_DIR / "sessions" / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.context_file = self.session_dir / "context.json"

        self.messages: List[Dict[str, Any]] = []
        self.load_context()

        if not self.messages:
            self.set_system_prompt(DEFAULT_SUPERVISOR_PROMPT)

    def load_context(self):
        """Loads context messages (from disk for now, will be replaced by database)."""
        if self.context_file.exists():
            try:
                with open(self.context_file, "r") as f:
                    self.messages = json.load(f)
            except Exception:
                self.messages = []
        else:
            self.messages = []

    def save_context(self):
        """Saves current context messages"""
        try:
            with open(self.context_file, "w") as f:
                json.dump(self.messages, f, indent=2)
        except Exception as e:
            print(f"Context couldn't be saved for the session {self.session_id}: {e}")

    def set_system_prompt(self, prompt: str):
        """Ensures the first message is the system prompt."""
        if self.messages and self.messages[0]["role"] == "system":
            self.messages[0]["content"] = prompt
        else:
            self.messages.insert(0, {"role": "system", "content": prompt})
        self.save_context()

    def add_message(self, role: str, content: str, **kwargs):
        """Adds a message to history"""
        message = {"role": role, "content": content}
        message.update(kwargs)
        self.messages.append(message)
        self.save_context()

    def get_messages(self) -> List[Dict[str, Any]]:
        """Returns the list of messages in LiteLLM format."""
        return self.messages

    def clear(self):
        """Clears session logs"""
        system_message = next((m for m in self.messages if m["role"] == "system"), None)
        self.messages = [system_message] if system_message else [{"role": "system", "content": DEFAULT_SUPERVISOR_PROMPT}]
        self.save_context()