from openai import OpenAI
import os
import json
import time
from dotenv import load_dotenv
load_dotenv()

import inference

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
    Review any arbitrary code using Groq or Gemini.
    Returns structured findings without a grader score.
    """
    providers = []
    
    # 1. Primary: Groq
    if os.environ.get("GROQ_API_KEY"):
        providers.append({
            "name": "Groq",
            "api_key": os.environ.get("GROQ_API_KEY"),
            "base_url": "https://api.groq.com/openai/v1",
            "model": "llama-3.3-70b-versatile"
        })
        
    # 2. Fallback: Gemini
    if os.environ.get("GEMINI_API_KEY"):
        providers.append({
            "name": "Gemini",
            "api_key": os.environ.get("GEMINI_API_KEY"),
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model": "gemini-2.0-flash"
        })
        
    # 3. Last Resort: Inference Proxy / Hackathon Default
    if not providers and hasattr(inference, '_api_key') and inference._api_key:
        providers.append({
            "name": "Fallback Proxy",
            "api_key": inference._api_key,
            "base_url": inference.API_BASE_URL,
            "model": inference.MODEL_NAME
        })

    if not providers:
        return {"error": "API keys not set. Please add GROQ_API_KEY or GEMINI_API_KEY to your .env file."}

    user_prompt = f"""Language: {language}
Context: {context if context else "General code review"}

Code to review:
```{language}
{code}
```

Review this code thoroughly and return JSON only."""

    last_error = ""

    for provider in providers:
        client = OpenAI(api_key=provider["api_key"], base_url=provider["base_url"])
        print(f"Attempting review with {provider['name']} ({provider['model']})...")
        
        provider_attempts = 3
        for attempt in range(provider_attempts):
            try:
                response = client.chat.completions.create(
                    model=provider["model"],
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
                return {"error": f"Failed to parse JSON from {provider['name']} model",
                        "raw": content[:500]}
            except Exception as e:
                err_str = str(e)
                last_error = err_str
                # For Groq or Gemini 429 errors
                if "429" in err_str or "quota" in err_str.lower() or "RESOURCE_EXHAUSTED" in err_str:
                    if attempt < provider_attempts - 1:
                        wait_time = 10 * (attempt + 1)
                        print(f"[{provider['name']}] Rate limit hit. Waiting {wait_time}s before retry ({attempt+1}/{provider_attempts})...")
                        time.sleep(wait_time)
                        continue
                print(f"[{provider['name']}] Request failed. Falling back to next provider if available.")
                break # Exit retry loop and move to next provider
                
    return {"error": f"All fallback APIs failed. Last error: {last_error}"}
