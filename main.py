import os
import random
import re
from typing import Tuple

import httpx
import openai
from bs4 import BeautifulSoup
from openai import OpenAI

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
CHAT_MODEL = "gpt-4o"
llm = OpenAI(api_key=OPENAI_API_KEY)

_useragent_list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/111.0.1661.62",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0",
]


def get_useragent():
    return random.choice(_useragent_list)


def search_method(url: str) -> Tuple[str, str, str]:
    """Search online for a query.

    Args:
        query (str): Query to search for.

    Returns:
        str: Search results.
    """
    r = httpx.get(
        url,
        headers={"User-Agent": get_useragent()},
    )
    parsed = BeautifulSoup(r.text, "html.parser")
    header = parsed.find(attrs=dict(id="page-header"))

    description = parsed.find(class_="ocpIntroduction")
    sections = parsed.find_all(class_="ocpSection")

    return (
        header.get_text(),
        description.get_text(),
        "\n".join([s.get_text() for s in sections]),
    )


def _generate_method(method_name: str, description: str, extra: str) -> str:
    message = f"""
        Given the Microsoft Excel function {method_name}, with description: {description}, and the following extra information: {extra}.

Implement a method in Python using the polars package, that takes as argument as many pl.Expressions as arguments the function has, and returns a single Expression, being this the result of the operation.

Regardless of the number or arguments, the argument of the function should always be an expanded argument: *args

Moreover, using the example in "extra", create a test case for the function that asserts the result of the function with the expected result.

Return only the function definition and the test case - wrapped in a function called `test` (starting with def and ending with the last line of the function definition).
"""
    response = (
        llm.chat.completions.create(
            messages=[
                {"role": "user", "content": message},
            ],
            model=CHAT_MODEL,
        )
        .choices[0]
        .message.content
    )

    pattern = r"```(\s*(python)\s*\n)?([\s\S]*?)```"
    m = re.search(pattern, response)
    if not m:
        return "I couldn't find a solution for this problem."

    return m.group(3)


def generate_method_from_url(url: str) -> str:
    method_name, description, extra = search_method(url)
    return _generate_method(method_name, description, extra)
