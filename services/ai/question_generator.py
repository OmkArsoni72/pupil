from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from services.ai.prompt_templates import assessment_prompt
import json
import logging
import re
from datetime import datetime, date
from bson import ObjectId
from fastapi.encoders import jsonable_encoder

logger = logging.getLogger(__name__)

class QuestionGenerator:
    @staticmethod
    async def generate_questions(params):
        print(f"🤖 [QuestionGenerator] Starting question generation")
        llm_client = params["llm_client"]
        schema = params["schema"]
        context = params["context"]
        difficulty = params.get("difficulty", "medium")
        subject = params.get("subject", "")
        
        print(f"🤖 [QuestionGenerator] Schema keys: {list(schema.keys()) if schema else 'None'}")
        print(f"🤖 [QuestionGenerator] Context keys: {list(context.keys()) if context else 'None'}")
        print(f"🤖 [QuestionGenerator] Difficulty: {difficulty}, Subject: {subject}")

        # Create structured prompt with all PRD sections and explicit JSON instructions
        parser = JsonOutputParser()
        format_instructions = parser.get_format_instructions()

        prompt = PromptTemplate(
            input_variables=["schema", "context", "difficulty", "subject", "learning_outcomes", "examples", "format_instructions"],
            template="""
You are an expert exam paper generator. Create a complete assessment based on the following specifications:

## EXAM SCHEMA/TEMPLATE
{schema}

## CORE CONTENT CONTEXT
Topics to cover: {context}

## LEARNING OUTCOMES TO BE TESTED
{learning_outcomes}

## DIFFICULTY LEVEL
{difficulty}

## EXAMPLES OF SIMILAR QUESTIONS (for reference only)
{examples}

## INSTRUCTIONS
1. Generate questions that strictly align with the exam schema and learning outcomes
2. If you find a similar question in the examples, DO NOT copy it exactly. Instead, adapt it by:
   - Changing numerical values
   - Modifying scenarios or contexts
   - Using different entities while keeping the core concept the same
3. Ensure questions test the specific learning outcomes provided
4. Maintain the difficulty level specified: {difficulty}
5. Follow the exact structure and format defined in the schema
6. Return ONLY valid JSON as per the schema structure. Do not include any explanations or markdown fences.

{format_instructions}

## CRITICAL OUTPUT REQUIREMENTS
Your response MUST be a valid JSON object with the following structure:
{{
  "sections": [
    {{
      "name": "Section Name",
      "questions": [
        {{
          "questionText": "The actual question text here",
          "questionType": "MCQ",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "answer": {{"key": "A", "explanation": "Explanation here"}},
          "difficulty": "{difficulty}"
        }}
      ]
    }}
  ]
}}

Generate the complete assessment JSON now:
"""
        )

        # Format the prompt with all context data
        def _safe_json_str(obj):
            return json.dumps(
                jsonable_encoder(
                    obj,
                    custom_encoder={
                        ObjectId: str,
                        datetime: lambda v: v.isoformat(),
                        date: lambda v: v.isoformat(),
                    },
                ),
                indent=2,
            )

        formatted_prompt = prompt.format(
            schema=_safe_json_str(schema),
            context=context.get("selected_topics", []),
            learning_outcomes=context.get("learning_outcomes", []),
            difficulty=difficulty,
            subject=subject,
            examples=_safe_json_str(context.get("examples", [])),
            format_instructions=format_instructions,
        )

        try:
            print(f"🤖 [QuestionGenerator] Calling LLM...")
            # Call the LLM
            if hasattr(llm_client, "chat"):
                # For Gemini client
                print(f"🤖 [QuestionGenerator] Using Gemini client")
                output_text = llm_client.chat(formatted_prompt)
            else:
                # For LangChain LLM
                print(f"🤖 [QuestionGenerator] Using LangChain LLM")
                chain = LLMChain(llm=llm_client, prompt=prompt)
                output_text = await chain.arun({
                    "schema": schema,
                    "context": context.get("selected_topics", []),
                    "learning_outcomes": context.get("learning_outcomes", []),
                    "difficulty": difficulty,
                    "subject": subject,
                    "examples": context.get("examples", []),
                    "format_instructions": format_instructions,
                })
            
            print(f"🤖 [QuestionGenerator] LLM response received, length: {len(output_text)}")
            print(f"🤖 [QuestionGenerator] LLM response preview: {output_text[:200]}...")

            # Try to parse as JSON with multiple robust strategies
            try:
                # 1) Preferred: use LangChain JsonOutputParser
                return parser.parse(output_text)

            except json.JSONDecodeError as json_error:
                logger.warning(f"JsonOutputParser decode error: {json_error}")
                
                # 2) Check if LLM returned the full prompt instead of JSON
                if "You are an expert exam paper generator" in output_text:
                    logger.error("LLM returned the full prompt instead of JSON response")
                    return {
                        "error": "LLM returned the full prompt instead of JSON. This indicates an API configuration issue.",
                        "raw_output": output_text[:500] + "..." if len(output_text) > 500 else output_text,
                        "schema": schema,
                        "context": context,
                    }
                
                # 3) Try to extract from fenced code blocks
                fenced = re.search(r"```json\s*([\s\S]*?)\s*```", output_text)
                if fenced:
                    candidate = fenced.group(1)
                    try:
                        return json.loads(candidate)
                    except Exception:
                        pass
                
                # 4) Try to extract the largest JSON object by brace matching
                candidate = QuestionGenerator._extract_json_object(output_text)
                if candidate:
                    try:
                        return json.loads(candidate)
                    except Exception:
                        # 5) Attempt light repair: remove trailing commas
                        repaired = re.sub(r",\s*([}\]])", r"\1", candidate)
                        try:
                            return json.loads(repaired)
                        except Exception:
                            pass
                
                # 6) Give up: return structured error
                logger.warning(f"Raw output (unparsed): {output_text[:500]}...")
                print(f"❌ [QuestionGenerator] Failed to parse JSON after all attempts")
                print(f"❌ [QuestionGenerator] Raw output: {output_text}")
                return {
                    "error": "Failed to parse LLM output as JSON after multiple attempts",
                    "raw_output": output_text[:500] + "..." if len(output_text) > 500 else output_text,
                    "schema": schema,
                    "context": context,
                }

        except Exception as e:
            logger.error(f"Error in question generation: {e}")
            return {
                "error": f"Question generation failed: {str(e)}",
                "schema": schema,
                "context": context
            }

    @staticmethod
    def _extract_json_object(text: str) -> str | None:
        """Extract the first top-level JSON object from text using brace matching."""
        start = None
        depth = 0
        for i, ch in enumerate(text):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start is not None:
                        return text[start:i+1]
        return None
