"""Deterministic Temporal Engine for ContractLens (Phase 8).

Parses contract temporal expressions, classifies them into explicit contractual timing
types, normalizes relative offsets, models recurrence without infinite instantiation,
and computes dates strictly when valid anchor dates are provided.
"""

import re
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from dateutil.relativedelta import relativedelta

from src.models.obligation import (
    TemporalType,
    RecurrenceFrequency,
    RecurrenceRule,
    TemporalConstraint,
)


MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
}

WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "fifteen": 15, "twenty": 20, "thirty": 30, "forty-five": 45,
    "sixty": 60, "ninety": 90, "one hundred twenty": 120,
    "one hundred eighty": 180, "twelve": 12, "twenty-four": 24, "thirty-six": 36
}


class TemporalEngine:
    """Deterministic contract temporal parser and normalizer."""

    @staticmethod
    def parse_temporal_expression(text: str) -> TemporalConstraint:
        """Parse natural contract language into a structured TemporalConstraint.

        Distinguishes:
        - FIXED_DATE: Concrete calendar date
        - RELATIVE_OFFSET: Standard offset (e.g. Net 30, within 30 days of receipt)
        - EVENT_RELATIVE: Triggered by breach, notice, termination, change of control
        - RECURRING: Periodic frequency (monthly, quarterly, annually)
        - CONDITIONAL: "If X occurs, party shall..."
        - ONGOING: Continuous requirement (maintain insurance, keep confidential)
        - UNSPECIFIED: No timing information
        """
        clean_text = text.strip()
        lower = clean_text.lower()

        # 1. Check for CONDITIONAL triggers
        cond_match = re.search(r"\b(?:if|in the event (?:that|of)|upon the occurrence of)\b\s+([^,;]+)[,;]\s*(.+)", clean_text, re.IGNORECASE)
        if cond_match and ("shall" in lower or "must" in lower or "agrees to" in lower or "within" in lower):
            cond_expr = cond_match.group(1).strip()
            remainder = cond_match.group(2).strip()
            sub_temporal = TemporalEngine.parse_temporal_expression(remainder)
            return TemporalConstraint(
                temporal_type=TemporalType.CONDITIONAL,
                raw_expression=clean_text,
                offset_days=sub_temporal.offset_days,
                offset_months=sub_temporal.offset_months,
                anchor_event=sub_temporal.anchor_event or f"condition_{cond_expr[:30].strip()}",
                condition=cond_expr,
                is_resolved=False
            )

        # 2. Check for RECURRING obligations
        recurring_match = re.search(r"\b(annually|annual|quarterly|quarter|monthly|month|weekly|daily|bi-weekly|semi-annually)\b", lower)
        if recurring_match and any(k in lower for k in ["report", "audit", "fee", "payment", "review", "statement", "invoice", "meeting", "reconciliation", "each", "every"]):
            freq_raw = recurring_match.group(1)
            freq_map = {
                "daily": RecurrenceFrequency.DAILY,
                "weekly": RecurrenceFrequency.WEEKLY,
                "bi-weekly": RecurrenceFrequency.WEEKLY,
                "monthly": RecurrenceFrequency.MONTHLY,
                "month": RecurrenceFrequency.MONTHLY,
                "quarterly": RecurrenceFrequency.QUARTERLY,
                "quarter": RecurrenceFrequency.QUARTERLY,
                "annual": RecurrenceFrequency.ANNUAL,
                "annually": RecurrenceFrequency.ANNUAL,
                "semi-annually": RecurrenceFrequency.CUSTOM
            }
            freq = freq_map.get(freq_raw, RecurrenceFrequency.CUSTOM)
            return TemporalConstraint(
                temporal_type=TemporalType.RECURRING,
                raw_expression=clean_text,
                recurrence=RecurrenceRule(
                    frequency=freq,
                    interval=1 if freq_raw != "semi-annually" else 6,
                    anchor_description=clean_text
                ),
                is_resolved=False
            )

        # 3. Check for ONGOING covenants
        if any(phrase in lower for phrase in [
            "at all times", "throughout the term", "during the term", "maintain insurance",
            "keep in force", "maintain in effect", "shall maintain", "shall keep confidential",
            "at its own expense maintain", "continuing obligation"
        ]):
            return TemporalConstraint(
                temporal_type=TemporalType.ONGOING,
                raw_expression=clean_text,
                anchor_event="contract_term",
                is_resolved=False
            )

        # 4. Check for FIXED_DATE
        fixed_match = re.search(r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})\b", lower)
        if fixed_match:
            month_str, day_str, year_str = fixed_match.groups()
            month_int = MONTH_NAMES[month_str]
            day_int = int(day_str)
            year_int = int(year_str)
            iso_date = f"{year_int:04d}-{month_int:02d}-{day_int:02d}"
            return TemporalConstraint(
                temporal_type=TemporalType.FIXED_DATE,
                raw_expression=clean_text,
                anchor_date=iso_date,
                calculated_date=iso_date,
                is_resolved=True
            )

        # 5. Check for RELATIVE_OFFSET or EVENT_RELATIVE
        # Pattern: (within/no later than/prior to) (X) (days/months/years) (after/of/following/prior to) (anchor event)
        offset_match = re.search(
            r"\b(?:within|no later than|not later than|at least|prior to)\s+(?:(?:(?:an?\s+)?additional\s+)?(\w+(?:\s+\w+)?|\d+)(?:\s*\((?:[a-zA-Z\s]+|\d+)\))?)\s+(calendar\s+|business\s+)?(days|months|years|hours)\s+(?:of|after|following|from|prior to)\s+([^,;\.]+)",
            clean_text,
            re.IGNORECASE
        )
        if offset_match:
            num_str = offset_match.group(1).strip().lower()
            unit = offset_match.group(3).strip().lower()
            anchor_raw = offset_match.group(4).strip()

            # Parse number
            offset_val = None
            if num_str.isdigit():
                offset_val = int(num_str)
            elif num_str in WORD_NUMBERS:
                offset_val = WORD_NUMBERS[num_str]
            else:
                # Handle dual like "thirty (30)"
                inner_digit = re.search(r"\d+", offset_match.group(0))
                if inner_digit:
                    offset_val = int(inner_digit.group(0))

            # Determine anchor event
            anchor_event = TemporalEngine._classify_anchor_event(anchor_raw)
            is_event_rel = any(k in anchor_event for k in ["breach", "discovery", "termination", "dispute", "audit", "change_of_control", "written_notice", "claim"])

            offset_days = offset_val if "day" in unit else (offset_val * 30 if "month" in unit and offset_val else None)
            offset_months = offset_val if "month" in unit else None

            return TemporalConstraint(
                temporal_type=TemporalType.EVENT_RELATIVE if is_event_rel else TemporalType.RELATIVE_OFFSET,
                raw_expression=clean_text,
                offset_days=offset_days,
                offset_months=offset_months,
                anchor_event=anchor_event,
                is_resolved=False
            )

        # Net payment terms (e.g., "Net 30", "Net 45")
        net_match = re.search(r"\bnet\s+(\d{1,3})\b", lower)
        if net_match:
            days = int(net_match.group(1))
            return TemporalConstraint(
                temporal_type=TemporalType.RELATIVE_OFFSET,
                raw_expression=clean_text,
                offset_days=days,
                anchor_event="invoice_date",
                is_resolved=False
            )

        # Unspecified timing
        return TemporalConstraint(
            temporal_type=TemporalType.UNSPECIFIED,
            raw_expression=clean_text,
            is_resolved=False
        )

    @staticmethod
    def _classify_anchor_event(anchor_raw: str) -> str:
        """Classify anchor phrase into a standardized anchor event identifier."""
        lower = anchor_raw.lower()
        if "invoice" in lower or "receipt" in lower or "billing" in lower:
            return "invoice_received"
        if "breach" in lower or "default" in lower:
            return "breach_discovered"
        if "effective date" in lower or "commencement" in lower:
            return "effective_date"
        if "expiration" in lower or "end of the term" in lower:
            return "expiration_date"
        if "notice" in lower:
            return "notice_received"
        if "termination" in lower:
            return "termination_notice"
        if "delivery" in lower or "shipment" in lower:
            return "delivery_date"
        if "audit" in lower:
            return "audit_requested"
        # Fallback slug
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", lower).strip("_")
        return slug[:40] if slug else "unspecified_event"

    @staticmethod
    def calculate_deadline(
        constraint: TemporalConstraint,
        anchor_date_str: Optional[str] = None
    ) -> TemporalConstraint:
        """Calculate concrete calendar deadline when a valid anchor date is supplied.

        If anchor_date is missing or unknown, deadline status remains unresolved.
        NEVER invents or hallucinates an anchor date.
        """
        # If already fixed date, nothing to calculate
        if constraint.temporal_type == TemporalType.FIXED_DATE and constraint.calculated_date:
            return constraint

        if not anchor_date_str:
            # Anchor is unknown: return as unresolved without fabricating a date
            return constraint.model_copy(update={"is_resolved": False, "calculated_date": None})

        try:
            anchor_dt = datetime.strptime(anchor_date_str, "%Y-%m-%d")
        except ValueError:
            return constraint.model_copy(update={"is_resolved": False, "calculated_date": None})

        calc_dt = anchor_dt
        if constraint.offset_days is not None:
            calc_dt += relativedelta(days=constraint.offset_days)
        elif constraint.offset_months is not None:
            calc_dt += relativedelta(months=constraint.offset_months)
        else:
            # Cannot calculate without offset
            return constraint.model_copy(update={"anchor_date": anchor_date_str, "is_resolved": False})

        calc_str = calc_dt.strftime("%Y-%m-%d")
        return constraint.model_copy(update={
            "anchor_date": anchor_date_str,
            "calculated_date": calc_str,
            "is_resolved": True
        })
