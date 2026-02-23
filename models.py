from pydantic import BaseModel, Field
from typing import List, Optional

class GitHubIssue(BaseModel):
    id: int
    number: int
    title: str
    body: Optional[str] = ""
    html_url: str
    repo_name: str

class IssueAnalysis(BaseModel):
    fit_score: int = Field(ge=1, le=10, description="Technical Fit Score (1-10)")
    is_expert_level: bool = Field(description="Is this an expert-level technical issue?")
    implementation_strategy: str = Field(description="A brief implementation strategy")
    reasoning: str = Field(description="Why this issue was flagged or discarded")
