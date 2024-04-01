from abc import ABC, abstractmethod

class LLMEngine(ABC):
    @abstractmethod
    async def generate(
        self, 
        system_message: str, 
        user_message: str, 
        history: list[tuple[str, str]] | None = None
    ) -> str:
        pass