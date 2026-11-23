import re
import unicodedata
from typing import Literal

from pydantic import BaseModel

EMERGENCY_SAFE_RESPONSE = (
    "CẢNH BÁO KHẨN CẤP: Các triệu chứng hoặc chỉ số bạn mô tả có thể là dấu hiệu cấp cứu y khoa nguy hiểm. "
    "Vui lòng gọi cấp cứu 115 ngay lập tức hoặc đến phòng cấp cứu / bệnh viện gần nhất để được bác sĩ xử trí kịp thời. "
    "Hệ thống này chỉ hỗ trợ sàng lọc và tham khảo thông tin, không thể xử lý tình huống cấp cứu."
)

PRESCRIPTION_SAFE_RESPONSE = (
    "Hệ thống chỉ cung cấp thông tin tham khảo và sàng lọc nguy cơ tiểu đường, "
    "không thể kê đơn thuốc, chỉ định thuốc hoặc điều chỉnh liều lượng (bao gồm insulin hay thuốc hạ đường huyết). "
    "Vui lòng trao đổi trực tiếp với bác sĩ chuyên khoa Nội tiết hoặc cơ sở y tế để được thăm khám và tư vấn phác đồ phù hợp."
)

PROMPT_INJECTION_SAFE_RESPONSE = (
    "Yêu cầu của bạn chứa nội dung điều hướng hệ thống không hợp lệ nên không thể xử lý. "
    "Vui lòng đặt câu hỏi trực tiếp liên quan đến sức khỏe, chỉ số sàng lọc hoặc kiến thức về bệnh tiểu đường."
)

_EMERGENCY_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p)
    for p in (
        r"\bngat xiu\b",
        r"\bbat tinh\b",
        r"\bhon me\b",
        r"\bmat y thuc\b",
        r"\bkhong phan ung\b",
        r"\bco giat\b",
        r"\btho nhanh sau\b",
        r"\bdau nguc du doi\b",
        r"\bdau that nguc\b",
        r"\bkho tho du doi\b",
        r"\bngung tho\b",
        r"\bsuy ho hap\b",
        r"\blo mo\b",
        r"\bnon oi lien tuc\b",
        r"\bnon mua du doi\b",
        r"(?:duong huyet|glucose|blood sugar).{0,30}(?:>|>=|tren|qua|vuot)\s*(?:300|350|400|450|500)",
        r"(?:300|350|400|450|500)\s*(?:mg/dl)?\s*(?:kem|va|voi)?\s*(?:non|lo mo|ngat|kho tho)",
        r"(?:duong huyet|glucose|blood sugar).{0,30}(?:<|<=|duoi|tut)\s*(?:40|45|50|54)",
        r"\b(?:fainting|passed out|passing out|unconscious|unresponsive|coma|seizure|convulsions?)\b",
        r"\b(?:severe chest pain|chest pain|severe shortness of breath|cannot breathe|can't breathe)\b",
        r"\b(?:diabetic ketoacidosis|severe hypoglycemia)\b",
    )
)

_PRESCRIPTION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p)
    for p in (
        r"\bke don\b",
        r"\bke toa\b",
        r"\bboc thuoc\b",
        r"\bviet don thuoc\b",
        r"\bcho toi don thuoc\b",
        r"\blieu (?:tiem )?insulin\b",
        r"\btang lieu\b",
        r"\bgiam lieu\b",
        r"\bchinh lieu\b",
        r"\bdieu chinh lieu\b",
        r"\bdoi thuoc\b",
        r"\bngung thuoc\b",
        r"\bngung uong thuoc\b",
        r"\bbo thuoc\b",
        r"\b(?:nen )?uong thuoc gi\b",
        r"\b(?:nen )?dung thuoc nao\b",
        r"\bthuoc nao (?:de )?(?:tri|chua|khoi|ha duong)\b",
        r"\b(?:metformin|glimepiride|gliclazide|insulin|sitagliptin|empagliflozin|dapagliflozin|liraglutide|semaglutide)\b.{0,35}\b(?:bao nhieu|lieu|don vi|mg|ui|iu|uong|tiem)\b",
        r"\b(?:prescribe|prescription|titrate)\b.{0,35}\b(?:medication|medicine|drug|insulin|metformin|glimepiride|gliclazide|dose|dosage)\b",
        r"\b(?:metformin|glimepiride|gliclazide|insulin)\b.{0,30}\b(?:dose|dosage|units?|mg)\b",
        r"\b(?:how much insulin|increase my insulin|decrease my insulin|change my dose|what medication should i take)\b",
    )
)

_INPUT_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p)
    for p in (
        r"\bignore\s+(?:all\s+|any\s+)?(?:previous|prior|above|system|earlier)\s+(?:instructions?|prompts?|rules?|directives?)\b",
        r"\bdisregard\s+(?:all\s+|any\s+)?(?:previous|prior|above|system)\s+(?:instructions?|prompts?|rules?)\b",
        r"\bforget\s+(?:all\s+|any\s+)?(?:previous|prior|above|system)\s+(?:instructions?|prompts?|rules?)\b",
        r"\boverride\s+(?:system|safety|all)\s+(?:instructions?|prompts?|rules?)\b",
        r"\b(?:reveal|show|print|output)\s+(?:your\s+)?system\s+prompt\b",
        r"\b(?:bo qua|quen di|phot lo)\s+(?:tat ca|moi|cac)?\s*(?:huong dan|chi dan|quy tac|lenh)\s*(?:truoc|tren|he thong)\b",
    )
)

_UNTRUSTED_INJECTION_SPANS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"(?:ignore|disregard|forget)\s+(?:all\s+|any\s+)?(?:previous|prior|above|system|earlier)\s+(?:instructions?|prompts?|rules?|directives?)[^.\n]*[.\n]?",
        r"override\s+(?:system|safety|all)\s+(?:instructions?|prompts?|rules?)[^.\n]*[.\n]?",
        r"(?:you are now|act as|pretend to be|jailbreak)\b[^.\n]*[.\n]?",
        r"(?:system|developer|assistant)\s*:\s*[^.\n]*[.\n]?",
        r"<\|?(?:im_start|im_end|system|instruction|prompt)\|?>",
        r"(?:bỏ\s*qua|bo\s*qua|quên\s*đi|quen\s*di|phớt\s*lờ|phot\s*lo)\s+(?:tất\s*cả|tat\s*ca|mọi|moi|các|cac)?\s*(?:hướng\s*dẫn|huong\s*dan|chỉ\s*dẫn|chi\s*dan|quy\s*tắc|quy\s*tac|lệnh|lenh)\s*(?:trước|truoc|trên|tren|hệ\s*thống|he\s*thong)[^.\n]*[.\n]?",
    )
)

_OUTPUT_DIAGNOSIS_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p)
    for p in (
        r"\bban\s+(?:chac chan|da|dang)\s+(?:da\s+)?(?:mac|bi)\s+(?:benh\s+)?(?:tieu duong|dai thao duong)\b",
        r"(?<!khong\s)(?<!khong phai\s)\bchan doan xac dinh\b",
        r"\bket luan ban\s+(?:mac|bi)\b",
        r"\byou\s+(?:definitely|certainly|clearly)\s+have\s+diabetes\b",
        r"\byou\s+are\s+diagnosed\s+with\s+diabetes\b",
        r"\bi\s+diagnose\s+you\s+with\b",
    )
)

_OUTPUT_DOSING_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p)
    for p in (
        r"\bban\s+(?:nen|hay|can|phai)\s+(?:uong|tiem|dung|bat dau|tang|giam)\s+(?:thuoc\s+)?(?:metformin|glimepiride|gliclazide|insulin|sitagliptin|empagliflozin|dapagliflozin|liraglutide|semaglutide)\b",
        r"\b(?:nen|hay|can|phai)\s+(?:uong|tiem)\s+(?:thuoc\s+)?(?:metformin|glimepiride|gliclazide|insulin|sitagliptin|empagliflozin|dapagliflozin|liraglutide|semaglutide)\b",
        r"\b(?:metformin|glimepiride|gliclazide|insulin|sitagliptin|empagliflozin|dapagliflozin)\s+\d+\s*(?:mg|mcg|g|ui|iu|don vi|units?|vien)\b",
        r"\b(?:tang lieu|giam lieu|tiem\s+\d+\s*(?:don vi|ui|iu)|uong\s+\d+\s*(?:mg|vien)\s+(?:moi ngay|hang ngay))\b",
        r"\b(?:take|inject|start|increase|decrease|prescribe)\s+(?:\w+\s+){0,3}(?:metformin|glimepiride|gliclazide|insulin)\b",
        r"\btake\s+\d+\s*(?:mg|tablets?|pills?)\s+(?:daily|every day|twice)\b",
    )
)


class SafetyCheckResult(BaseModel):
    """Outcome of pre-LLM safety screening on user input."""

    is_safe: bool
    flag: Literal["ok", "emergency", "prescription", "prompt_injection"]
    safe_response: str | None = None


def _normalize_ascii(text: str) -> str:
    """Lowercase, strip Vietnamese accents, and normalize whitespace for pattern matching."""
    decomposed = unicodedata.normalize("NFD", text)
    without_marks = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    folded = without_marks.replace("đ", "d").replace("Đ", "D").lower()
    return re.sub(r"\s+", " ", folded).strip()


def _matches_any(normalized: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(normalized) for pattern in patterns)


def check_input_safety(text: str) -> SafetyCheckResult:
    """Screen user input for emergencies, prescription/dosing requests, or prompt injection."""
    normalized = _normalize_ascii(text or "")
    if not normalized:
        return SafetyCheckResult(is_safe=True, flag="ok", safe_response=None)

    if _matches_any(normalized, _EMERGENCY_PATTERNS):
        return SafetyCheckResult(
            is_safe=False,
            flag="emergency",
            safe_response=EMERGENCY_SAFE_RESPONSE,
        )

    if _matches_any(normalized, _PRESCRIPTION_PATTERNS):
        return SafetyCheckResult(
            is_safe=False,
            flag="prescription",
            safe_response=PRESCRIPTION_SAFE_RESPONSE,
        )

    if _matches_any(normalized, _INPUT_INJECTION_PATTERNS):
        return SafetyCheckResult(
            is_safe=False,
            flag="prompt_injection",
            safe_response=PROMPT_INJECTION_SAFE_RESPONSE,
        )

    return SafetyCheckResult(is_safe=True, flag="ok", safe_response=None)


def sanitize_untrusted_text(text: str) -> str:
    """Strip prompt-injection directives from retrieved documents or untrusted snippets."""
    cleaned = text or ""
    for pattern in _UNTRUSTED_INJECTION_SPANS:
        cleaned = pattern.sub(" ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def check_output_safety(text: str) -> tuple[bool, list[str]]:
    """Verify LLM output avoids diagnostic certainty claims and medication dosing directives."""
    normalized = _normalize_ascii(text or "")
    reasons: list[str] = []

    if _matches_any(normalized, _OUTPUT_DIAGNOSIS_PATTERNS):
        reasons.append("Output contains an affirmative diagnostic certainty claim.")

    if _matches_any(normalized, _OUTPUT_DOSING_PATTERNS):
        reasons.append("Output contains a medication prescription or dosing directive.")

    return len(reasons) == 0, reasons
