/**
 * WhatsApp order module
 * يبني رسالة واتساب جاهزة للإرسال مع كل منتجات السلة
 */
const WhatsAppOrder = {
  PHARMACY_NUMBER: '9705952224444', // ← غيّرها للرقم الحقيقي

  buildMessage() {
    const items = Cart.getItems();
    if (items.length === 0) return '';

    const lines = [];
    lines.push('🛒 *طلب من صيدلية السلاق*');
    lines.push('━━━━━━━━━━━━━━━━━━');
    items.forEach(item => {
      lines.push(`· ${item.name}`);
      lines.push(`  السعر: ${item.price.toFixed(2)} شيكل × ${item.qty}`);
    });
    lines.push('━━━━━━━━━━━━━━━━━━');

    const total = Cart.getTotal();
    lines.push(`*المجموع:* ${total.toFixed(2)} شيكل`);
    lines.push('');
    lines.push('_اسم العميل:_ ');
    lines.push('_رقم الهاتف:_ ');
    lines.push('');
    lines.push('صيدلية السلاق — شارع الجلاء');
    lines.push('مفتوح 24 ساعة يومياً');

    return lines.join('\n');
  },

  getURL() {
    const message = this.buildMessage();
    if (!message) return '#';
    const encoded = encodeURIComponent(message);
    return `https://wa.me/${this.PHARMACY_NUMBER}?text=${encoded}`;
  }
};
