from __future__ import annotations

from typing import AsyncGenerator

from groq import AsyncGroq

from ..core.config import settings
from .prompts import build_system_prompt


def _client() -> AsyncGroq:
    """Return a configured async Groq client."""
    return AsyncGroq(api_key=settings.GROQ_API_KEY)


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
    client = _client()
    system_prompt = build_system_prompt(retrieved_context)

    # Prepare messages payload
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(_to_groq_history(history))
    messages.append({"role": "user", "content": user_message})

    # Estimate prompt tokens locally (approx 3.9 characters per token)
    full_prompt_text = system_prompt + " " + " ".join([m["content"] for m in messages[1:]])
    prompt_tokens = max(1, int(len(full_prompt_text) / 3.9))

    # Call the Groq API with streaming enabled (without stream_options keyword)
    stream = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=2048,
        stream=True,
    )
    
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
        response = await client.chat.completions.create(
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
