from openai import OpenAI
import os
import json

import inference

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_MODEL = os.environ.get("FREE_REVIEW_MODEL", "gemini-1.5-flash")

SYSTEM_PROMPT = """You are an expert code reviewer with 15+ years 
of experience. Review the provided code and identify ALL issues.

For each issue found, provide:
- line_number: exact line where issue occurs (integer)
- issue_type: one of bug/security/performance/style/logic
- severity: one of critical/major/minor
- description: clear explanation of the problem
- suggested_fix: how to fix it

Also provide:
- overall_verdict: approve/request_changes/comment
- summary: 2-3 sentence overall assessment
- positive_aspects: list of 2-3 things done well

Respond ONLY with valid JSON, no markdown:
{
  "issues": [
    {
      "line_number": <int>,
      "issue_type": "<type>",
      "severity": "<severity>",
      "description": "<description>",
      "suggested_fix": "<fix>"
    }
  ],
  "overall_verdict": "<verdict>",
  "summary": "<summary>",
  "positive_aspects": ["<aspect1>", "<aspect2>"]
}"""

def review_free_code(code: str, language: str = "python", 
                     context: str = "") -> dict:
    """
    Review any arbitrary code using Gemini.
    Returns structured findings without a grader score.
    """
    api_key_to_use = GEMINI_API_KEY if GEMINI_API_KEY else inference._api_key
    base_url_to_use = GEMINI_BASE_URL if GEMINI_API_KEY else inference.API_BASE_URL

    if not api_key_to_use:
        return {"error": "GEMINI_API_KEY not set and inference proxy key unavailable"}

    client = OpenAI(
        api_key=api_key_to_use,
        base_url=base_url_to_use
    )

    user_prompt = f"""Language: {language}
Context: {context if context else "General code review"}

Code to review:
```{language}
{code}
```

Review this code thoroughly and return JSON only."""

    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=3000,
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:])
            if content.strip().endswith("```"):
                content = content.strip()[:-3].strip()
        return json.loads(content)
    except json.JSONDecodeError:
        return {"error": "Failed to parse AI response",
                "raw": content[:500]}
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "quota" in err_str.lower() or "RESOURCE_EXHAUSTED" in err_str:
            return {"error": "API rate limit reached (429). Your Gemini free-tier quota is exhausted. "
                             "Wait a minute and try again, or get a new API key at "
                             "https://aistudio.google.com/app/apikey"}
        return {"error": err_str}
