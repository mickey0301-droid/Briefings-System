import os
from openai import OpenAI


def get_client():

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "未找到 OPENAI_API_KEY。\n\n請在系統環境變數設定：\nOPENAI_API_KEY=你的key"
        )

    return OpenAI(api_key=api_key)


def generate_ai_briefing(prompt: str, language: str = "中文"):

    client = get_client()

    system_prompt = """
You are a geopolitical intelligence analyst.

Write a strategic intelligence briefing.

Be analytical and structured.
"""

    if language == "English":
        system_prompt = """
You are a geopolitical intelligence analyst.

Write a strategic intelligence briefing in English.
"""

    response = client.chat.completions.create(

        model="gpt-4o-mini",

        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],

        temperature=0.3
    )

    return response.choices[0].message.content


def generate_sub_briefing(prompt: str, group_name: str = "", language: str = "繁體中文") -> str:
    """
    Generate a focused sub-report (~600-900 words) for one source group.
    Used in multi-phase report generation before final synthesis.
    """
    client = get_client()

    system_prompt = f"""You are a senior intelligence analyst preparing a focused media monitoring sub-report for the [{group_name}] source group.

Requirements:
1. Write in {language}, in formal analytical prose (not bullet points).
2. Length: 600–900 words.
3. Cover the top 3–5 most significant stories with specific details (names, dates, figures).
4. Note any recurring themes, patterns, or escalating developments across stories.
5. Explicitly flag any items related to Taiwan, China, US-China relations, cross-strait tensions, or regional security.
6. This sub-report will feed into a comprehensive synthesis — prioritise content richness and specificity over formatting.
7. Begin directly with the analysis. Do not write a title or heading."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content