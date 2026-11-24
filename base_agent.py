"""
Base agent — shared interface, Gemini integration, provenance logging,
and human-approval gate used by all specialist agents.
"""

import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ── Provenance labels displayed in the UI ────────────────────────
LABEL_COMPUTED = "🟢 [COMPUTED]"
LABEL_AI       = "🔵 [AI ANALYSIS]"
LABEL_APPROVAL = "🟡 [REQUIRES APPROVAL]"
LABEL_ERROR    = "🔴 [ERROR]"


class AgentResponse:
    """Standard response envelope returned by every agent."""

    def __init__(self, agent_name: str, query: str):
        self.agent_name = agent_name
        self.query = query
        self.timestamp = datetime.now().isoformat()
        self.computed: Dict[str, Any] = {}       # rule-based numbers
        self.ai_narrative: str = ""              # Gemini-generated text
        self.charts: list = []                   # file paths to generated charts
        self.requires_approval: bool = False
        self.approval_item: Optional[str] = None # what exactly needs approval
        self.error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent_name,
            "query": self.query,
            "timestamp": self.timestamp,
            "computed": self.computed,
            "ai_narrative": self.ai_narrative,
            "charts": self.charts,
            "requires_approval": self.requires_approval,
            "approval_item": self.approval_item,
            "error": self.error,
        }

    def to_text(self) -> str:
        """Human-readable plain-text version for the chat UI."""
        lines = [f"**{self.agent_name}**  |  {self.timestamp[:16]}"]
        if self.error:
            lines.append(f"\n{LABEL_ERROR}  {self.error}")
            return "\n".join(lines)

        if self.computed:
            lines.append(f"\n{LABEL_COMPUTED}")
            for k, v in self.computed.items():
                lines.append(f"  • {k}: {v}")

        if self.ai_narrative:
            lines.append(f"\n{LABEL_AI}")
            lines.append(self.ai_narrative)

        if self.requires_approval:
            lines.append(f"\n{LABEL_APPROVAL}  {self.approval_item}")

        if self.charts:
            lines.append(f"\n📊 Charts: {', '.join(self.charts)}")

        return "\n".join(lines)


class BaseAgent:
    """
    Abstract base for all warehouse agents.

    Subclasses must implement ``run(query, df, **kwargs) -> AgentResponse``.
    """

    name: str = "BaseAgent"

    def __init__(self):
        self._gemini_client = None

    # ── Gemini integration ───────────────────────────────────────

    def _get_gemini_client(self):
        """Lazily initialise the Gemini client. Returns None if unavailable."""
        if self._gemini_client is not None:
            return self._gemini_client
        try:
            from config.settings import GEMINI_API_KEY, GEMINI_MODEL
            if not GEMINI_API_KEY:
                logger.warning("GEMINI_API_KEY not set. AI narratives will be skipped.")
                return None
            from google import genai
            self._gemini_client = genai.Client(api_key=GEMINI_API_KEY)
            return self._gemini_client
        except ImportError:
            logger.warning("google-genai not installed. AI narratives will be skipped.")
            return None
        except Exception as exc:
            logger.warning("Gemini init failed: %s", exc)
            return None

    def _ask_gemini(self, prompt: str, system_prefix: str = "") -> str:
        """
        Call Gemini with a prompt and return the text response.
        Returns an empty string (silently) if the client is unavailable.
        """
        client = self._get_gemini_client()
        if client is None:
            return ""
        try:
            from config.settings import GEMINI_MODEL
            from config.prompts import SYSTEM_PROMPT
            full_prompt = f"{SYSTEM_PROMPT}\n\n{system_prefix}\n\n{prompt}".strip()
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=full_prompt,
            )
            return response.text.strip()
        except Exception as exc:
            logger.error("Gemini call failed: %s", exc)
            return f"[AI narrative unavailable: {exc}]"

    # ── Human approval gate ──────────────────────────────────────

    def _flag_for_approval(self, response: AgentResponse, item: str) -> None:
        """Mark a response as requiring human approval before action."""
        response.requires_approval = True
        response.approval_item = item

    # ── Logging ─────────────────────────────────────────────────

    def _log(self, response: AgentResponse) -> None:
        """Append the response to the audit log file."""
        try:
            from config.settings import LOGS_DIR
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            log_path = LOGS_DIR / "agent_audit.jsonl"
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(response.to_dict(), default=str) + "\n")
        except Exception as exc:
            logger.warning("Audit log write failed: %s", exc)

    # ── Main entry point ─────────────────────────────────────────

    def run(self, query: str, df, **kwargs) -> AgentResponse:
        raise NotImplementedError("Subclasses must implement run()")
