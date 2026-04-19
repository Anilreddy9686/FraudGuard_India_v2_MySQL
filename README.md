# 🛡️ Online Payment Fraud Detection
### AI-Powered Payment Fraud Detection System
**Developed by ANILREDDY | 📞 9686809509 | anilreddy@opfd.in**

MySQL · Flask · Machine Learning · Indian Rupees (₹) · Security Hardened

---

## 📦 Project Structure

```
OPFD/
├── app.py                     ← Main entry point
├── config.py                  ← MySQL + security config
├── schema.sql                 ← Optional manual DB setup
├── requirements.txt           ← Python dependencies
├── payments.pkl               ← Copy your ML model here
│
├── modules/
│   ├── db.py                  ← MySQL + auto table creation (7 tables)
│   ├── security.py            ← ALL security features (checklist)
│   ├── auth.py                ← Login · Register · Logout · Reset Password
│   ├── otp.py                 ← OTP 2-Factor Authentication
│   ├── predict.py             ← Fraud detection + INR + Dashboard
│   ├── admin.py               ← Admin panel + IP blacklist
│   ├── history.py             ← Transaction history
│   ├── analytics.py           ← Charts & statistics
│   ├── alerts.py              ← Real-time fraud alerts
│   ├── export.py              ← CSV & HTML report
│   ├── search.py              ← AJAX advanced search
│   ├── heatmap.py             ← India state-wise heatmap
│   ├── receipt.py             ← Print/share receipt
│   ├── users.py               ← All users + profile
│   └── settings.py            ← System settings
│
└── templates/
    ├── base.html              ← Sidebar layout
    ├── login.html             ← Sign-in (forgot password link)
    ├── register.html          ← Registration (strong password rules)
    ├── forgot_password.html   ← Password reset request
    ├── reset_password.html    ← New password form
    ├── blocked.html           ← IP blocked page (403)
    ├── otp_verify.html        ← 6-digit OTP page
    ├── dashboard.html         ← Home dashboard
    ├── predict.html           ← Transaction checker
    ├── result.html            ← Fraud result + receipt link
    ├── history.html           ← Paginated history
    ├── search.html            ← AJAX search & filter
    ├── analytics.html         ← Chart.js analytics
    ├── heatmap.html           ← Leaflet.js India map
    ├── receipt.html           ← Printable receipt
    ├── alerts.html            ← Fraud notifications
    ├── admin.html             ← Admin panel + IP blacklist tab
    ├── users_all.html         ← All users management
    ├── profile.html           ← Profile + OTP toggle
    └── settings.html          ← System settings
```

---

## ⚙️ Setup (4 Steps)

### 1 — Create MySQL Database
```bash
mysql -u root -p
CREATE DATABASE opfd_india CHARACTER SET utf8mb4;
EXIT;
```

### 2 — Set your MySQL password in `config.py`
```python
MYSQL_PASSWORD = "your_mysql_password"
```

### 3 — Install dependencies
```bash
pip install -r requirements.txt
```
> Linux: `sudo apt install libmysqlclient-dev python3-dev gcc`

### 4 — Run
```bash
python app.py
```
→ Open **http://localhost:5000**

---

## 🔑 Default Login
| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `Admin@123` |

---

## 🔐 Security Modules (All Implemented)

| Feature | Implementation |
|---|---|
| Login Rate Limiting | 5 failed attempts → account locked |
| Account Lockout | Configurable duration (default 15 min) |
| IP Blacklist | Admin can block any IP from admin panel |
| HttpOnly Cookies | `SESSION_COOKIE_HTTPONLY = True` |
| SameSite Cookies | `SESSION_COOKIE_SAMESITE = "Lax"` |
| Session Token Rotation | Rotated on every successful login |
| Generic Error Messages | Never reveals if username/email exists |
| Password Reset | Expiring 1-hour single-use tokens |
| Don't Reveal Email | Same message whether email exists or not |
| Invalidate Sessions After Reset | `session.clear()` on password reset |
| OTP 2-Factor Auth | 6-digit, 5-min expiry, per-user or forced |
| Server-Side Validation | All inputs validated server-side |
| SQL Injection Prevention | 100% parameterised queries |
| Suspicious Activity Alerts | Failed logins logged with IP + timestamp |
| Role-Based Access Control | `@login_required` + `@admin_required` |
| Audit Trail | Every action logged with IP |
| Strong Password Rules | 8+ chars, uppercase, number required |
| Duplicate Account Prevention | Generic error message on collision |

---

## 🗄️ Database Tables (7 total)

| Table | Purpose |
|---|---|
| `users` | Accounts with login_attempts, locked_until, reset_token |
| `transactions` | All fraud prediction records |
| `alerts` | Real-time fraud notifications |
| `audit_log` | Full activity trail with IP |
| `otp_tokens` | 2FA OTP codes with expiry |
| `system_settings` | Configurable app settings |
| `ip_blacklist` | Blocked IP addresses |

---

## 🇮🇳 Indian Fraud Rules

| Rule | Trigger | Risk |
|---|---|---|
| High-value NEFT/RTGS | PAYMENT/TRANSFER > ₹20L | +80 |
| Round-figure hawala | Amount % ₹1L = 0, ≥ ₹1L | +55 |
| Large cash-out | CASH_OUT > ₹5L | +70 |
| UPI large transfer | TRANSFER ₹1L–₹2L | +40 |
| Abnormal debit | DEBIT > ₹10L | +65 |
| Balance mismatch | Δbal ≠ amount (+₹1000) | +20 |
| Sender zeroed out | New bal = 0, old > 0 | +30 |

---

## 🌐 All Routes

```
Auth
  /login                  Sign in
  /register               Register
  /logout                 Sign out
  /forgot-password        Request reset link
  /reset-password/<token> Set new password
  /otp-verify             OTP verification

App
  /dashboard              Home
  /predict                Check transaction
  /history                Transaction history
  /search                 Search & filter (AJAX)
  /analytics              Charts
  /heatmap                India heatmap
  /alerts                 Fraud alerts
  /alerts/count           Unread count (JSON)
  /receipt/<id>           Print receipt
  /receipt/<id>/json      Receipt JSON
  /export/csv             Download CSV
  /export/report          Download HTML report
  /profile                My profile

Admin
  /admin/                 Admin dashboard
  /admin/toggle/<uid>     Toggle user active
  /admin/promote/<uid>    Promote to admin
  /admin/demote/<uid>     Demote to user
  /admin/delete_user/<uid> Delete user
  /admin/reset_password/<uid> Reset password
  /admin/delete_txn/<id>  Delete transaction
  /admin/block_ip         Block IP address
  /admin/unblock_ip/<id>  Unblock IP
  /users                  All users
  /users/delete/<uid>     Delete user
  /settings               System settings
```

---

## 📞 Indian Fraud Helplines
- **RBI**: 1800-111-109
- **Cyber Crime**: cybercrime.gov.in
- **NPCI/UPI**: 1800-120-1740

---

**Developed by ANILREDDY | 📞 9686809509 | anilreddy@opfd.in**
