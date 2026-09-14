"""Branch detection for Pharmacy Orders.
يحدد الفرع الأقرب بناءً على area code في رقم الهاتف.
"""

AREA_CODE_BRANCHES = {
    "2": "رام الله",
    "59": "غزة",
    "56": "الخليل",
    "52": "نابلس",
    "51": "أريحا",
    "50": "المركز",
    "53": "طوباس",
    "55": "بيت لحم",
    "58": "الدوادمي",
    "57": "طماس/الغور",
}

DEFAULT_BRANCH = "غزة"

BRANCH_INFO = {
    "غزة": {"branch": "غزة", "branch_name": "الفرع الرئيسي — غزة", "address": "غزة، جنوب المول البندا", "phone": "9705952224444", "delivery_zone": "غزة والضواحي"},
    "رام الله": {"branch": "رام الله", "branch_name": "فرع رام الله", "address": "رام الله", "phone": "9705952224444", "delivery_zone": "رام الله والضواحي"},
    "الخليل": {"branch": "الخليل", "branch_name": "فرع الخليل", "address": "الخليل", "phone": "9705952224444", "delivery_zone": "الخليل والضواحي"},
    "نابلس": {"branch": "نابلس", "branch_name": "فرع نابلس", "address": "نابلس", "phone": "9705952224444", "delivery_zone": "نابلس والضواحي"},
}

def find_nearest_branch_by_phone(phone: str) -> dict:
    digits = ''.join(c for c in phone if c.isdigit())
    if not digits:
        return _branch_info(DEFAULT_BRANCH)
    area_code = digits[:2] if len(digits) >= 2 else digits[:1]
    branch_name = AREA_CODE_BRANCHES.get(area_code, DEFAULT_BRANCH)
    return _branch_info(branch_name)

def _branch_info(branch_name: str) -> dict:
    return BRANCH_INFO.get(branch_name, BRANCH_INFO[DEFAULT_BRANCH])
