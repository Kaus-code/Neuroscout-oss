import os
import requests
import json
from models import GitHubIssue, IssueAnalysis
from dotenv import load_dotenv
import re

load_dotenv()

class AIEngine:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        # Direct REST URL for Gemini 2.5 Flash (1.5 is deprecated)
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

    def analyze_issue(self, issue: GitHubIssue) -> IssueAnalysis:
        prompt = f"""
        You are a Lead AI Engineer. Analyze the following GitHub issue and determine if it's "expert-level."
        
        Expert-level issues involve:
        - RAG optimization
        - Multi-agent coordination
        - Custom PyTorch/TensorFlow layers
        - Complex React state bugs (AI dashboards)
        - Deep learning architecture improvements
        
        Discard:
        - Documentation typos
        - Simple UI color changes or CSS fixes
        - Basic feature requests without technical complexity
        
        Issue Title: {issue.title}
        Issue Body: {issue.body[:3000] if issue.body else "No body"}
        
        Respond ONLY in JSON format following this schema:
        {{
            "fit_score": (int 1-10),
            "is_expert_level": (bool),
            "implementation_strategy": (string),
            "reasoning": (string)
        }}
        """
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }
        
        try:
            response = requests.post(f"{self.url}?key={self.api_key}", headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            # Extract text from candidate
            content_text = result['candidates'][0]['content']['parts'][0]['text']
            
            data = json.loads(content_text.strip())
            return IssueAnalysis(**data)
        except Exception as e:
            # Fallback parsing if JSON mode is tricky or model response is slightly off
            try:
                if 'response' in locals() and response.text:
                    content_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                    match = re.search(r'\{.*\}', content_text, re.DOTALL)
                    if match:
                        data = json.loads(match.group())
                        return IssueAnalysis(**data)
            except:
                pass
                
            return IssueAnalysis(
                fit_score=1,
                is_expert_level=False,
                implementation_strategy="N/A",
                reasoning=f"AI Error: {str(e)}"
            )
