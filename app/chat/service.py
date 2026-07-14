from __future__ import annotations

import asyncio
import random
from typing import AsyncGenerator

from groq import AsyncGroq, RateLimitError, APITimeoutError, APIConnectionError

from ..core.config import settings
from .prompts import build_system_prompt


def _client() -> AsyncGroq:
    """Return a configured async Groq client."""
    return AsyncGroq(api_key=settings.GROQ_API_KEY)


async def call_with_retry(func, *args, max_retries=3, initial_delay=1.0, backoff_factor=2.0, **kwargs):
    """
    Call an async function with exponential backoff and jitter for RateLimit, Timeout, and Connection errors.
    """
    delay = initial_delay
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except (RateLimitError, APITimeoutError, APIConnectionError) as e:
            if attempt == max_retries:
                raise e
            
            # Calculate backoff with random jitter (0.8 - 1.2)
            jitter = random.uniform(0.8, 1.2)
            sleep_time = delay * jitter
            print(f"[Groq Retry] Attempt {attempt + 1} failed with {type(e).__name__}. Retrying in {sleep_time:.2f}s...")
            await asyncio.sleep(sleep_time)
            delay *= backoff_factor


def _to_groq_history(history: list[dict]) -> list[dict]:
    """
    Convert our internal message history to Groq-compatible message objects.

    Each item in `history` is expected to be:
        {"role": "user" | "model", "text": "..."}
        
    Groq expects "assistant" instead of "model" and "content" instead of "text".
    """
    groq_history = []
    for msg in history:
        role = "assistant" if msg["role"] == "model" else msg["role"]
        groq_history.append({"role": role, "content": msg["text"]})
    return groq_history


async def is_harmful_input(text: str) -> bool:
    """
    Check if the user input violates safety/moderation guidelines using Llama Guard.
    Returns True if the content is harmful/unsafe, False otherwise.
    """
    client = _client()
    try:
        response = await call_with_retry(
            client.chat.completions.create,
            model="llama-guard-3-8b",
            messages=[{"role": "user", "content": text}],
            temperature=0.0,
            max_tokens=10,
            stream=False,
        )
        content = response.choices[0].message.content.strip().lower()
        print(f"[Moderation Check] Input: {text[:30]}... | Result: {content}")
        return "unsafe" in content
    except Exception as e:
        print(f"[Moderation Error] Safety check failed: {e}")
        return False


async def stream_reply(
    history: list[dict],
    user_message: str,
    retrieved_context: str = "",
) -> AsyncGenerator[str, None]:
    """
    Stream a Groq reply token-by-token over an async generator.

    Args:
        history:           List of previous turns [{role, text}, ...].
                           Role must be "user" or "model".
        user_message:      The latest message from the user.
        retrieved_context: Optional RAG chunks to inject into the system prompt.

    Yields:
        Text chunks as they arrive from the model.
    """
    # 1. Content Moderation Check
    if await is_harmful_input(user_message):
        yield "[Safety Warning: Your message has been flagged by our content moderation system. Please keep the conversation safe, respectful, and educational.]"
        return

    client = _client()
    system_prompt = build_system_prompt(retrieved_context)

    # Prepare messages payload
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(_to_groq_history(history))
    messages.append({"role": "user", "content": user_message})

    # Estimate prompt tokens locally (approx 3.9 characters per token)
    full_prompt_text = system_prompt + " " + " ".join([m["content"] for m in messages[1:]])
    prompt_tokens = max(1, int(len(full_prompt_text) / 3.9))

    # Call the Groq API with streaming enabled (without stream_options keyword) with retry
    try:
        stream = await call_with_retry(
            client.chat.completions.create,
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=2048,
            stream=True,
        )
    except (RateLimitError, APITimeoutError, APIConnectionError) as e:
        print(f"[Groq Error] Chat completion failed after retries: {e}")
        yield f"\n\n[System Error: The English Tutor is currently busy (Rate Limit/Timeout). Please try again in a few seconds. Details: {e}]"
        return
    
    completion_text = ""
    async for chunk in stream:
        if chunk.choices:
            content = chunk.choices[0].delta.content
            if content:
                completion_text += content
                yield content

    # Calculate final completion token count (approx 3.9 characters per token) and cost
    completion_tokens = max(1, int(len(completion_text) / 3.9))
    # llama-3.3-70b-versatile rates: $0.59/M input, $0.79/M output
    cost = (prompt_tokens * 0.59 / 1_000_000) + (completion_tokens * 0.79 / 1_000_000)
    print(f"[Groq Usage] Model: llama-3.3-70b-versatile (Estimated) | Prompt Tokens: {prompt_tokens} | Completion Tokens: {completion_tokens} | Cost: ${cost:.8f}")
    
    # Yield usage data as a metadata string to be picked up by the WebSocket
    yield f"[USAGE:{{\"prompt_tokens\": {prompt_tokens}, \"completion_tokens\": {completion_tokens}, \"cost\": {cost:.8f}}}]"

async def generate_chat_title(prompt: str) -> str:
    """Generate a short 3-5 word title for a new chat session based on the first prompt."""
    client = _client()
    try:
        response = await call_with_retry(
            client.chat.completions.create,
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates extremely short titles (2-5 words max) for a conversation based on the user's first message. Do NOT use quotes around the title. Do NOT add any preamble. Just output the short title."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=15,
            stream=False,
        )
        
        # Log token usage for title generation (fully supported in non-streaming responses)
        if hasattr(response, "usage") and response.usage:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            # llama-3.1-8b-instant rates: $0.05/M input, $0.08/M output
            cost = (prompt_tokens * 0.05 / 1_000_000) + (completion_tokens * 0.08 / 1_000_000)
            print(f"[Groq Usage] Model: llama-3.1-8b-instant | Prompt Tokens: {prompt_tokens} | Completion Tokens: {completion_tokens} | Cost: ${cost:.8f}")

        title = response.choices[0].message.content.strip().strip('"').strip("'")
        return title[:100]  # Ensure it fits in the DB column
    except Exception as e:
        print(f"[Groq Error] Failed to generate chat title: {e}")
        # Fallback if title generation fails
        return prompt[:30] + ("..." if len(prompt) > 30 else "")
