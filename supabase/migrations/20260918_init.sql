-- ═══════════════════════════════════════════════════════════
-- 001 — صيدلية السلاق: schema سليمة + RLS صارم + seed
-- متوافقة مع أي schema قديم (IF NOT EXISTS + ADD COLUMN IF NOT EXISTS)
-- ═══════════════════════════════════════════════════════════

-- 1. الجداول ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL DEFAULT '',
  category TEXT NOT NULL DEFAULT 'أخرى',
  "desc" TEXT DEFAULT '',
  price NUMERIC(10,2) NOT NULL DEFAULT 0,
  icon TEXT NOT NULL DEFAULT 'medical',
  image TEXT DEFAULT '',
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
  id BIGSERIAL PRIMARY KEY,
  customer_name TEXT DEFAULT '',
  customer_phone TEXT DEFAULT '',
  items JSONB NOT NULL DEFAULT '[]'::jsonb,
  total NUMERIC(10,2) NOT NULL DEFAULT 0,
  item_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'pending',
  notes TEXT DEFAULT '',
  reply TEXT DEFAULT '',
  replied_at TIMESTAMPTZ,
  whatsapp_url TEXT DEFAULT '',
  branch TEXT DEFAULT '',
  branch_name TEXT DEFAULT '',
  delivery_zone TEXT DEFAULT '',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS settings (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL DEFAULT 'صيدلية السلاق',
  address TEXT DEFAULT '',
  phone TEXT DEFAULT '',
  whatsapp_number TEXT DEFAULT '9705952224444',
  hours TEXT DEFAULT '7 صباحا - 11 مساء',
  whatsapp_api_token TEXT DEFAULT '',
  whatsapp_phone_id TEXT DEFAULT '',
  whatsapp_base_url TEXT DEFAULT 'https://graph.facebook.com/v17.0'
);

-- دخول columns جديدة إن لم تكن موجودة (لتحديث schemas قديمة)
ALTER TABLE products ADD COLUMN IF NOT EXISTS active BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS branch TEXT DEFAULT '';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS branch_name TEXT DEFAULT '';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_zone TEXT DEFAULT '';

-- 2. الفهارس ----------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);

-- 3. RLS صارم -----------------------------------------------------------
-- anon: يقرأ المنتجات فقط.
-- orders و settings: لا قراءة للعامة — الوصول كله عبر API حامل service_role.
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS products_select_any ON products;
DROP POLICY IF EXISTS products_select_anon ON products;
CREATE POLICY products_select_anon ON products FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS products_service_write ON products;
CREATE POLICY products_service_write ON products FOR ALL TO service_role USING (true) WITH CHECK (true);

-- إزالة السياسات القديمة المتساهلة على orders/settings إن وُجدت
DROP POLICY IF EXISTS orders_select_any ON orders;
DROP POLICY IF EXISTS settings_select_any ON settings;
DROP POLICY IF EXISTS orders_service_write ON orders;
DROP POLICY IF EXISTS settings_service_write ON settings;
DROP POLICY IF EXISTS orders_service_all ON orders;
DROP POLICY IF EXISTS settings_service_all ON settings;

CREATE POLICY orders_service_all ON orders FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY settings_service_all ON settings FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 4. البيانات الأولية ----------------------------------------------------
INSERT INTO settings (id, name, address, phone, whatsapp_number, hours)
VALUES (1, 'صيدلية السلاق', 'غزة، جنوب المول البندا', '9705952224444', '9705952224444', '7 صباحا - 11 مساء')
ON CONFLICT (id) DO NOTHING;

-- منتجات الكتالوج المعتمد (نحتفظ بالمنتجات الموجودة ولا نحذف أي تعديلات)
INSERT INTO products (id, name, category, "desc", price, icon, image, active) VALUES
  (1,  'باراسيتامول ٥٠٠ملغ × ٢٠ قرص',  'دواء',   'مسكن حراري ومضاد للالتهابات — مناسب للصداع وآلام الجسم والحمى', 12.50, 'medicine', 'img/medicine.svg', true),
  (2,  'فيتامين D3 ٤٠٠٠ وحدة × ٦٠ كبسولة', 'فيتامين', 'يدعم صحة العظام والمناعة — الجرعة اليومية الموصى بها',         32.00, 'vitamin',  'img/vitamins.svg', true),
  (3,  'فيتامين C ١٠٠٠ملغ × ٦٠ قرص',      'فيتامين', 'مضاد للأكسدة ودعم المناعة — مناسب للفصل الشتوي',                 24.50, 'vitamin',  'img/vitamins.svg', true),
  (4,  'كريم واقي شمس SPF50 PA+++ ٥٠ جم', 'بشرة',    'حماية شمسية عالية — مناسب للبشرة الطبيعية والحساسة',              45.00, 'skin',     'img/skin.svg', true),
  (5,  'سيراب السعال مع هيدروميتون × ١٢٠ مل', 'دواء', 'مضاد سعال وطارد البلغم — مناسب للكبار والصغار',                  14.50, 'medicine', 'img/medicine.svg', true),
  (6,  'حزمة فحص صباحي (ضغط + سكر)',      'أدوات',   'فحصين سريعين في الصيدلية — ضغط الدم وجلوكوز الدم',              89.00, 'tools',    'img/tools.svg', true),
  (7,  'مقياس ضغط الدم التلقائي OMRON',   'أدوات',   'للمستخدم المنزلي — شاشة رقمية ووضع اليد الأيمن',                 125.00, 'tools',   'img/tools.svg', true),
  (8,  'كريم واقي الجسم SPF50 ٢٠٠ جم',     'بشرة',    'كريم واقي جسم عالي الحماية — مناسب للماء والرياضة',              75.00, 'skin',     'img/skin.svg', true),
  (9,  'مجموعة فحوصات منزلية سريعة',       'أدوات',   'للمرضى الذين يحتاجون متابعة دورية — النتائج في دقيقة',           45.00, 'tools',    'img/tools.svg', true),
  (10, 'كركم مع البيبرين ٥٠٠ملغ × ٦٠ كبسولة', 'فيتامين', 'مضاد التهاب طبيعي — يدعم صحة المفاصل والهضم',                 38.00, 'vitamin',  'img/vitamins.svg', true),
  (11, 'صابون مضاد للبكتيريا ٤٠٠ جم',      'أدوات',   'نظافة عميقة — مناسب للعناية اليومية',                             18.00, 'tools',    'img/tools.svg', true),
  (12, 'مجموعة أدوات العناية الشخصية',     'أدوات',   'أساسيات للعناية اليومية: فرشاة، خيط تنظير، مناديل معقمة',        28.00, 'tools',    'img/tools.svg', true),
  (13, 'مرطب البشرة الجاف الطازج × ١٠٠ جم','بشرة',    'مرطب خاص بالبشرة الجافة والحساسة — بدون بارابين',                35.00, 'skin',     'img/skin.svg', true),
  (14, 'مجموعة فحوصات شاملة',              'أدوات',   '٣ فحوصات معتمدة في الصيدلية — نتيجة فورية',                      95.00, 'tools',    'img/tools.svg', true),
  (16, 'كبسولة فيتامين D3 5000 وحدة × ٩٠','فيتامين',  'فيتامين D3 عالي الجرعة — يدعم المناعة والعظام',                  45.00, 'capsule',  'img/vitamins.svg', true)
ON CONFLICT (id) DO NOTHING;

-- إعادة ضبط المتسلسلات بعد الإدخال بمعرّفات صريحة حتى لا تتصادم الإضافات الجديدة
SELECT setval(pg_get_serial_sequence('products', 'id'), COALESCE((SELECT MAX(id) FROM products), 1));
SELECT setval(pg_get_serial_sequence('settings', 'id'), COALESCE((SELECT MAX(id) FROM settings), 1));

-- 5. Trigger لـ updated_at -------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_orders_updated_at ON orders;
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();