# 📘 CCR Master Override Register & Shutdown Log – User Manual  
*For Congo FLNG CCR Operations – Version 3.0*  
*Document ID: CCR-MANUAL-3.0 | Approved: February 2026 | CONFIDENTIAL*

<a name="toc"></a>
## 📌 Table of Contents
1. [System Overview](#system-overview)  
2. [Access & Login](#access-login)  
3. [User Roles & Permissions](#user-roles)  
4. [Main Interface Guide](#main-interface)  
   - [Override Register Tab](#override-register)  
   - [Visual Status Guide](#visual-status)  
5. <a name="shutdown-log-section"></a>[📝 SHUTDOWN LOG Tab](#shutdown-log)  
   - [Logging Shutdown Events](#log-shutdown)  
   - [Editing Existing Events](#edit-shutdown)  
   - [Export & Email Functions](#shutdown-export)  
6. [📧 Email Functions](#email-functions)  
   - [Send Overrides Report](#send-overrides)  
   - [Send Shutdown Report](#send-shutdown)  
   - [Custom Email Recipients](#custom-email)  
7. <a name="scheduler-section"></a>[⏰ Automated Scheduler](#scheduler)  
   - [Integrated Daily Reports](#integrated-reports)  
   - [Report Contents](#report-contents)  
   - [Schedule & Timezone](#schedule-timezone)  
8. [Admin Functions](#admin-functions)  
9. [Troubleshooting](#troubleshooting)  
10. [Security & Best Practices](#security)  
11. [Appendices](#appendices)  
    - [Priority Risk Matrix](#priority-matrix)  
    - [Tag Number Formats](#tag-formats)  
    - [Shift Handover Checklist](#handover-checklist)  

---

<a name="system-overview"></a>
## 🔒 System Overview
The **CCR Master Override Register** is a dual-module digital log for:
- 📋 **FGS Override Register**: Tracks all Fire & Gas System bypasses
- 📝 **SHUTDOWN LOG**: Records all unplanned/planned plant shutdown events

**Critical Features**:
- ✅ Real-time visibility with color-coded status indicators
- ✅ Automated daily email reports (05:00 & 17:00 Congo Time)
- ✅ Integrated reports combining Overrides + Shutdown Logs
- ✅ Permanent audit trail (no deletion of Shutdown records)
- ✅ A3 PDF exports with multi-line text support
- ✅ LAN access across facility network

> ℹ️ **Regulatory Compliance**: Meets FLNG Safety Procedures SP-FGS-003 (Overrides) and SP-SHUT-001 (Shutdown Logs)

---

<a name="access-login"></a>
## 🔑 Access & Login
| Location | URL |
|----------|-----|
| **CCR Workstations** | `http://<SERVER-IP>:7860` *(Ask Supervisor for current IP)* |
| **Field Tablets** | Same URL (must be on facility Wi-Fi) |
| **Alternative** | `http://inst.local:7860` *(if mDNS configured)* |

**Login Credentials**:
| Role | Username | Password | When to Use |
|------|----------|----------|-------------|
| **Operator** | `user` | `user` | Logging new overrides/shutdowns |
| **Shift Supervisor** | `manager` | `manager` | Approving overrides, managing shutdowns |
| **Instrument Engineer** | `admin` | `admin` | Bulk imports, system maintenance |

> 🔒 **Security Requirements**:  
> - Always **log out** when leaving workstation (click 🚪 Logout)  
> - Never share credentials – each operator must use own login  
> - Change default passwords via Windows Security → Local Users  

---

<a name="user-roles"></a>
## 👥 User Roles & Permissions
| Action | Operator (`user`) | Supervisor (`manager`) | Engineer (`admin`) |
|--------|-------------------|------------------------|--------------------|
| **View all entries** | ✅ | ✅ | ✅ |
| **Create new override** | ✅ | ✅ | ✅ |
| **Create shutdown event** | ✅ | ✅ | ✅ |
| **Approve override** (`Approved=YES`) | ❌ | ✅ | ✅ |
| **Close override** (`Closed=YES`) | ❌ | ✅ | ✅ |
| **Edit shutdown event** | ❌ | ✅ | ✅ |
| **Delete override** | ❌ | ✅ | ✅ |
| **Export to Excel/PDF** | ✅ | ✅ | ✅ |
| **Email reports** | ✅ | ✅ | ✅ |
| **Import Excel data** | ❌ | ❌ | ✅ |
| **Access Admin Panel** | ❌ | ❌ | ✅ |

---

<a name="main-interface"></a>
## 💻 Main Interface Guide
<a name="override-register"></a>
### 📋 Override Register Tab
*Full documentation in [Visual Status Guide](#visual-status)*

<a name="visual-status"></a>
### 🎨 Visual Status Guide
The table uses **color-coded rows** for instant status recognition:

| Color | Condition | Meaning | Required Action |
|-------|-----------|---------|-----------------|
| **🟡 Yellow** | `Approved = NO` | Pending supervisor approval | Supervisor must review before shift handover |
| **🟢 Light Green** | `Approved = YES`<br>`Closed = NO` | Active approved override | Monitor until physically cleared |
| **⚪ Light Gray** | `Approved = YES`<br>`Closed = YES` | Completed/closed override | Archived – no action needed |

> 💡 **Pro Tip**: During shift handover, focus on **yellow rows** first – these require immediate approval attention.

---

<a name="shutdown-log"></a>
## 📝 SHUTDOWN LOG Tab
*Log all unplanned/planned shutdown events. All entries are permanent audit records (no deletion allowed).*

<a name="log-shutdown"></a>
### ➕ Logging a New Shutdown Event
1. Click **"➕ Add New Event"** button below the table  
2. Fill **required fields** (marked with ✅):  
   - ✅ **Event Description**: Full technical reason (e.g., *"Unplanned shutdown of Train A due to high pressure in cold box"*)  
   - ✅ **First Cause**: Root cause analysis (e.g., *"Faulty pressure transmitter 77PT-1234"*)  
   - ✅ **Reported By**: Your name/role  
3. Optional fields:  
   - **Issues and next steps**: Action items (e.g., *"1. Replace transmitter by 04-Feb\n2. Review calibration procedure"*)  
   - **Action by**: Responsible team/person  
4. Click **"✅ Add New Event"**  
5. ✅ **Confirmation**: Green status message + event appears in table with auto-generated ID  

> ⚠️ **Critical Rule**:  
> Shutdown records **CANNOT BE DELETED** per FLNG Safety Procedure SP-SHUT-001. Only corrections via "Edit Event" are permitted.

<a name="edit-shutdown"></a>
### ✏️ Editing Existing Shutdown Events
1. Select event ID from **"Select Event ID to Edit"** dropdown  
2. Click **"✏️ Load Selected Event"**  
3. Modify fields as needed:  
   - Update **Issues and next steps** with progress  
   - Add **Action by** / **Reported by** if missing  
4. Click **"💾 Update Event"**  
5. ✅ **Confirmation**: Event updated with same ID (audit trail preserved)  

> 🔒 **Security Note**:  
> Only `manager` and `admin` roles can edit shutdown events. Operators see fields as read-only.

<a name="shutdown-export"></a>
### 📤 Export & Email Functions (Shutdown Log)
| Button | Function | Output |
|--------|----------|--------|
| **📤 Export to Excel** | Full shutdown log export | `ShutdownLog_Export_YYYYMMDD_HHMMSS.xlsx` |
| **🖨️ Export to PDF (A3)** | Professional A3 report with multi-line text | `ShutdownLog_A3_YYYYMMDD_HH-MM-SS.pdf` |
| **✉️ Send by Email (Managers)** | Email exports to managers in `emails.txt` | 2 attachments + Congo FLNG IP address |

**To email shutdown reports**:  
1. Click **"✉️ Send by Email (Managers)"**  
2. ✅ Status shows: *"Email sent to X recipient(s)! (ShutdownLog_Export_..., ShutdownLog_A3_...)"*  
3. Managers receive email with:  
   - `SHUTDOWN_LOG_FULL_EXPORT.xlsx`  
   - `SHUTDOWN_LOG_CURRENT_VIEW.pdf`  
   - Congo FLNG IP address in footer  
   - Timestamp of export  

---

<a name="email-functions"></a>
## 📧 Email Functions
<a name="send-overrides"></a>
### ✉️ Send Overrides Report (Main Register Tab)
1. Go to **"📋 Main Register"** tab  
2. Click **"✉️ Send by Email (Managers)"**  
3. Managers receive:  
   - `OVERRIDES_FULL_DATABASE.xlsx`  
   - `OVERRIDES_CURRENT_VIEW.pdf` (A3 with color-coded status)  

<a name="send-shutdown"></a>
### ✉️ Send Shutdown Report (Shutdown Log Tab)
1. Go to **"📝 SHUTDOWN LOG"** tab  
2. Click **"✉️ Send by Email (Managers)"**  
3. Managers receive:  
   - `SHUTDOWN_LOG_FULL_EXPORT.xlsx`  
   - `SHUTDOWN_LOG_CURRENT_VIEW.pdf` (A3 with multi-line text)  

<a name="custom-email"></a>
### 📧 Custom Email Recipients
1. Go to **"📧 Custom Email"** tab  
2. Enter emails (one per line):  
```
manager1@congoflng.com
supervisor2@wison.com
hse@congoflng.com
```

3. (Optional) Add note in **"Optional Note"** field (e.g., *"Shift handover report - 06:00"*)  
4. Click **"📤 Send Custom Email"**  
5. ✅ Status confirms delivery with attachment names  

> 🔒 **Security**: Attachments contain CONFIDENTIAL operational data. Only send to authorized Congo FLNG personnel.

---

<a name="scheduler"></a>
## ⏰ Automated Scheduler
<a name="integrated-reports"></a>
### 📬 Integrated Daily Reports
The system automatically sends **combined reports** at:  
- **🌅 05:00 Congo Time** (Start of day shift)  
- **🌇 17:00 Congo Time** (Start of night shift)  

**Recipients**: All emails listed in `emails.txt` (managers only)  

<a name="report-contents"></a>
### 📦 Report Contents (4 Attachments)
| Attachment | Contents | Format |
|------------|----------|--------|
| `OVERRIDES_FULL_DATABASE.xlsx` | Complete override register | Excel |
| `OVERRIDES_CURRENT_VIEW.pdf` | Filtered table (A3 Landscape) | PDF with color-coded rows |
| `SHUTDOWN_LOG_FULL_EXPORT.xlsx` | Complete shutdown event log | Excel |
| `SHUTDOWN_LOG_CURRENT_VIEW.pdf` | Shutdown events (A3 Landscape) | PDF with multi-line text |

**Email Body Includes**:  

```
CCR OPERATOR SYSTEM AUTOMATED REPORT
Generated at: [Timestamp] (Congo FLNG Time)
Schedule: Daily at 05:00 and 17:00 Congo Time
OVERRIDES SUMMARY:
• Total Active: [X]
• Pending Approvals (Yellow): [Y]
SHUTDOWN LOG SUMMARY:
• Total Events: [Z]
• Recent Event (ID #[ID]): [Description]
⚠️ CONFIDENTIAL: Contains operational safety data.
IP ADDRESS: [Your Server IP]
```



<a name="schedule-timezone"></a>
### 🌍 Timezone & Configuration
- **Timezone**: Africa/Brazzaville (Congo Republic Time, UTC+1)  
- **No DST**: Congo does not observe Daylight Saving Time  
- **Verification**: Check console logs at startup:  
  `📍 Timezone: Africa/Brazzaville`  
- **Customization**: To change schedule:  
  1. Open `app.py`  
  2. Find `start_email_scheduler()` function  
  3. Modify schedule lines:  
     ```python
     schedule.every().day.at("05:00", SCHEDULER_TIMEZONE).do(send_scheduled_email)
     schedule.every().day.at("17:00", SCHEDULER_TIMEZONE).do(send_scheduled_email)
     ```  
  4. Restart application  

> ⚠️ **Critical**: Server clock must be synchronized with Congo time. Verify with:  
> ```powershell
> w32tm /query /status  # Windows Time Service status
> ```

---

<a name="admin-functions"></a>
## ⚙️ Admin Functions
*(Accessible only to `admin` role)*  
- **Import Excel Data**: Bulk import overrides (duplicates auto-skipped)  
- **Email Configuration**: Manage `emails.txt` for scheduler recipients  
- **System Maintenance**: Database backups, log reviews  

> ℹ️ **Import Template**: Always use exported files as templates (skip 13 title rows required)

---

<a name="troubleshooting"></a>
## 🛠️ Troubleshooting
| Issue | Solution |
|-------|----------|
| **"Site can't be reached" on LAN** | 1. Verify device on same network<br>2. Check Windows Firewall → Allow port 7860<br>3. Contact IT: Ext. 4357 |
| **PDF shows truncated text** | Use **A3 Landscape** exports (all PDF buttons generate A3) |
| **Email not sending** | 1. Verify `emails.txt` exists with valid emails<br>2. Check Gmail App Password in code<br>3. Confirm outbound port 465 open |
| **Scheduler not running** | Check console: `✅ Email scheduler thread started`<br>Verify `emails.txt` exists and has valid emails |
| **"NameError: shutdown_export_status"** | Update event bindings to use `shutdown_email_status` (see app.py line 1655 fix) |
| **Multi-line PDF text not wrapping** | Ensure fpdf2 ≥ 2.7.0: `pip install --upgrade fpdf2` |

> 📞 **Support Contacts**:  
> - Startup Manager  
> - Offshore Installation Manager  
> - HSE Advisor   

---

<a name="security"></a>
## 🔒 Security & Best Practices
### ✅ DO
- [ ] Log overrides **before** implementation (except genuine emergencies)  
- [ ] Use actual tag numbers from P&IDs in *Module Parameter*  
- [ ] Set accurate *Priority* per SP-FGS-003 risk matrix  
- [ ] Update *Status* during shift handovers  
- [ ] Export database weekly to network drive (`\\FLNG-SERVER\HSE\FGS_Logs`)  
- [ ] Print A3 PDF daily for CCR board  

### ❌ DON'T
- [ ] Share credentials with other personnel  
- [ ] Leave workstation logged in when unattended  
- [ ] Delete entries except duplicates/test data (Overrides only)  
- [ ] Modify *Entry No*, *Time In*, or *Requested By* fields  
- [ ] Import unverified Excel files  
- [ ] Use app on public/unsecured networks  

### 📜 Audit Trail
All actions are logged:  
- Entry creation/modification timestamps  
- User attribution for all changes  
- Full history preserved (no soft deletes)  
- Exportable for regulatory audits  

---

<a name="appendices"></a>
## 📎 Appendices
<a name="priority-matrix"></a>
### Appendix A: Priority Risk Matrix (SP-FGS-003)
| Priority | Criteria | Example |
|----------|----------|---------|
| **critical** | Life safety impact; potential escalation to major incident | Bypass of ESD critical shutdown valve |
| **high** | Major process impact; potential production loss >4hrs | Bypass of main flare header gas detector |
| **medium** | Minor process impact; localized effect | Bypass of non-critical area gas detector |
| **low** | No immediate safety/process impact; administrative | Bypass for routine calibration with redundant detection |

<a name="tag-formats"></a>
### Appendix B: Common Tag Number Formats
| System | Format | Example | Location |
|--------|--------|---------|----------|
| **Gas Detection** | `77ATFZPxx-xxx` | `77ATFZP01-301` | P01 flare header |
| **Fire Detection** | `77ATFIRxx-xxx` | `77ATFIR02-105` | Turbine enclosure |
| **ESD Valves** | `77ESDVxx-xxx` | `77ESDV03-201` | Export line |
| **Process Alarms** | `77PT/TT/FITxx` | `77PT04-101` | Separator pressure |
| **FACP Bypass** | `77BSFZxxxx-xxx` | `77BSFZCRA4-D918` | Crane machinery room |

> ℹ️ **Reference**: Always verify tag numbers against latest P&IDs in `\\FLNG-SERVER\P&IDs\FGS`

<a name="handover-checklist"></a>
### Appendix C: Shift Handover Checklist
**Incoming Supervisor Must Verify**:  
- [ ] **No yellow rows** in Override Register (all pending approvals resolved)  
- [ ] **Green rows** have valid clearance timelines in *Status* field  
- [ ] **Shutdown Log** has no unresolved critical events  
- [ ] Printed A3 PDF posted on CCR handover board  
- [ ] Email reports received for 05:00/17:00 scheduler sends  

> ✅ **Handover Complete Only When**:  
> *"All yellow rows resolved AND green rows verified with physical status"*  

---

*Document ID: CCR-MANUAL-3.0*  
*Written by: [Fabio Matricardi | Key Solution Srl](fabio.matricardi@key-solution.eu) | Wison CSU INST Superintendent*  
*Revision Date: February 2026*  
*CONFIDENTIAL – For Congo FLNG Personnel Only*  

> ℹ️ **Need Help?**  
> Access this manual anytime via the **"📚 User Manual"** tab in the application.  
> Last updated: `2026-02-04`  
> Questions? Contact HSE Advisor or Startup Manager


