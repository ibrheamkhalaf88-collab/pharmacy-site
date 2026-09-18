-- ═══════════════════════════════════════════════
-- صيدلية السلاق — Supabase Schema (clean)
-- ═══════════════════════════════════════════════
-- افتح: https://supabase.com/dashboard/project/vsffmvrpuwhodgqpjzcg/sql
-- الصق هاد، اضغط Run
-- ═══════════════════════════════════════════════

-- 1. الجداول
CREATE TABLE IF NOT EXISTS products (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL DEFAULT '',
  category TEXT NOT NULL DEFAULT 'أخرى',
  desc TEXT DEFAULT '',
  price NUMERIC(10,2) NOT NULL DEFAULT 0,
  icon TEXT NOT NULL DEFAULT 'medical',
  image TEXT DEFAULT '',
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

-- 2. الفهارس
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at DESC);

-- 3. RLS
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS products_select_any ON products FOR SELECT TO anon USING (true);
CREATE POLICY IF NOT EXISTS products_service_write ON products FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY IF NOT EXISTS orders_select_any ON orders FOR SELECT TO anon USING (true);
CREATE POLICY IF NOT EXISTS orders_service_write ON orders FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY IF NOT EXISTS settings_select_any ON settings FOR SELECT TO anon USING (true);
CREATE POLICY IF NOT EXISTS settings_service_write ON settings FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 4. البيانات الأولية
INSERT INTO settings (id, name, address, phone, whatsapp_number, hours)
VALUES (1, 'صيدلية السلاق', 'غزة، جنوب المول البندا', '9705952224444', '9705952224444', '7 صباحا - 11 مساء')
ON CONFLICT (id) DO NOTHING;

-- 5. Trigger
CREATE OR REPLACE FUNCTION update_updated_at_column() RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_orders_updated_at ON orders;
CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();