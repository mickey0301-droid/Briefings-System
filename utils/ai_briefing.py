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
    Generate a structured sub-report for one source group, following the standard
    five-chapter report architecture (一-五). Citation codes [S1][S2]... from
    the input data MUST be preserved intact in the output.
    Used in multi-phase report generation before final synthesis.
    """
    client = get_client()

    system_prompt = f"""You are a senior intelligence analyst preparing a structured sub-report for the [{group_name}] source group.

Requirements:
1. Write in {language}, in formal analytical prose (NOT bullet points).
2. Follow this five-chapter structure exactly. Include every chapter; write "本期無相關新聞。" if a chapter has no relevant content from this source group:

   一、國際要聞
   二、台美中要聞
   三、台灣國安要聞
   四、中國要聞
   五、區域情勢（依新聞所屬地理區域分子節列出）

3. CRITICAL — Citation preservation: The input news items carry citation codes such as [S1], [S2], [S3] etc. Whenever you state a fact drawn from a specific item, append its citation code immediately after the relevant sentence, e.g. "...報導指出。[S3]". NEVER omit, renumber, alter, or invent [Sx] codes. These codes are the sole link to the source bibliography.
4. Do NOT place raw URLs anywhere in the body text.
5. MANDATORY — People: full official title + conventionally established Chinese name（English full name）on first mention. E.g. 美國總統川普（Donald Trump）、日本首相岸田文雄（Fumio Kishida）.
6. MANDATORY — Media outlets: never use vague collective terms like "西方媒體"、"外媒". Use the specific outlet name with Chinese and English on first mention, e.g. 路透社（Reuters）、德國之聲（Deutsche Welle）.
7. MANDATORY — Organizations: Chinese name（English Name）on first mention, e.g. 北大西洋公約組織（NATO）、美國國務院（U.S. Department of State）.
8. Begin directly with 一、國際要聞. Do not write a preamble or title.

Output structure (all eight chapters are REQUIRED; write "本期無相關新聞。" in any chapter or sub-section that has no relevant content from this source group):

一、摘要
（本群組本期最重要判斷，一段）

二、國際要聞

三、台美中要聞

四、台灣國安要聞

五、中國要聞

六、區域情勢
（一）亞太地區
1. 國際要聞研析
2. 台美中要聞研析
（二）亞西地區
1. 國際要聞研析
2. 台美中要聞研析
（三）北美地區
1. 國際要聞研析
2. 台美中要聞研析
（四）拉丁美洲及加勒比海
1. 國際要聞研析
2. 台美中要聞研析
（五）歐洲地區
1. 國際要聞研析
2. 台美中要聞研析
（六）非洲地區
1. 國際要聞研析
2. 台美中要聞研析

七、專家研析
1. 國際要聞研析
2. 台美中要聞研析

八、研析
1. 國際要聞研析
2. 台美中要聞研析"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content