"""
الفرع الأقرب — نظام توزيع الطلبات على فروع الصيدلية.
يعتمد على رمز المنطقة (area code) فيرقم الهاتف لتحديد أقرب فرع.
方式 Palestinian phone area codes map إلى مدن/مناطق:
  2 :+: رام الله/أغوار/قلدومان/بير Zeb
  970/59 :+: غزة (كل الرموز التي تبدأ بـ 59)
  2 ++ : رام الله وضواحيها
"""

# Palestinian area codes → city/region mapping
# الرمز هو أول رقمين或三人 في رقم الهاتف (بعد رمز الدولة +970 أو 970)
AREA_CODE_BRANCHES = {
    "2": "رام الله",       # رام الله وضواحيها (أغوار، قفز، etc.)
    "59": "غزة",          # غزة والمناطق التابعة لها
    "56": "الخليل",       # الخليل وضواحيها
    "52": "نابلس",        # نابلس وضواحيها
    "51": "أريحا",        # أريحا وضواحيها
    "50": "المدينة المنورة / 北 Area",  # 北 area (يعتمد على التغطية)
    "53": "طوباس/ال frequencies",  # طوباس والمناطق الشمالية الشرقية
    "55": "بيت لحم",     # بيت لحم وضواحيها
    "58": "الدوادمي/المركز",  # مناطق وسطية
    "57": "طامر/الغور",   # مناطق الغور
}

# في حال لم يتطابق الرمز — نحدد الفرع الرئيسي
DEFAULT_BRANCH = "غزة"

# إعدادات الفروع (مسافة، اسم، رقم هاتف فرع خاص إذا احتاج)
BRANCH_INFO = {
    "غزة": {
        "name": "الفرع الرئيسي — غزة",
        "address": "غزة، جنوب المول البندا",
        "phone": "9705952224444",
        "delivery_zone": "غزة والضواحي",
    },
    "رام الله": {
        "name": "فرع رام الله",
        "address": "رام الله — 상대국 الأعلى",
        "phone": "",  # إذا ما كان فيه فرع ثاني، يرده على الرئيسي
        "delivery_zone": "رام الله وضواحيها",
    },
    "الخليل": {
        "name": "فرع الخليل",
        "address": "الخليل — 중심 سوق الخليل",
        "phone": "",
        "delivery_zone": "الخليل وضواحيها",
    },
}

def find_nearest_branch_by_phone(phone: str) -> dict:
    """
    تحديد الفرع الأقرب بناءً على رقم الهاتف.
    يأخذ رقم الهاتف (مع أو بدون +970) ويرجع اسم الفرع وإعداداته.
    """
    # تنظيف رقم الهاتف — نأخذ الأرقام فقط
    digits = ''.join(c for c in phone if c.isdigit())
    if not digits:
        return _branch_info(DEFAULT_BRANCH)

    # قرابة الرمز (أول رقمين)
    area_code = digits[:2] if len(digits) >= 2 else digits[:1]

    # البحث عن فرع مطابق
    branch_name = AREA_CODE_BRANCHES.get(area_code, DEFAULT_BRANCH)
    return _branch_info(branch_name)


def find_nearest_branch_by_city(city: str) -> dict:
    """
    تحديد الفرع الأقرب بناءً على اسم المدينة.
    إذا ما وجد مطابق، يرجع الفرع الرئيسي.
    """
    city_lower = city.lower().strip() if city else ""
    if not city_lower:
        return _branch_info(DEFAULT_BRANCH)

    # محاولة مطابقة جزئية
    for branch_name in AREA_CODE_BRANCHES.values():
        if city_lower in branch_name.lower() or branch_name.lower() in city_lower:
            return _branch_info(branch_name)

    return _branch_info(DEFAULT_BRANCH)


def _branch_info(branch_name: str) -> dict:
    """Return branch info dict"""
    info = BRANCH_INFO.get(branch_name, {})
    return {
        "branch": branch_name,
        "branch_name": info.get("name", f"فرع {branch_name}"),
        "address": info.get("address", ""),
        "phone": info.get("phone", ""),
        "delivery_zone": info.get("delivery_zone", branch_name),
    }
