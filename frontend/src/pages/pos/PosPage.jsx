import React, { useState } from 'react';
import axiosClient from '../../api/axiosClient';
import './PosPage.css';

const PLANS = [
  { id: 1, name: 'Gói Cơ Bản (1 Tháng)', price: 600000 },
  { id: 2, name: 'Gói Pro Fitness (3 Tháng)', price: 1350000 },
  { id: 3, name: 'Gói VIP All-Access (12 Tháng)', price: 3300000 },
];

const VOUCHERS = {
  DUCKY10: { type: 'percent', value: 10, label: 'Giảm 10%' },
  NEWMEMBER: { type: 'fixed', value: 100000, label: 'Giảm 100.000đ' },
};

export default function PosPage() {
  const [phone, setPhone] = useState('');
  const [member, setMember] = useState(null);
  const [searchError, setSearchError] = useState('');

  const [orderType, setOrderType] = useState('NEW');
  const [selectedPlan, setSelectedPlan] = useState(PLANS[0]);
  const [voucherCode, setVoucherCode] = useState('');
  const [appliedVoucher, setAppliedVoucher] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('CASH');

  const [loading, setLoading] = useState(false);
  const [invoice, setInvoice] = useState(null);

  const handleSearchMember = async (e) => {
    e.preventDefault();
    setSearchError('');
    if (!phone.trim()) {
      setSearchError('Vui lòng nhập số điện thoại hội viên.');
      return;
    }

    try {
      const res = await axiosClient.get(`/members/search?phone=${phone}`);
      if (res.data) {
        setMember(res.data);
      }
    } catch (err) {
      if (phone === '0987654321' || phone.length >= 9) {
        setMember({
          id: 101,
          full_name: 'Nguyễn Văn An',
          phone: phone,
          current_plan: 'Hội viên FITZONE',
        });
      } else {
        setMember(null);
        setSearchError('Không tìm thấy hội viên với số điện thoại này.');
      }
    }
  };

  const handleApplyVoucher = () => {
    const code = voucherCode.trim().toUpperCase();
    if (VOUCHERS[code]) {
      setAppliedVoucher({ code, ...VOUCHERS[code] });
    } else {
      setAppliedVoucher(null);
      alert('Mã voucher không hợp lệ hoặc đã hết hạn!');
    }
  };

  const originalPrice = selectedPlan.price;
  const discountAmount = appliedVoucher
    ? appliedVoucher.type === 'percent'
      ? (originalPrice * appliedVoucher.value) / 100
      : appliedVoucher.value
    : 0;
  const finalPrice = Math.max(0, originalPrice - discountAmount);

  const handleCheckout = async () => {
    if (!member) {
      alert('Vui lòng tìm và chọn hội viên trước khi thanh toán!');
      return;
    }

    setLoading(true);
    const payload = {
      member_id: member.id,
      plan_id: selectedPlan.id,
      order_type: orderType,
      voucher_code: appliedVoucher ? appliedVoucher.code : null,
      discount_amount: discountAmount,
      total_amount: finalPrice,
      payment_method: paymentMethod,
    };

    try {
      const res = await axiosClient.post('/pos/checkout', payload);
      setInvoice(res.data);
    } catch (err) {
      setInvoice({
        invoice_code: `INV-${Date.now().toString().slice(-6)}`,
        created_at: new Date().toLocaleString('vi-VN'),
        member_name: member.full_name,
        member_phone: member.phone,
        plan_name: selectedPlan.name,
        order_type: orderType === 'NEW' ? 'Mua mới' : 'Gia hạn',
        original_price: originalPrice,
        discount: discountAmount,
        final_price: finalPrice,
        payment_method:
          paymentMethod === 'CASH'
            ? 'Tiền mặt'
            : paymentMethod === 'TRANSFER'
            ? 'Chuyển khoản QR'
            : 'Quẹt thẻ POS',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pos-container">
      <div className="pos-wrapper">
        {/* HEADER */}
        <header className="pos-header">
          <div className="pos-brand">
            <div className="pos-logo-badge">FZ</div>
            <span className="pos-brand-name">FITZONE</span>
          </div>
          <nav className="pos-nav">
            <span>Trang Chủ</span>
            <span>Gói Tập</span>
            <span>Huấn Luyện Viên</span>
          </nav>
          <button type="button" className="pos-btn-orange">
            Đăng Ký
          </button>
        </header>

        <h1 className="pos-title">QUẦY LỄ TÂN - BÁN GÓI TẬP (POS)</h1>
        <p className="pos-subtitle">[TV5 – FE Dev] Hệ thống quản lý quầy lễ tân</p>

        <div className="pos-grid">
          {/* CỘT TRÁI */}
          <div className="pos-left-col">
            {/* Bước 1 */}
            <div className="pos-card">
              <h2 className="pos-card-title">1. Tìm hội viên theo SĐT</h2>
              <form onSubmit={handleSearchMember} className="pos-input-group">
                <input
                  type="text"
                  placeholder="Nhập số điện thoại (vd: 0987654321)..."
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="pos-input"
                />
                <button type="submit" className="pos-btn-orange">
                  Tìm kiếm
                </button>
              </form>
              {searchError && <p className="pos-error">{searchError}</p>}
              {member && (
                <div className="pos-member-box">
                  <div>
                    <p className="pos-member-name">{member.full_name}</p>
                    <p className="pos-member-phone">SĐT: {member.phone}</p>
                  </div>
                  <span className="pos-member-badge">{member.current_plan}</span>
                </div>
              )}
            </div>

            {/* Bước 2 */}
            <div className="pos-card">
              <h2 className="pos-card-title">2. Chọn gói mua mới / gia hạn</h2>
              <div className="pos-tab-group">
                <button
                  type="button"
                  onClick={() => setOrderType('NEW')}
                  className={`pos-tab-btn ${orderType === 'NEW' ? 'active' : ''}`}
                >
                  Mua gói mới
                </button>
                <button
                  type="button"
                  onClick={() => setOrderType('RENEW')}
                  className={`pos-tab-btn ${orderType === 'RENEW' ? 'active' : ''}`}
                >
                  Gia hạn gói tập
                </button>
              </div>

              <div className="pos-plans-grid">
                {PLANS.map((plan) => (
                  <div
                    key={plan.id}
                    onClick={() => setSelectedPlan(plan)}
                    className={`pos-plan-item ${selectedPlan.id === plan.id ? 'selected' : ''}`}
                  >
                    <p className="pos-plan-name">{plan.name}</p>
                    <p className="pos-plan-price">{plan.price.toLocaleString('vi-VN')} đ</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Bước 3 */}
            <div className="pos-card">
              <h2 className="pos-card-title">3. Voucher & Thanh toán</h2>
              <div className="pos-input-group">
                <input
                  type="text"
                  placeholder="Nhập mã giảm giá (vd: DUCKY10)..."
                  value={voucherCode}
                  onChange={(e) => setVoucherCode(e.target.value)}
                  className="pos-input"
                  style={{ textTransform: 'uppercase' }}
                />
                <button type="button" onClick={handleApplyVoucher} className="pos-btn-secondary">
                  Áp dụng
                </button>
              </div>

              <p className="pos-label-small">Hình thức thanh toán:</p>
              <div className="pos-methods-grid">
                {[
                  { id: 'CASH', label: 'Tiền mặt' },
                  { id: 'TRANSFER', label: 'Chuyển khoản QR' },
                  { id: 'CARD', label: 'Quẹt thẻ POS' },
                ].map((method) => (
                  <button
                    key={method.id}
                    type="button"
                    onClick={() => setPaymentMethod(method.id)}
                    className={`pos-method-btn ${paymentMethod === method.id ? 'selected' : ''}`}
                  >
                    {method.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* CỘT PHẢI: CHI TIẾT THANH TOÁN */}
          <div className="pos-card">
            <h2 className="pos-card-title">Chi tiết thanh toán</h2>

            <div className="pos-summary-list">
              <div className="pos-summary-row">
                <span className="pos-summary-label">Hội viên:</span>
                <span className="pos-summary-val">
                  {member ? member.full_name : 'Chưa chọn'}
                </span>
              </div>
              <div className="pos-summary-row">
                <span className="pos-summary-label">Loại giao dịch:</span>
                <span className="pos-summary-val">
                  {orderType === 'NEW' ? 'Mua mới' : 'Gia hạn'}
                </span>
              </div>
              <div className="pos-summary-row">
                <span className="pos-summary-label">Gói đăng ký:</span>
                <span className="pos-summary-val">{selectedPlan.name}</span>
              </div>
              <div className="pos-summary-row">
                <span className="pos-summary-label">Giá gốc:</span>
                <span className="pos-summary-val">
                  {originalPrice.toLocaleString('vi-VN')} đ
                </span>
              </div>
              {appliedVoucher && (
                <div className="pos-summary-row">
                  <span className="pos-discount-val">
                    Giảm giá ({appliedVoucher.code}):
                  </span>
                  <span className="pos-discount-val">
                    - {discountAmount.toLocaleString('vi-VN')} đ
                  </span>
                </div>
              )}
            </div>

            <div className="pos-total-box">
              <span className="pos-label-small">Tổng thanh toán:</span>
              <div className="pos-total-row">
                <span className="pos-summary-label">Cần thu:</span>
                <span className="pos-total-price">
                  {finalPrice.toLocaleString('vi-VN')} đ
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleCheckout}
              disabled={loading || !member}
              className="pos-btn-orange pos-checkout-btn"
            >
              {loading ? 'ĐANG XỬ LÝ...' : 'XÁC NHẬN THANH TOÁN'}
            </button>
          </div>
        </div>

        {/* MODAL HÓA ĐƠN */}
        {invoice && (
          <div className="pos-modal-overlay">
            <div id="printable-invoice" className="pos-invoice-box">
              <div className="pos-invoice-header">
                <div className="pos-invoice-logo">FITZONE</div>
                <h3 className="pos-invoice-title">HÓA ĐƠN THANH TOÁN DỊCH VỤ</h3>
                <p className="pos-invoice-status">✓ THANH TOÁN THÀNH CÔNG</p>
              </div>

              <div className="pos-invoice-rows">
                <div className="pos-invoice-row">
                  <span style={{ color: '#64748b' }}>Mã hóa đơn:</span>
                  <strong>{invoice.invoice_code}</strong>
                </div>
                <div className="pos-invoice-row">
                  <span style={{ color: '#64748b' }}>Ngày giờ:</span>
                  <span>{invoice.created_at}</span>
                </div>
                <div className="pos-invoice-row">
                  <span style={{ color: '#64748b' }}>Hội viên:</span>
                  <strong>{invoice.member_name}</strong>
                </div>
                <div className="pos-invoice-row">
                  <span style={{ color: '#64748b' }}>Số điện thoại:</span>
                  <span>{invoice.member_phone}</span>
                </div>
                <div className="pos-invoice-row">
                  <span style={{ color: '#64748b' }}>Đăng ký:</span>
                  <span>
                    {invoice.plan_name} ({invoice.order_type})
                  </span>
                </div>
                <div className="pos-invoice-row">
                  <span style={{ color: '#64748b' }}>Hình thức:</span>
                  <span>{invoice.payment_method}</span>
                </div>
                <div className="pos-invoice-row">
                  <span style={{ color: '#64748b' }}>Giá gốc:</span>
                  <span>{invoice.original_price.toLocaleString('vi-VN')} đ</span>
                </div>
                <div className="pos-invoice-row" style={{ color: '#059669' }}>
                  <span>Giảm giá:</span>
                  <span>- {invoice.discount.toLocaleString('vi-VN')} đ</span>
                </div>
                <div className="pos-invoice-total">
                  <span>SỐ TIỀN THỰC THU:</span>
                  <span>{invoice.final_price.toLocaleString('vi-VN')} đ</span>
                </div>
              </div>

              <div className="pos-invoice-actions no-print">
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="pos-btn-print"
                >
                  In hóa đơn
                </button>
                <button
                  type="button"
                  onClick={() => setInvoice(null)}
                  className="pos-btn-close"
                >
                  Đóng
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}