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
        english.append("SYNTHETIC REPLAY - not a description of current pollution or evidence of a government order.")
        hindi.append("काल्पनिक रीप्ले - यह वर्तमान प्रदूषण का विवरण या किसी सरकारी आदेश का प्रमाण नहीं है।")
    if needs_review:
        english.append("This version needs review; a new plan based on revised inputs has not yet been approved.")
        hindi.append("इस संस्करण की समीक्षा आवश्यक है; संशोधित जानकारी के आधार पर नई योजना अभी अनुमोदित नहीं हुई है।")
    for diff in plan.differences:
        p = diff.proposed
        english.append(f"Activity {diff.activity_id}: {diff.original.period_id} / {diff.original.room_id} -> "
                       f"{'deferred with explicit permission' if p.deferred else p.period_id + ' / ' + p.room_id}; "
                       f"approved alternative: {p.alternative_id or 'none'}.")
        hindi.append(f"गतिविधि {diff.activity_id}: {diff.original.period_id} / {diff.original.room_id} -> "
                     f"{'स्पष्ट अनुमति से स्थगित' if p.deferred else p.period_id + ' / ' + p.room_id}; "
                     f"अनुमोदित विकल्प: {p.alternative_id or 'कोई नहीं'}।")
    if not plan.differences:
        english.append("No timetable changes in this version.")
        hindi.append("इस संस्करण में समय-सारणी का कोई परिवर्तन नहीं है।")
    english.append("A teacher's acknowledgement of receiving the plan is separate from carrying it out. This preview does not establish a school closure or a health benefit.")
    hindi.append("शिक्षक द्वारा योजना मिलने की पुष्टि और उसका कार्यान्वयन अलग हैं। इस पूर्वावलोकन से विद्यालय बंद होने या स्वास्थ्य लाभ का निष्कर्ष नहीं निकाला जा सकता।")
    return MessagePreview(plan_version=plan.id, mode=mode, calendar_date=date,
                          needs_review=needs_review, english="\n".join(english), hindi="\n".join(hindi))
