# Sahakari MIS v1.1 – Cooperative Management System

## Requirements
- Python 3.9+ (no extra packages; Pillow optional for member photo display)

## Run
    python main.py

## Default login
    Username: admin    Password: admin123

## Forgot Password
- Click "Forgot Password?" on the login screen.
- Tab 1 (Reset via Admin): provide any admin's username+password to reset another user.
- Tab 2 (Emergency Recovery): master code is  SAHAKARI@RESET  — keep this confidential.

## Share Certificate
- Landscape certificate with green zigzag border, red inner border,
  Nepali field labels, cooperative seal watermark, and signature lines.
- Click "Print Certificate" in Share Records after selecting a row.

## Files
  main.py         – Login, Forgot-Password dialog, main shell
  database.py     – SQLite schema, helpers, atomic transactions
  styles.py       – Colours, fonts, ttk style configuration
  dashboard.py    – Summary cards & quick-stats
  members.py      – Member registration, photo/document upload
  shares.py       – Share purchase, transfer, certificate printing
  savings.py      – Savings accounts, deposit/withdraw, interest calc
  loans.py        – Loan application, approval, repayment, EMI calc
  accounting.py   – Chart of accounts, journal entries, trial balance, P&L
  transactions.py – Daily voucher register
  reports.py      – Printable reports

## Uploads
  photos/documents are copied to  sahakari-mis/uploads/  automatically.

## Recovery code (KEEP SAFE)
  SAHAKARI@RESET
