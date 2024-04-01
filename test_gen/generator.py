from llm.base import LLMEngine

class PythonTestGenerator:
    """The PythonTestGenerator class is responsible for generating Python unit tests for a given class. 
    It uses a language model to generate the tests and then parses the output to return the generated tests.

    Raises:
        KeyError: If the output is not correctly formatted. If this is the case please re-run the generator.
        ValueError: If the input is not correctly formatted.

    Returns:
        string: The python code of the generated test.
    """
    system_prompt = (
        "You are a senior python developer whose job is to write extended test cases for a python codebase. "
        "You are given a class you need to test and optionally some tests already written for that class. "
        "You must figure out which tests cases to write, covering also the edge cases and increasing the overall "
        "coverage. When you generate some code you must encapusate it into the markdown like sintax ```python ... ```.\n"
        "Note that your tests can be rejected. If that happens you will receive the rejection reason and you need to "
        "rewrite them from scratch.\n"
        "You can use the following libraries: unittest, pytest, hypothesis, fake.\n You MUST import the class you are testing and all the libraries you need.\n"
    ) 
    message_templates = {
        "extend_test": "Here is a Python unit test class: {existing_test_class}. Write an extended version of the test class that includes additional tests to cover some extra corner cases.",
        "extend_coverage": "Here is a Python unit test class and the class that it tests: {existing_test_class} {class_under_test}. Write an extended version of the test class that includes additional unit tests that will increase the test coverage of the class under test.",
        "corner_cases": "Here is a Python unit test class and the class that it tests: {existing_test_class} {class_under_test}. Write an extended version of the test class that includes additional unit tests that will cover corner cases missed by the original and will increase the test coverage of the class under test.",
        "new_test": "Here is a Python class that needs testing: {class_under_test}. Write a Python unit test class that will test the class.",
    }
    
    def __init__(self, llm_engine: LLMEngine) -> None:
        self._llm_engine = llm_engine
        
    @property
    def actions(self) -> list[str]:
        return list(self.message_templates.keys())
    
    async def generate(
        self, 
        action: str, 
        class_under_test: str | None, 
        existing_test_class: str | None, 
        history: list[tuple[str, str]] | None = None
    ) -> str:
        self._validate_input(action, class_under_test, existing_test_class)
        if class_under_test and existing_test_class:
            message = self.message_templates[action].format(
                class_under_test=class_under_test,
                existing_test_class=existing_test_class
            )
        elif class_under_test:
            message = self.message_templates[action].format(
                class_under_test=class_under_test
            )
        else:
            message = self.message_templates[action].format(
                existing_test_class=existing_test_class
            )
        output = await self._llm_engine.generate(
            system_message=self.system_prompt,
            user_message=message,
            history=history
        )
        return self._parse_output(output)
            
    def _validate_input(
        self, 
        action: str, 
        class_under_test: str | None, 
        existing_test_class: str | None
    ) -> None:
        if action not in self.actions:
            raise ValueError(f"Action must be one of {self.actions}")
        if action == "new_test" and existing_test_class is not None:
            raise ValueError("Existing test class should not be provided for action 'new_test'")
        if action != "new_test" and existing_test_class is None:
            raise ValueError("Existing test class should be provided for actions other than 'new_test'")
        if class_under_test is None and action != "extend_test":
            raise ValueError("Class under test must be provided")
        
    def _parse_output(self, output: str) -> str:
        output = output.strip().split("```python")[1].split("```")[0].strip()
        return output
    