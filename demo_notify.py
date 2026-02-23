"""Send a demo notification to prove the full pipeline works."""
import os
from dotenv import load_dotenv
from models import GitHubIssue, IssueAnalysis
from notifier import TelegramNotifier

load_dotenv()

# Create a mock expert-level issue
mock_issue = GitHubIssue(
    id=99999,
    number=12345,
    title="[Bug] RAG chain drops context when using multi-agent orchestration with streaming",
    body="When using LangGraph's multi-agent setup with streaming enabled, the RAG retriever loses document context between agent handoffs...",
    html_url="https://github.com/langchain-ai/langgraph/issues/12345",
    repo_name="langchain-ai/langgraph"
)

mock_analysis = IssueAnalysis(
    fit_score=9,
    is_expert_level=True,
    implementation_strategy="Fix the context serialization in the agent handoff protocol. Implement a shared memory buffer for RAG context persistence across agent boundaries.",
    reasoning="This involves RAG optimization + multi-agent coordination - core expert-level domains."
)

notifier = TelegramNotifier()
print("Sending demo notification to Telegram...")
notifier.notify(mock_issue, mock_analysis)
print("Done! Check your Telegram.")
