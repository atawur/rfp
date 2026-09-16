import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, cast

from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam
from openai import OpenAI
from google import genai
from google.genai import types

from app.agents.rfp_agent.tools import AVAILABLE_TOOLS, TOOL_REGISTRY
from app.agents.rfp_agent.schemas import RFPExtractionSchema, RFPExtractionListSchema
from app.agents.rfp_agent.prompts import EXTRACTION_SYSTEM_PROMPT, EXTRACTION_USER_PROMPT

logger = logging.getLogger(__name__)


class BaseRFPAgent(ABC):
    """
    Abstract Base Class for RFP AI Extraction & Validation Agents.
    Follows the Strategy Pattern to allow dynamic switching between providers.
    """

    @abstractmethod
    def run(self, url: str, initial_content: str) -> list[Dict[str, Any]]:
        """
        Executes the extraction and validation pipeline for the given webpage content.
        Returns a list of extracted and validated RFP dictionaries.
        """
        pass


class OpenAIRFPAgentPipeline(BaseRFPAgent):
    """
    OpenAI-based agent pipeline supporting tool calling and structured outputs.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        temperature: float = 0.0,
        **extra_params,
    ):
        if not api_key:
            raise ValueError("OpenAI API key must be provided from active database configuration.")
        self.client = OpenAI(api_key=api_key)
        self.model = model or "gpt-4o"
        self.temperature = float(temperature)
        self.extra_params = extra_params

    def _run_extraction_agent(self, url: str, initial_content: str) -> RFPExtractionListSchema:
        logger.info(f"[OpenAI] Running Extraction Agent for {url} using model {self.model}")

        messages: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": EXTRACTION_USER_PROMPT.format(content=initial_content[:30000])},
        ]

        openai_tools = cast(list[ChatCompletionToolParam], AVAILABLE_TOOLS)
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=openai_tools,
                tool_choice="auto",
                temperature=self.temperature,
            )

            message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            if finish_reason == "tool_calls" and message.tool_calls:
                messages.append(message.model_dump())  # type: ignore
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    logger.info(f"[OpenAI] Agent calling tool: {function_name} with {function_args}")

                    if function_name in TOOL_REGISTRY:
                        tool_result = TOOL_REGISTRY[function_name](**function_args)
                    else:
                        tool_result = f"Error: Tool {function_name} not found."

                    messages.append({  # type: ignore
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(tool_result),
                    })
            elif finish_reason == "stop":
                break
            else:
                logger.warning(f"[OpenAI] Unexpected finish_reason: {finish_reason}")
                break

        logger.info("[OpenAI] Extracting final structured data...")
        final_response = self.client.chat.completions.parse(
            model=self.model,
            messages=messages,
            response_format=RFPExtractionListSchema,
            temperature=self.temperature,
        )

        parsed_data = final_response.choices[0].message.parsed
        if not parsed_data:
            raise ValueError("Failed to parse structured output from OpenAI.")

        return parsed_data

    def _run_validation_agent(self, extracted_list: RFPExtractionListSchema) -> list[Dict[str, Any]]:
        logger.info("[OpenAI] Running Validation Agent on extracted items")

        system_prompt = """
        You are a strict Quality Control Validation Agent.
        Your job is to review a list of extracted RFPs.
        Check for logical inconsistencies, such as:
        - Are required fields missing?
        - Are deadlines logically sound?
        - Are there contradictory facts mentioned in validation_flags?
        
        Respond ONLY with a valid JSON object matching this exact schema:
        {
            "results": [
                {
                    "status": "NEW" | "NEEDS_REVIEW",
                    "validation_flags": ["issue 1", "issue 2", ...]
                }
            ]
        }
        Ensure the output results array has exactly the same length and order as the input RFPs.
        """

        user_prompt = f"Review these extracted RFPs:\n{extracted_list.model_dump_json(indent=2)}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=self.temperature,
        )

        content = response.choices[0].message.content or '{"results": []}'
        validation_result = json.loads(content)
        validation_list = validation_result.get("results", [])

        final_data_list = []
        for idx, rfp in enumerate(extracted_list.rfps):
            data = rfp.model_dump()
            val = validation_list[idx] if idx < len(validation_list) else {}
            data["status"] = val.get("status", "NEW")
            data["validation_flags"] = list(set(data.get("validation_flags", []) + val.get("validation_flags", [])))
            final_data_list.append(data)

        return final_data_list

    def run(self, url: str, initial_content: str) -> list[Dict[str, Any]]:
        extracted_list_schema = self._run_extraction_agent(url, initial_content)
        validated_data_list = self._run_validation_agent(extracted_list_schema)

        for data in validated_data_list:
            data["source_url"] = url

        return validated_data_list


class GeminiRFPAgentPipeline(BaseRFPAgent):
    """
    Google Gemini-based agent pipeline supporting structured schema generation.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.0,
        **extra_params,
    ):
        if not api_key:
            raise ValueError("Gemini API key must be provided from active database configuration.")
        self.client = genai.Client(api_key=api_key)
        self.model = model or "gemini-2.5-flash"
        self.temperature = float(temperature)
        self.extra_params = extra_params

    def _run_extraction_agent(self, url: str, initial_content: str) -> RFPExtractionListSchema:
        logger.info(f"[Gemini] Running Extraction Agent for {url} using model {self.model}")

        config = types.GenerateContentConfig(
            system_instruction=EXTRACTION_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=RFPExtractionListSchema,
            temperature=self.temperature,
        )

        user_prompt = EXTRACTION_USER_PROMPT.format(content=initial_content[:30000])

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=config,
        )

        response_text = response.text or "{}"
        try:
            parsed_data = RFPExtractionListSchema.model_validate_json(response_text)
        except Exception as e:
            logger.error(f"[Gemini] Failed to parse structured output from Gemini: {e}")
            raise ValueError(f"Failed to parse structured output from Gemini: {e}")

        return parsed_data

    def _run_validation_agent(self, extracted_list: RFPExtractionListSchema) -> list[Dict[str, Any]]:
        logger.info("[Gemini] Running Validation Agent on extracted items")

        system_instruction = """
        You are a strict Quality Control Validation Agent.
        Your job is to review a list of extracted RFPs.
        Check for logical inconsistencies, such as missing required fields, impossible deadlines, or conflicting facts.
        Respond ONLY with a valid JSON object matching:
        {
            "results": [
                {
                    "status": "NEW" or "NEEDS_REVIEW",
                    "validation_flags": ["issue 1", "issue 2", ...]
                }
            ]
        }
        Ensure the output results array has exactly the same length and order as the input RFPs.
        """

        user_prompt = f"Review these extracted RFPs:\n{extracted_list.model_dump_json(indent=2)}"

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=self.temperature,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=config,
        )

        content = response.text or '{"results": []}'
        validation_result = json.loads(content)
        validation_list = validation_result.get("results", [])

        final_data_list = []
        for idx, rfp in enumerate(extracted_list.rfps):
            data = rfp.model_dump()
            val = validation_list[idx] if idx < len(validation_list) else {}
            data["status"] = val.get("status", "NEW")
            data["validation_flags"] = list(set(data.get("validation_flags", []) + val.get("validation_flags", [])))
            final_data_list.append(data)

        return final_data_list

    def run(self, url: str, initial_content: str) -> list[Dict[str, Any]]:
        extracted_list_schema = self._run_extraction_agent(url, initial_content)
        validated_data_list = self._run_validation_agent(extracted_list_schema)

        for data in validated_data_list:
            data["source_url"] = url

        return validated_data_list


class AgentFactory:
    """
    Factory Pattern for instantiating the appropriate BaseRFPAgent implementation
    based on the database configuration provider.
    """

    @staticmethod
    def create_agent(
        provider: str,
        api_key: str,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        **extra_params,
    ) -> BaseRFPAgent:
        norm_provider = (provider or "").lower().strip()

        if norm_provider == "openai":
            model = model_name or "gpt-4o"
            return OpenAIRFPAgentPipeline(
                api_key=api_key,
                model=model,
                temperature=temperature,
                **extra_params,
            )
        elif norm_provider in {"gemini", "google"}:
            model = model_name or "gemini-2.5-flash"
            return GeminiRFPAgentPipeline(
                api_key=api_key,
                model=model,
                temperature=temperature,
                **extra_params,
            )
        else:
            raise ValueError(
                f"Unsupported AI provider: '{provider}'. Supported providers are: 'openai', 'gemini'."
            )


# Backward compatibility alias
RFPAgentPipeline = OpenAIRFPAgentPipeline
