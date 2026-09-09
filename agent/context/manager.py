from typing import List, Dict, Any, Optional
from agent.configs.config import agent_settings
from agent.db.repository import session_repo

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
    """
    Manages session context, loading and saving conversation turns directly to SQLite DB.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_repo = session_repo

        # Ensure session exists in the database
        if not self.session_repo.get_session(session_id):
            self.session_repo.create_session(session_id)

        self.messages: List[Dict[str, Any]] = []
        self.load_context()

        # If empty conversation, initialize with supervisor system prompt
        if not self.messages:
            self.set_system_prompt(DEFAULT_SUPERVISOR_PROMPT)

    def load_context(self):
        """Loads conversation messages from the SQLite database."""
        self.messages = self.session_repo.get_messages(self.session_id)

    def set_system_prompt(self, prompt: str):
        """Ensures the supervisor system prompt is present in the database."""
        if not any(m.get("role") == "system" for m in self.messages):
            self.session_repo.add_message(
                session_id=self.session_id,
                role="system",
                content=prompt,
                sender="supervisor"
            )
            self.load_context()

    def add_message(
        self,
        role: str,
        content: str,
        files: Optional[List[Dict[str, Any]]] = None,
        turn_id: Optional[str] = None,
        sender: str = "supervisor",
        **kwargs
    ):
        """Persists a message to the SQLite messages table and updates in-memory history."""
        self.session_repo.add_message(
            session_id=self.session_id,
            role=role,
            content=content,
            files=files,
            turn_id=turn_id,
            sender=sender,
            metadata=kwargs
        )
        self.load_context()

    def get_messages(self) -> List[Dict[str, Any]]:
        """Returns the list of messages in LiteLLM / OpenAI format."""
        return self.messages

    def clear(self):
        """Clears session messages from the database and resets to system prompt."""
        self.session_repo.clear_messages(self.session_id)
        self.set_system_prompt(DEFAULT_SUPERVISOR_PROMPT)
        self.load_context()
