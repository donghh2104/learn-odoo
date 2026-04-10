# Tài liệu Hệ thống: Module Quản lý Bất động sản (Estate)

Tài liệu này mô tả phiên bản mở rộng của module `estate` trên Odoo 14, phục vụ mục tiêu học toàn diện các thành phần cốt lõi: ORM, Security, Automation, Wizard, API và Testing.

---

## 📂 1) Cấu trúc chính

```text
custom_addons/estate/
├── __manifest__.py
├── models/
│   ├── estate_property.py
│   ├── estate_property_offer.py
│   ├── estate_property_type.py
│   ├── estate_property_tag.py
│   └── res_partner.py
├── controllers/
│   └── api_controller.py
├── wizards/
│   ├── estate_property_offer_wizard.py
│   └── estate_property_offer_wizard_views.xml
├── security/
│   ├── security.xml
│   └── ir.model.access.csv
├── data/
│   ├── estate_sequence_data.xml
│   ├── estate_property_type_data.xml
│   ├── estate_cron.xml
│   └── estate_demo.xml
├── views/
│   ├── estate_property_views.xml
│   ├── estate_property_offer_views.xml
│   ├── estate_property_type_views.xml
│   ├── estate_property_tag_views.xml
│   ├── res_partner_views.xml
│   └── estate_menus.xml
├── reports/
│   ├── estate_property_report.xml
│   └── estate_property_report_templates.xml
└── tests/
    ├── __init__.py
    └── test_estate_flow.py
```

---

## 🏗 2) ORM & Business Logic nâng cao

### `estate.property`
- Kế thừa `mail.thread`, `mail.activity.mixin` để học **chatter + activities**.
- Thêm `reference` tự sinh qua sequence `estate.property`.
- Bổ sung tracking cho các field quan trọng (`state`, `expected_price`, `selling_price`, `salesperson_id`, ...).
- Có action nghiệp vụ:
  - `action_sold()`
  - `action_cancel()`
  - `action_set_to_new()`
- Có cron method:
  - `_cron_schedule_stale_property_activities()` tạo To-do cho BĐS tồn đọng.

### `estate.property.offer`
- Khi tạo offer mới, nếu BĐS đang `new` thì tự chuyển `offer_received`.
- Chặn tạo/chấp nhận offer trên BĐS đã `sold/canceled`.
- `action_accept()` cập nhật BĐS (buyer, selling_price, state) và ghi log chatter.
- `action_refuse()` ghi log chatter.
- Có cron method `_cron_notify_expiring_offers()` để nhắc offer sắp hết hạn.

---

## ⚙️ 3) Automation (Scheduled Actions)

Trong `data/estate_cron.xml`:
- **Estate - Follow-up stale properties**
- **Estate - Notify expiring offers**

Mục đích học:
- Cách tạo `ir.cron`
- Cách tách business logic thành method cron-friendly
- Cách tạo activity tự động cho người phụ trách

---

## 🧙 4) Wizard nâng cao

`estate.property.offer.wizard` hỗ trợ:
- Tạo offer hàng loạt theo danh sách BĐS
- Áp dụng `discount_percent`
- Chỉnh `validity`
- Ghi `note` vào chatter
- Trả `display_notification` sau khi xử lý

---

## 🛡 5) Security & Access

### Groups
- `group_estate_user` (Agent)
- `group_estate_manager` (Manager)
- `group_estate_auditor` (Auditor - read-only)

### Rules
- Agent: chỉ thấy BĐS mình phụ trách hoặc chưa có người phụ trách.
- Manager: thấy toàn bộ.
- Auditor: thấy toàn bộ (kết hợp access read-only).

### Access CSV
- Auditor có quyền đọc (`perm_read=1`) và không có quyền sửa/tạo/xóa trên model nghiệp vụ.

---

## 🌐 6) REST API + JWT (học integration)

Controller: `controllers/api_controller.py`

### Điểm chính
- JWT auth qua `Authorization: Bearer <token>`
- Response envelope chuẩn:
  - `status`
  - `message`
  - `data`
  - `errors`
  - `meta`
- Hỗ trợ paging/filter/sort cho list API

### Endpoint tiêu biểu
- `POST /api/v1/auth/login`
- `GET /api/v1/properties`
- `GET /api/v1/properties/<id>`
- `POST /api/v1/properties`
- `PUT /api/v1/properties/<id>`
- `DELETE /api/v1/properties/<id>`
- `POST /api/v1/properties/<id>/action/sold`
- `POST /api/v1/offers/<id>/action/accept`
- `POST /api/v1/offers/<id>/action/refuse`
- `GET /api/v1/properties/<id>/image`

---

## 🧪 7) Test

Đã thêm test SavepointCase:
- `tests/test_estate_flow.py`

Kịch bản test:
1. Tạo BĐS mới -> tạo offer -> accept -> sold.
2. Validate rule 90% (offer quá thấp phải lỗi `ValidationError`).

---

## 🚀 8) Lệnh chạy khuyến nghị

```bash
python odoo-bin -c odoo.conf -u estate --stop-after-init
python odoo-bin -c odoo.conf --test-enable --test-tags estate --stop-after-init
```

> Gợi ý: sau khi update module, vào Technical > Automation để kiểm tra cron và chạy thử manually.
