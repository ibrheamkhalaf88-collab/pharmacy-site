"""
رقم ساببايس (Supabase SQL schema)
يُستخدم لإنشاء الجداول والسياسات والأدوار المطلوبة لمشروع صيدلية السلاق.

استخدام:
  1. افتح Supabase Dashboard → Database → SQL Editor
  2. انسخ هذا الكود وشدّه (Run)
  3. أو استخدم Supabase CLI: supabase db push

ملاحظات HAKEM:
  - الجداول بتستخدم SERIAL و BIGSERIAL للـ IDs
  - RLS (Row Level Security) مفعّل على كل الجداول
  - أناس الـ anon يقدر يقرأ products و orders بس ما يقدروا يكتبون إلا عبر APIs
  - الـ service role يقدر يكتب في كل الجداول (للـ backend admin)
"""

-- ═══════════════════════════════════════════════════════════════
-- ضبط الإعدادات العامة
-- ═══════════════════════════════════════════════════════════════
SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- ═══════════════════════════════════════════════════════════════
-- 1. جدول المنتجات (products)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS products (
    id            BIGSERIAL PRIMARY KEY,
    name          TEXT NOT NULL,                          -- اسم المنتج (عربي)
    category      TEXT NOT NULL DEFAULT 'أخرى',          -- التصنيف: دواء، فيتامين، بشرة، أدوات، أخرى
    desc          TEXT,                                   -- الوصف
    price         NUMERIC(10, 2) NOT NULL DEFAULT 0,     -- السعر بالشيكل
    icon          TEXT NOT NULL DEFAULT 'medical',        -- رمز Material Symbols
    image         TEXT,                                   -- رابط الصورة (اختياري)
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- فهرسة للتصفح السريع حسب التصنيف والسعر
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_products_name ON products USING gin(name gin_trgm_ops); -- بحث نصي (يتطلب pg_trgm)

--스만 RG (Row Level Security)
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- سياسة: أي أحد يقدر يقرأ المنتجات (للعملاء والـ frontend)
CREATE POLICY "products_select_any" ON products
    FOR SELECT
    TO anon
    USING (true);

-- سياسة: الـ service role فقط يقدر يكتب (يضيف/يعدل/يحذف)
CREATE POLICY "products_service_write" ON products
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ملاحظة: لا تفتح كتابة للـ anon إلا إذا كنتOI API endpoint خاص


-- ═══════════════════════════════════════════════════════════════
-- 2. جدول الطلبات (orders)
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS orders (
    id              BIGSERIAL PRIMARY KEY,
    customer_name   TEXT DEFAULT '',
    customer_phone  TEXT DEFAULT '',
    items           JSONB NOT NULL DEFAULT '[]'::jsonb,   -- قائمة المنتجات: [{"product_id":1,"name":"...","quantity":2,"price":12.5,"category":"دواء"}, ...]
    total           NUMERIC(10, 2) NOT NULL DEFAULT 0,
    item_count      INTEGER NOT NULL DEFAULT 0,
    status          TEXT NOT NULL DEFAULT 'pending',       -- pending, confirmed, preparing, dispatched, delivered, cancelled
    notes           TEXT DEFAULT '',
    reply           TEXT,                                   -- رد الصيدلي على الطلب
    replied_at      TIMESTAMPTZ,
    whatsapp_url    TEXT,                                   -- رابط واتساب pre-filled
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- فهرسة
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_customer_phone ON orders(customer_phone);

ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- القراءة للـ anon (للاعرض فقط)
CREATE POLICY "orders_select_any" ON orders
    FOR SELECT
    TO anon
    USING (true);

-- الكتابة للـ service role فقط
CREATE POLICY "orders_service_write" ON orders
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


-- ═══════════════════════════════════════════════════════════════
-- 3. جدول الإعدادات (settings) — جد واحد فقط
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS settings (
    id              BIGSERIAL PRIMARY KEY,
    name            TEXT NOT NULL DEFAULT 'صيدلية السلاق',       -- اسم الصيدلية
    address         TEXT DEFAULT '',                              -- العنوان
    phone           TEXT DEFAULT '',                             -- رقم الهاتف
    whatsapp_number TEXT DEFAULT '9705952224444',               -- رقم واتساب (قابل للتعديل)
    hours           TEXT DEFAULT '7 صباحًا - 11 مساءً',           -- ساعات العمل
    whatsapp_api_token TEXT DEFAULT '',                          -- WhatsApp Cloud API token (اختياري)
    whatsapp_phone_id  TEXT DEFAULT '',                          -- WhatsApp Phone ID (اختياري)
    whatsapp_base_url  TEXT DEFAULT 'https://graph.facebook.com/v17.0' -- Base URL
);

-- 插入数据初始化 (إذا الجدول فاضي)
INSERT INTO settings (id, name, address, phone, whatsapp_number, hours, whatsapp_api_token, whatsapp_phone_id, whatsapp_base_url)
SELECT 1, 'صيدلية السلاق', 'غزة، جنوب المول البندا', '9705952224444', '9705952224444', '7 صباحًا - 11 مساءً', '', '', 'https://graph.facebook.com/v17.0'
WHERE NOT EXISTS (SELECT 1 FROM settings);

ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- القراءة للـ anon
CREATE POLICY "settings_select_any" ON settings
    FOR SELECT
    TO anon
    USING (true);

-- الكتابة للـ service role فقط
CREATE POLICY "settings_service_write" ON settings
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


-- ═══════════════════════════════════════════════════════════════
-- 4. دوال مساعدة (Helper Functions)
-- ═══════════════════════════════════════════════════════════════

-- دالة لجلب إعدادات الصيدلية 변경후 JSON (مفيدة للـ API)
CREATE OR REPLACE FUNCTION get_pharmacy_settings()
RETURNS JSONB AS $$
BEGIN
    RETURN (
        SELECT jsonb_build_object(
            'name', COALESCE(name, ''),
            'address', COALESCE(address, ''),
            'phone', COALESCE(phone, ''),
            'whatsapp_number', COALESCE(whatsapp_number, ''),
            'hours', COALESCE(hours, ''),
            'whatsapp_api_token', COALESCE(whatsapp_api_token, ''),
            'whatsapp_phone_id', COALESCE(whatsapp_phone_id, ''),
            'whatsapp_base_url', COALESCE(whatsapp_base_url, '')
        )
        FROM settings
        WHERE id = 1
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- دالة agg لجلب إجمالي الطلبات اليوم
CREATE OR REPLACE FUNCTION get_daily_order_stats()
RETURNS TABLE (total_orders int, total_revenue numeric) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::int,
        COALESCE(SUM(total)::numeric, 0)::numeric
    FROM orders
    WHERE created_at >= CURRENT_DATE
      AND created_at < CURRENT_DATE + INTERVAL '1 day'
      AND status NOT IN ('cancelled');
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;


-- ═══════════════════════════════════════════════════════════════
-- 5. التحديث التلقائي لـ updated_at
-- ═══════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- تطبيق الدالة على الجداول
DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_orders_updated_at ON orders;
CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ═══════════════════════════════════════════════════════════════
-- 6. ملء البيانات الأولية (Seed data) — 15 منتج
-- ═══════════════════════════════════════════════════════════════
INSERT INTO products (name, category, desc, price, icon, image) VALUES
    ('باراسيتامول ٥٠٠ملغ × ٢٠ قرص', 'دواء', 'مسكن حراري ومضاد للالتهاب الخفيف — مناسب للصداع والحمى.', 12.50, 'pills', NULL),
    ('إيبوبروفين ٤٠٠ملغ × ٢٠ قرص', 'دواء', 'مسكن أقوى ومضاد التهاب — للألم العضلي والمفصلي.', 18.00, 'pills', NULL),
    ('أموكسيسلين ٥٠٠ملغ × ٢١ كبسولة', 'دواء', 'مضاد حيوي لالتهابات البكتيريا — بوصفة طبية.', 22.00, 'capsule', NULL),
    ('سيراب السعال ذات العشبة × ١٢٠ مل', 'دواء', 'مذيبات للبلغم ومسكنة للسعال — مناسبة للكبار والصغار.', 14.50, 'syrup', NULL),
    ('فيتامين D3 ١٠٠٠ وحدة × ٦٠ كبسولة', 'فيتامين', 'يدعم صحة العظام والمناعة — الجرعة اليومية المثالية.', 32.00, 'vitamin', NULL),
    ('فيتامين C ١٠٠٠ملغ × ٦٠ قرص', 'فيتامين', 'يعزز المناعة ويحمي من الفيروسات — استهلاك يومي مريح.', 24.00, 'vitamin', NULL),
    ('أوميغا ٣ زيت سمك × ٦٠ كبسولة', 'فيتامين', 'يدعم صحة القلب والدماغ والشعر — مصدر نقي لأوميغا ٣.', 42.00, 'vitamin', NULL),
    ('حديد + فيتامين C × ٣٠ قرص', 'فيتامين', 'مكمل الحديد — مناسب لفقر الدم والإرهاق.', 18.00, 'vitamin', NULL),
    ('كريم واقي من الشمس SPF50 × ٥٠ جم', 'بشرة', 'حماية عالية من أشعة الشمس — غير دهني، مناسب للبشرة الحساسة.', 45.00, 'sunscreen', NULL),
    ('مرطب وجه يومي براتينزا × ٥٠ جم', 'بشرة', 'يرطب ويهدئ البشرة الجافة — خالٍ من البارابين، غير كوميدوجين.', 28.00, 'cream', NULL),
    ('قنية طبية معقمة × ٣٠ قطعة', 'أدوات', 'قنية وريدية معقمة — للتوصيل الوريدي والحقن.', 12.00, 'medical', NULL),
    ('جهاز قياس ضغط الدم إلكتروني', 'أدوات', 'رقمي، شاشة كبيرة، مع بطاقة الذاكرة — دقيق ومعتمد.', 89.00, 'medical', NULL),
    ('مشرط طبي معقم × ٢٠ قطعة', 'أدوات', 'مشرط معقم فردي — لفتح الجروح الصغيرة وتنظيفها.', 3.50, 'medical', NULL),
    ('قفازات مطاطية معقمة × ١٠٠ قطعة', 'أدوات', 'قفازات لاتكس خالية من البودر — معقمة ومختومة.', 16.00, 'medical', NULL)
ON CONFLICT DO NOTHING;


-- ═══════════════════════════════════════════════════════════════
-- 7. منح الصلاحيات (Permissions)
-- ═══════════════════════════════════════════════════════════════
-- ن Muslim الـ anon و authenticated لا يقدر يكتب，我就 في الجداول
GRANT SELECT ON TABLE products, orders, settings TO anon;
GRANT SELECT ON TABLE products, orders, settings TO authenticated;

-- الـ service role يقدر يكتب في كل الجداول
GRANT ALL ON TABLE products, orders, settings TO service_role;
GRANT ALL ON FUNCTION get_pharmacy_settings, get_daily_order_stats TO service_role;
GRANT ALL ON FUNCTION update_updated_at_column TO service_role;


-- ═══════════════════════════════════════════════════════════════
-- 8. إنشاء Extension للبحث النصي الكامل (اختياري)
-- ═══════════════════════════════════════════════════════════════
-- لـ بحث متقدم عن المنتجات بالاسم
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX IF NOT EXISTS idx_products_name_trgm ON products USING gin (name gin_trgm_ops);


-- ═══════════════════════════════════════════════════════════════
-- انتهت!
-- ═══════════════════════════════════════════════════════════════
-- ملاحظة: بعد تشغيل هذا الكود، جهّز Supabase للعمل:
--   1. تأكد من إعدادات RLS أنها مناسبة لـ production
--   2. اكتفِ API keys من Settings → API
--   3. أضف SUPABASE_URL و SUPABASE_ANON_KEY و SUPABASE_SERVICE_ROLE_KEY لـ .env
--   4. ثبت supabase-py: pip install supabase
--   5. شغّل الـ MCP server: python backend/app/supabase_mcp_server.py
-- ═══════════════════════════════════════════════════════════════
