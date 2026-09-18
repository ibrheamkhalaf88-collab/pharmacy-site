"""Branch — كشف الفرع الأقرب من رقم الهاتف الفلسطيني.
التصليح: نأخذ الأرقام فقط، ننزع +970 / 0 البادئة، ثم أول رقمين (مثل 59 → غزة).
"""

AREA_CODE_BRANCHES = {
    "59": "غزة",
    "56": "الخليل",
    "52": "نابلس",
    "51": "أريحا",
    "53": "طوباس",
    "55": "بيت لحم",
    "58": "الدوادمي",
    "57": "طماس/الغور",
}

DEFAULT_BRANCH = "غزة"

BRANCH_INFO = {
    "غزة": {"branch": "غزة", "branch_name": "الفرع الرئيسي — غزة", "address": "غزة، جنوب المول البندا", "phone": "9705952224444", "delivery_zone": "غزة والضواحي"},
    "الخليل": {"branch": "الخليل", "branch_name": "فرع الخليل", "address": "الخليل", "phone": "9705952224444", "delivery_zone": "الخليل والضواحي"},
    "نابلس": {"branch": "نابلس", "branch_name": "فرع نابلس", "address": "نابلس", "phone": "9705952224444", "delivery_zone": "نابلس والضواحي"},
}


def find_nearest_branch_by_phone(phone: str) -> dict:
    digits = "".join(c for c in (phone or "") if c.isdigit())
    if not digits:
        return _branch_info(DEFAULT_BRANCH)
    # انزع بادئة الدولة +970 أو الصفر الافتتاحي لأرقام المحمول 05X/059X
    if digits.startswith("970"):
        digits = digits[3:]
    if digits.startswith("0"):
        digits = digits[1:]
    area_code = digits[:2]
    branch_name = AREA_CODE_BRANCHES.get(area_code, DEFAULT_BRANCH)
    return _branch_info(branch_name)


def _branch_info(branch_name: str) -> dict:
    return BRANCH_INFO.get(branch_name, BRANCH_INFO[DEFAULT_BRANCH])