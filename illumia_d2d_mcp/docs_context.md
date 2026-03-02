# Illumia / Transact / CBORD Product Documentation

> Bundled reference context for the Illumia D2D MCP tools.
> This file is shipped inside the Python package and queried by `query_illumia_docs`.

---

## Quickcharge by Transact

Quickcharge is the campus commerce transaction-processing platform. It powers
point-of-sale, self-service, vending, and mobile commerce across dining,
retail, and auxiliary services.

### Core Components

| Component | Description |
|---|---|
| **Quickcharge Server** | Central transaction hub; processes all tender types, manages accounts, and feeds reporting. Deployed on-premises or hosted. |
| **POS Desktop** | Full-featured cashier terminal for dining halls, retail, and convenience stores. Supports campus card, credit/debit, meal plan, declining balance, and payroll deduction. |
| **Self-Service Kiosk** | Unattended ordering and payment terminal. Touch screen with NFC reader. Ideal for coffee bars, grab-and-go, and after-hours service. |
| **Cashless Vending** | Retrofit adapter that adds NFC campus-card and mobile-wallet acceptance to existing vending machines. Eliminates cash handling. |
| **Mobile Ordering** | White-label mobile app for order-ahead and contactless pickup. Integrates with CBORD Menu Management for real-time menus and nutritional data. |

### Payment Types

- **Campus Card (NFC):** contactless tap via physical or mobile credential.
- **Meal Plan / Declining Balance:** managed by Quickcharge account engine.
- **Credit / Debit:** EMV chip + contactless via integrated payment gateway.
- **Payroll Deduction:** post-tax employee purchases reconciled through payroll system (Kronos, ADP, Workday).
- **Guest / Visitor Accounts:** pre-loaded value or credit card on file.

### Integrations

- **CBORD Menu Management:** bi-directional menu sync (items, pricing,
  nutrition, allergens). Used by Mobile Ordering and digital menu boards.
- **Payroll Systems (Kronos, ADP, Workday):** batch or real-time deduction
  feeds for employee purchases.
- **Student Information Systems:** enrollment-driven meal plan assignment.
- **ERP / Finance:** GL posting, revenue allocation, reconciliation.

---

## Campus ID – Mobile Credential by Transact

Mobile Credential replaces physical campus ID cards with a smartphone-based
digital identity stored in Apple Wallet and Google Wallet.

### Key Benefits
- **Eliminate plastic cards:** no printing, no replacement fees, no badge
  printers to maintain.
- **Instant provisioning:** credentials pushed to student phones at enrollment.
- **Multi-function:** door access, dining, library, rec center, transit,
  laundry, printing—all from one mobile credential.
- **Higher security:** biometric unlock on phone vs. easily cloned mag-stripe.

### Triggers to Look For
- Physical ID card programs with high replacement costs.
- Badge printer maintenance contracts.
- Separate door-access and dining-card systems.
- Student satisfaction complaints about carrying physical cards.

---

## Campus Commerce – Transact Insights

Transact Insights is a unified analytics and reporting platform that
consolidates transaction data across all campus commerce touch points.

### Key Benefits
- **Cross-location visibility:** single dashboard for all dining, retail,
  vending, and auxiliary revenue.
- **Menu performance:** item-level sales, waste tracking, and trend analysis.
- **Peak utilization:** heat maps of transaction volume by location, day, and
  hour.
- **Financial reconciliation:** automated GL posting and variance reporting.

### Triggers to Look For
- No unified reporting across dining sites.
- Manual Excel-based reconciliation.
- Inability to compare location performance.
- No visibility into menu item profitability.

---

## Integrated Payments – Sponsor Payments

Integrated Payments unifies all payment tender types into a single
processing layer, including sponsor (third-party) payments such as
visitor meal programs, conference billing, and departmental charge-backs.

### Key Benefits
- **Unified tender processing:** one reconciliation workflow for campus card,
  credit, meal plan, payroll deduct, and sponsor billing.
- **Auto-reconciliation:** eliminates manual payroll deduction matching.
- **Sponsor billing:** departments, conferences, and visiting groups can fund
  meals and services without per-transaction manual entry.
- **Compliance:** PCI DSS scope reduction through tokenized payment flows.

### Triggers to Look For
- Separate payroll deduction reconciliation process.
- Manual departmental charge-back workflows.
- Conference or visitor meal billing handled outside the system.
- Multiple payment processors with separate reporting.

---

## Architecture Patterns

### Typical Small Campus (< 5 locations)
- 1 Quickcharge Server (hosted)
- POS Desktop terminals at each location
- Campus Card NFC readers
- CBORD Menu Management integration

### Typical Mid-Size Campus (5-15 locations)
- 1 Quickcharge Server (on-prem or hosted)
- Mix of POS Desktop, Self-Service Kiosks, and Cashless Vending
- Mobile Ordering app
- Payroll Deduction module
- Transact Insights reporting
- Campus ID mobile credential

### Typical Large Campus (15+ locations)
- Quickcharge Server cluster (HA)
- Full hardware suite: POS, Kiosks, Vending, Mobile
- Integrated Payments with all tender types
- Campus ID mobile credential with door access
- Transact Insights with custom dashboards
- Multiple payroll and ERP integrations
