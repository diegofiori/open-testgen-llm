import openai

from test_gen.llm.base import LLMEngine

class OpenAILLMEngine(LLMEngine):
    def __init__(self, openai_client: openai.AsyncClient, model: str = "gpt-4-0125-preview") -> None:
        self._client = openai_client
        self._model = model
    
    async def generate(
        self, 
        system_message: str, 
        user_message: str, 
        history: list[tuple[str, str]] | None = None
    ) -> str:
        """
        Generates a response from the model
        Parameters:
            system_message(str): The system message
            user_message(str): The user message
            history(List[Tuple[str, str]]): The history of the conversation
        Returns:
            str: The generated response
        """
        messages = self._create_messages(system_message, user_message, history)
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
        )
        return response.choices[0].message.content
    
    def _create_messages(self, system_message: str, user_message: str, history: list[tuple[str, str]] | None) -> list[dict]:
        messages = [{"role": "system", "content": system_message}]
        if history is not None:
            for user, assistant in history:
                messages.append({"role": "user", "content": user})
                messages.append({"role": "assistant", "content": assistant})
        messages.append({"role": "user", "content": user_message})
        return messages