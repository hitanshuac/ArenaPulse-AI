import json
import os
from typing import Any

import google.generativeai as genai
from pydantic import BaseModel, Field

from app.deterministic_rules import run_deterministic_crowd_analysis, run_deterministic_translation


class ToolArgument(BaseModel):
    zone_id: str = Field(default="")
    script_en: str = Field(default="")
    script_es: str = Field(default="")
    urgency_reason: str = Field(default="")
    priority: str = Field(default="")
    instructions: str = Field(default="")

class DecisionModel(BaseModel):
    tool_name: str
    arguments: ToolArgument

class FanQueryResponse(BaseModel):
    urgency_level: str
    detected_intent: str
    translated_response_en: str
    translated_response_es: str

api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

class VolunteerAgent:
    """
    An agent that processes incoming stadium telemetry, reasons over safety thresholds,
    and executes deterministic workflows based on its findings.
    """

    def __init__(self):
        self.api_available = True if api_key else False

    def _dispatch_broadcast(self, zone_id: str, script_en: str, script_es: str) -> str:
        return f"[Dispatched Broadcast] Audio script pushed to {zone_id} speaker system. (EN: '{script_en[:40]}...', ES: '{script_es[:40]}...')"

    def _escalate_to_command(self, zone_id: str, urgency_reason: str) -> str:
        return f"[Escalation Triggered] Central command notified of critical issue in {zone_id}: {urgency_reason}."

    def _assign_volunteer_tasks(self, zone_id: str, priority: str, instructions: str) -> str:
        return f"[Task Assigned] Mobile alert pushed to volunteers in '{zone_id}' with {priority} priority: {instructions}."

    def process_telemetry(self, zones: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Ingests real-time telemetry metrics and determines operational responses using Gemini.
        """
        if not self.api_available:
            return run_deterministic_crowd_analysis(zones)

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
            You are an autonomous stadium safety coordinator agent for the FIFA World Cup 2026.
            Analyze this real-time stadium telemetry:
            {json.dumps(zones)}

            Rules:
            1. If a zone's occupancy exceeds 80%, you MUST trigger "dispatch_broadcast" and "assign_volunteer_tasks".
            2. If a zone is at or near 95% capacity, you MUST also trigger "escalate_to_command".
            3. If all zones are below 80%, output an empty list of tools.

            Return strictly a valid JSON array of your decisions matching this schema:
            [
                {{
                    "tool_name": "dispatch_broadcast" | "escalate_to_command" | "assign_volunteer_tasks",
                    "arguments": {{
                        "zone_id": "Name of the zone",
                        "script_en": "Clear English megaphone announcement text to route crowd",
                        "script_es": "Spanish translation of the English megaphone announcement",
                        "urgency_reason": "Clear explanation of density bottleneck risk",
                        "priority": "HIGH" | "MEDIUM" | "LOW",
                        "instructions": "Simple action steps for physical volunteers on the ground"
                    }}
                }}
            ]
            """

            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            raw_decisions = json.loads(response.text)
            validated_decisions = [DecisionModel.model_validate(d) for d in raw_decisions]

            execution_trace = []

            for decision in validated_decisions:
                tool_name = decision.tool_name
                args = decision.arguments

                if tool_name == "dispatch_broadcast":
                    res = self._dispatch_broadcast(args.zone_id, args.script_en, args.script_es)
                elif tool_name == "escalate_to_command":
                    res = self._escalate_to_command(args.zone_id, args.urgency_reason)
                elif tool_name == "assign_volunteer_tasks":
                    res = self._assign_volunteer_tasks(args.zone_id, args.priority, args.instructions)
                else:
                    res = f"[Unknown Action] Attempted to trigger unsupported tool: {tool_name}"

                execution_trace.append(res)

            decision_msg = f"Agent evaluated {len(zones)} zones and automatically initiated {len(execution_trace)} safety workflows."
            if not execution_trace:
                decision_msg = "Agent evaluated zones and verified all operations are running safely."
                execution_trace.append("[No Action Required] Telemetry metrics are within safe limits.")

            return {
                "decision": decision_msg,
                "execution_trace": execution_trace
            }

        except Exception as e:
            fallback = run_deterministic_crowd_analysis(zones)
            fallback["decision"] += f" (Gemini Fallback Applied: {e!s})"
            return fallback

    def interpret_fan_query(self, query: str) -> dict[str, Any]:
        """
        Classifies incoming on-ground fan communications for safety risk and translations.
        """
        if not self.api_available:
            return run_deterministic_translation(query)

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
            Analyze this verbal input from a fan near a volunteer checkpoint: "{query}"

            Assess if the query signals an active emergency (medical distress, physical danger, lost children, injuries) or if it is casual navigation.
            Translate the volunteer's response into English and Spanish.

            Return strictly a valid JSON object matching this schema:
            {{
                "urgency_level": "CASUAL" | "CRITICAL",
                "detected_intent": "Brief classification of query intent",
                "translated_response_en": "Your structured, context-aware reply in English",
                "translated_response_es": "Your structured, context-aware reply in Spanish"
            }}
            """

            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            raw_data = json.loads(response.text)
            validated_data = FanQueryResponse.model_validate(raw_data)
            return validated_data.model_dump()
        except Exception as e:
            fallback = run_deterministic_translation(query)
            fallback["detected_intent"] += f" (Fallback applied: {e!s})"
            return fallback
