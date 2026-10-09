"""Deterministic bilingual preview, never delivery or model-authored policy."""
from .workflow_contracts import MessagePreview


def message_preview(plan, binding, needs_review):
    mode = binding["mode"] if binding else "MANUAL"
    date = binding.get("calendar_date") if binding else None
    english = ["PREVIEW ONLY - NOT SENT. Synthetic school timetable.",
               f"Approved plan version: {plan.id}", f"Evidence mode: {mode}",
               f"Date: {date or 'Not specified; administrator must verify the date.'}"]
    hindi = ["केवल पूर्वावलोकन - भेजा नहीं गया। काल्पनिक विद्यालय की समय-सारणी।",
             f"अनुमोदित योजना संस्करण: {plan.id}", f"साक्ष्य मोड: {mode}",
             f"तारीख: {date or 'निर्दिष्ट नहीं; प्रशासक तारीख की पुष्टि करें।'}"]
    if mode == "REPLAY":
        english.append("SYNTHETIC REPLAY - not current pollution or a government order.")
        hindi.append("काल्पनिक रीप्ले - वर्तमान प्रदूषण या सरकारी आदेश नहीं।")
    if needs_review:
        english.append("This version needs review; revised inputs have not replaced it.")
        hindi.append("इस संस्करण की समीक्षा आवश्यक है; संशोधित जानकारी ने इसे बदला नहीं है।")
    for diff in plan.differences:
        p = diff.proposed
        english.append(f"Activity {diff.activity_id}: {diff.original.period_id} / {diff.original.room_id} -> "
                       f"{'explicitly deferred' if p.deferred else p.period_id + ' / ' + p.room_id}; "
                       f"approved alternative: {p.alternative_id or 'none'}.")
        hindi.append(f"गतिविधि {diff.activity_id}: {diff.original.period_id} / {diff.original.room_id} -> "
                     f"{'स्पष्ट अनुमति से स्थगित' if p.deferred else p.period_id + ' / ' + p.room_id}; "
                     f"अनुमोदित विकल्प: {p.alternative_id or 'कोई नहीं'}।")
    if not plan.differences:
        english.append("No timetable changes in this version.")
        hindi.append("इस संस्करण में समय-सारणी का कोई परिवर्तन नहीं है।")
    english.append("Teacher acknowledgement is separate from execution. No closure or health benefit is inferred.")
    hindi.append("शिक्षक की प्राप्ति-पुष्टि और कार्यान्वयन अलग हैं। विद्यालय बंद होने या स्वास्थ्य लाभ का निष्कर्ष नहीं है।")
    return MessagePreview(plan_version=plan.id, mode=mode, calendar_date=date,
                          needs_review=needs_review, english="\n".join(english), hindi="\n".join(hindi))
