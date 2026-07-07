"""OpenAI-compatible request/response models for ``/v1/chat/completions``."""

from pydantic import BaseModel, Field
from typing import Optional


class Message(BaseModel):
    """A chat message."""
    role: str  # system | user | assistant
    content: str


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request body."""
    model: str = "gpt-4o"
    messages: list[Message]
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False
    model_name: Optional[str] = None  # resolved model name (TextToSQLFlow extension)


class Choice(BaseModel):
    """A single completion choice."""
    index: int
    message: Message
    finish_reason: str = "stop"


class Usage(BaseModel):
    """Token usage information."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response."""
    id: str = ""
    object: str = "chat.completion"
    created: int = 0
    model: str = ""
    choices: list[Choice] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)
