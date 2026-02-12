"""
Standalone Plant Shutdown Event Log Application
Preserves all original Shutdown Log functionality with streamlined architecture
PDF functionality REMOVED due to rendering issues - Excel-only exports
"""
import gradio as gr
import json
import os
import socket
import tempfile
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import mimetypes
import pandas as pd
from pathlib import Path
from datetime import datetime
import shutil

# ======================
# CONFIGURABLE CATEGORIES (MAINTENANCE-FRIENDLY)
# Edit these dictionaries to update classification options without touching core logic
# ======================

EVENT_TYPE_OPTIONS = ["PSD", "ESD"]

EVENT_CLASSIFICATION_OPTIONS = ["GENUINE", "SPURIOUS"]

MAIN_CLUSTER_OPTIONS = {
    "GENUINE": [
        "1. Process / Operability",
        "2. Mechanical / Asset Integrity",
        "3. Containment / HSE Event",
        "4. Safety & Protection Systems",
        "5. Utilities & External Constraints",
        "6. Natural / Environmental External Event"
    ],
    "SPURIOUS": [
        "1. Procedure",
        "2. Architecture (Project)",
        "3. Component Failure",
        "4. Logic/ Configuration"
    ]
}

# SUBCLUSTER MAPPING: Key format = "CLASSIFICATION|MAIN_CLUSTER"
SUBCLUSTER_OPTIONS = {
    # GENUINE clusters
    "GENUINE|1. Process / Operability": [
        "TBD",
        "Process Upset (P/T/level/flow outside operating and/or design limits, dynamic instability, thermodynamic phenomena, etc.)",
        "Transients (start-up, shutdown, setup change)"
    ],
    "GENUINE|2. Mechanical / Asset Integrity": [
        "TBD",
        "Mechanical failure",
        "Progressive degradation (corrosion, chemical-biological risk, fouling)",
        "Vibration"
    ],
    "GENUINE|3. Containment / HSE Event": [
        "TBD",
        "Environmental Leak",
        "Emissions",
        "Fire / Explosion"
    ],
    "GENUINE|4. Safety & Protection Systems": [
        "TBD",
        "ESD valve failure",
        "Critical loops Loss of redundancy"
    ],
    "GENUINE|5. Utilities & External Constraints": [
        "TBD",
        "Utility failures (electrical, instrument air, cooling, fuel gas)",
        "Grid constraints (upstream/downstream/external blackout)"
    ],
    "GENUINE|6. Natural / Environmental External Event": [
        "TBD",
        "Natural events (such as storms, floods, etc., beyond the plant's control)",
        "Environmental events (related to interactions between the plant and the surrounding environment: gas detection, soil contamination, H2S limit exceedance)"
    ],
    
    # SPURIOUS clusters
    "SPURIOUS|1. Procedure": [
        "TBD",
        "Human error (operation/maintenance)",
        "Wrong procedure"
    ],
    "SPURIOUS|2. Architecture (Project)": [
        "TBD",
        "Wrong assembly",
        "Redundancy",
        "Undersizing",
        "Out of standard/spec",
        "Obsolete"
    ],
    "SPURIOUS|3. Component Failure": [
        "TBD",
        "Wear/tear",
        "Poor quality"
    ],
    "SPURIOUS|4. Logic/ Configuration": [
        "TBD",
        "Wrong set point",
        "Logic error",
        "C&E mismatch",
        "Voting logic error",
        "Software modification/patch"
    ]
}

# Fixed organizational fields (auto-populated)
FIXED_FIELDS = {
    "Country": "CONGO",
    "Company": "ENI CONGO",
    "Unit/Asset": "NGUYA FLNG"
}

# Complete column schema (order matters for exports/UI)
SHUTDOWN_COLUMNS = [
    'ID', 'timestamp', 'Country', 'Company', 'Unit/Asset', 'Event Type', 
    'Event Classification', 'Main Cluster', 'Subcluster', 
    'Technical Details/Event Description', 'First Cause', 'RCA', 
    'Actions', 'Action by', 'Reported by'
]

# ======================
# CORE CONFIGURATION
# ======================
SHUTDOWN_FILE = "shutdown.json"
SECRETFILE = "secret.json"
GMAIL_APP_PASSWORD = None
MANAGER_EMAILS_FILE = "emails.txt"
SENDER_EMAIL = "fabio.matricardi@gmail.com"
MYLOCALIP = socket.gethostbyname(socket.gethostname()) if not socket.gethostbyname(socket.gethostname()).startswith("localhost") else "127.0.0.1"

# Initialize shutdown log file with schema migration
if not os.path.exists(SHUTDOWN_FILE):
    with open(SHUTDOWN_FILE, 'w') as f:
        json.dump([], f)
    print(f"✅ Created new shutdown log: {SHUTDOWN_FILE}")
else:
    # Migrate existing records to new schema
    with open(SHUTDOWN_FILE, 'r') as f:
        events = json.load(f)
    
    migrated = False
    for event in events:
        # Backfill missing fields with safe defaults
        for col in SHUTDOWN_COLUMNS:
            if col not in event:
                if col in FIXED_FIELDS:
                    event[col] = FIXED_FIELDS[col]
                elif col == 'Event Type':
                    event[col] = EVENT_TYPE_OPTIONS[0]
                elif col == 'Event Classification':
                    event[col] = EVENT_CLASSIFICATION_OPTIONS[0]
                elif col == 'Main Cluster':
                    event[col] = MAIN_CLUSTER_OPTIONS[EVENT_CLASSIFICATION_OPTIONS[0]][0]
                elif col == 'Subcluster':
                    key = f"{EVENT_CLASSIFICATION_OPTIONS[0]}|{MAIN_CLUSTER_OPTIONS[EVENT_CLASSIFICATION_OPTIONS[0]][0]}"
                    event[col] = SUBCLUSTER_OPTIONS.get(key, ["TBD"])[0]
                elif col in ['RCA', 'Actions']:
                    event[col] = "Pending"
                else:
                    event[col] = ""
                migrated = True
    
    if migrated:
        backup_path = SHUTDOWN_FILE.replace('.json', f'_migrated_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        shutil.copy2(SHUTDOWN_FILE, backup_path)
        with open(SHUTDOWN_FILE, 'w') as f:
            json.dump(events, f, indent=2)
        print(f"✅ Migrated {len(events)} existing records to new schema (backup: {backup_path})")

# Load Gmail password
try:
    with open(SECRETFILE) as f:
        GMAIL_APP_PASSWORD = json.load(f)['secret_code']
except FileNotFoundError:
    print("⚠️ Warning: JSON file not found - email functionality disabled")
except (json.JSONDecodeError, KeyError) as e:
    print(f"⚠️ Warning: Error reading secret_code: {e} - email functionality disabled")

# ======================
# SCHEDULED REPORTS (Excel-only)
# ======================
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import logging

logging.basicConfig(level=logging.INFO)
scheduler_logger = logging.getLogger('apscheduler.executors.default')
scheduler_logger.setLevel(logging.INFO)

# TWO SCHEDULER TIME TRIGGERS (Africa/Brazzaville = UTC+1)
T1H = 7  # Morning report hour
T1M = 50 # Morning report minute
T2H = 17 # Evening report hour
T2M = 50 # Evening report minute

def send_scheduled_report(report_type="automated"):
    """Send scheduled shutdown report with Excel export only"""
    try:
        timestamp = datetime.now(pytz.timezone('Africa/Brazzaville')).strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n⏰ SCHEDULED REPORT TRIGGERED [{timestamp}] - Type: {report_type}")

        # Generate Excel export ONLY
        excel_path, excel_msg = export_shutdown_excel()
        if excel_path is None:
            raise Exception(f"Excel export failed: {excel_msg}")

        # Prepare custom note with report type
        custom_note = (
            f"SCHEDULED SHUTDOWN LOG REPORT ({report_type})\n"
            f"Generated at: {timestamp} (Africa/Brazzaville Time)\n"
            f"Total Events: {len(load_shutdown_events())}\n"
            f"IP ADDRESS: {MYLOCALIP}\n"
            f"⚠️ AUTOMATED REPORT - DO NOT REPLY"
        )

        # Get recipients
        managers, error = read_manager_emails()
        if error:
            raise Exception(f"Email recipients error: {error}")
        if not managers:
            raise Exception("No valid manager emails configured")

        # Send email with Excel only
        status = send_email_with_exports(
            recipients=managers,
            excel_path=excel_path,
            custom_note=custom_note
        )

        # Cleanup temp file
        try:
            if excel_path and os.path.exists(excel_path):
                os.remove(excel_path)
        except Exception as e:
            print(f"⚠️ Cleanup warning for {excel_path}: {str(e)}")

        log_msg = f"✅ SCHEDULED REPORT SENT [{timestamp}] to {len(managers)} managers"
        print(log_msg)
        with open("scheduled_reports.log", "a", encoding="utf-8") as log:
            log.write(f"{timestamp} | SUCCESS | {len(managers)} recipients | {status[:100]}\n")
        return log_msg

    except Exception as e:
        error_time = datetime.now(pytz.timezone('Africa/Brazzaville')).strftime('%Y-%m-%d %H:%M:%S')
        error_msg = f"❌ SCHEDULED REPORT FAILED [{error_time}]: {str(e)}"
        print(error_msg)
        with open("scheduled_reports.log", "a", encoding="utf-8") as log:
            log.write(f"{error_time} | FAILED | {str(e)[:200]}\n")
        return error_msg

def start_scheduled_reports():
    """Initialize and start the background scheduler"""
    try:
        w_at_timezone = pytz.timezone('Africa/Brazzaville')
        scheduler = BackgroundScheduler(timezone=w_at_timezone)

        # Schedule T1 (T1H:T1M)
        T1_name = f"Daily {T1H:02d}:{T1M:02d} Shutdown Report"
        T1_args = f"{T1H:02d}:{T1M:02d} Daily Report"
        scheduler.add_job(
            send_scheduled_report,
            CronTrigger(hour=T1H, minute=T1M, timezone=w_at_timezone),
            id='shutdown_report_am',
            name=T1_name,
            replace_existing=True,
            kwargs={'report_type': T1_args}
        )

        # Schedule T2 (T2H:T2M)
        T2_name = f"Daily {T2H:02d}:{T2M:02d} Shutdown Report"
        T2_args = f"{T2H:02d}:{T2M:02d} Daily Report"
        scheduler.add_job(
            send_scheduled_report,
            CronTrigger(hour=T2H, minute=T2M, timezone=w_at_timezone),
            id='shutdown_report_pm',
            name=T2_name,
            replace_existing=True,
            kwargs={'report_type': T2_args}
        )

        scheduler.start()

        # Log next run times
        jobs = scheduler.get_jobs()
        next_runs = "\n".join([f"  • {job.name}: {job.next_run_time}" for job in jobs])
        print(f"\n✅ SCHEDULED REPORTS ACTIVATED (Africa/Brazzaville Timezone UTC+1)")
        print(f"Next executions:\n{next_runs}")
        print("Reports will continue running while application is active\n")

        return scheduler

    except Exception as e:
        print(f"⚠️ Scheduler initialization failed: {str(e)}")
        return None

# ======================
# EMAIL FUNCTIONALITY (Excel-only)
# ======================
def read_manager_emails():
    """Read validated manager emails from file"""
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    emails = []
    if not os.path.exists(MANAGER_EMAILS_FILE):
        return [], f"❌ Email file '{MANAGER_EMAILS_FILE}' not found. Create file with manager emails (one per line)."
    try:
        with open(MANAGER_EMAILS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                email = line.strip()
                if email and not email.startswith('#') and email_pattern.match(email):
                    emails.append(email)
        if not emails:
            return [], f"❌ No valid emails found in '{MANAGER_EMAILS_FILE}'. Format: one email per line."
        return emails, None
    except Exception as e:
        return [], f"❌ Error reading email file: {str(e)}"

def send_email_with_exports(recipients, excel_path, custom_note=""):
    """Send shutdown log exports via email (Excel only)"""
    if not GMAIL_APP_PASSWORD:
        return "❌ EMAIL NOT CONFIGURED: Set GMAIL_APP_PASSWORD environment variable"
    if not recipients:
        return "❌ No valid recipients provided"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"Plant Shutdown Log Export - {timestamp}"
    body = f"""PLANT SHUTDOWN EVENT LOG EXPORT
Generated by: Shutdown Log System
Timestamp: {timestamp} (Congo FLNG Time)
{('Note: ' + custom_note) if custom_note else ''}
Attachment:
• SHUTDOWN_LOG_FULL_EXPORT.xlsx - Complete event history with all classification fields

⚠️ CONFIDENTIAL: Contains operational safety data.
Do not forward outside authorized Congo FLNG personnel.

System IP: {MYLOCALIP}
Automated message from Plant Shutdown Event Log System
"""

    # Create message
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = SENDER_EMAIL
    message['To'] = ', '.join(recipients[:3]) + (f" + {len(recipients)-3} more" if len(recipients) > 3 else "")
    message.attach(MIMEText(body, 'plain'))

    # Attach Excel file ONLY
    attachments = []
    if os.path.exists(excel_path):
        try:
            ctype, _ = mimetypes.guess_type(excel_path)
            maintype, subtype = (ctype or 'application/octet-stream').split('/', 1)
            with open(excel_path, 'rb') as fp:
                part = MIMEBase(maintype, subtype)
                part.set_payload(fp.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment', filename="SHUTDOWN_LOG_FULL_EXPORT.xlsx")
            message.attach(part)
            attachments.append("SHUTDOWN_LOG_FULL_EXPORT.xlsx")
        except Exception as e:
            print(f"⚠️ Attachment error: {str(e)}")

    if not attachments:
        return "❌ Failed to attach Excel file"

    # Send email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=30) as server:
            server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(message, to_addrs=recipients)
        return f"✅ Email sent to {len(recipients)} recipient(s)! ({', '.join(attachments)})"
    except smtplib.SMTPAuthenticationError:
        return "❌ EMAIL AUTH FAILED: Invalid GMAIL_APP_PASSWORD. Contact administrator."
    except Exception as e:
        return f"❌ Email failed: {str(e)[:100]}"

# ======================
# SHUTDOWN LOG OPERATIONS
# ======================
def load_shutdown_events():
    """Load events from JSON with error handling and schema validation"""
    try:
        with open(SHUTDOWN_FILE, 'r') as f:
            events = json.load(f)
        
        # Ensure all events have complete schema (defense in depth)
        for event in events:
            for col in SHUTDOWN_COLUMNS:
                if col not in event:
                    if col in FIXED_FIELDS:
                        event[col] = FIXED_FIELDS[col]
                    elif col == 'Event Type':
                        event[col] = EVENT_TYPE_OPTIONS[0]
                    elif col == 'Event Classification':
                        event[col] = EVENT_CLASSIFICATION_OPTIONS[0]
                    elif col == 'Main Cluster':
                        event[col] = MAIN_CLUSTER_OPTIONS[EVENT_CLASSIFICATION_OPTIONS[0]][0]
                    elif col == 'Subcluster':
                        key = f"{EVENT_CLASSIFICATION_OPTIONS[0]}|{MAIN_CLUSTER_OPTIONS[EVENT_CLASSIFICATION_OPTIONS[0]][0]}"
                        event[col] = SUBCLUSTER_OPTIONS.get(key, ["TBD"])[0]
                    elif col in ['RCA', 'Actions']:
                        event[col] = "Pending"
                    else:
                        event[col] = ""
        return events
    except Exception as e:
        print(f"⚠️ Load error: {str(e)}")
        return []

def save_shutdown_events(events):
    """Save events to JSON with backup"""
    try:
        # Create backup before writing
        if os.path.exists(SHUTDOWN_FILE):
            backup_path = SHUTDOWN_FILE.replace('.json', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            shutil.copy2(SHUTDOWN_FILE, backup_path)
        
        with open(SHUTDOWN_FILE, 'w') as f:
            json.dump(events, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ Save error: {str(e)}")
        return False

def get_filtered_shutdowns(filters):
    """Apply filters to shutdown events"""
    events = load_shutdown_events()
    if not events:
        return pd.DataFrame(columns=SHUTDOWN_COLUMNS)
    
    df = pd.DataFrame(events, columns=SHUTDOWN_COLUMNS)
    
    for col, val in filters.items():
        if val and val.strip():
            df = df[df[col].astype(str).str.contains(val, case=False, na=False)]
    
    return df.sort_values('ID', ascending=False).reset_index(drop=True)

# ======================
# EXPORT FUNCTIONS (Excel-only)
# ======================
def export_shutdown_excel():
    """Export shutdown log to Excel with all columns"""
    df = get_filtered_shutdowns({})
    if df.empty:
        return None, "❌ No shutdown events to export"
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"ShutdownLog_Export_{timestamp}.xlsx"
    filepath = os.path.join(tempfile.gettempdir(), filename)

    try:
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Header rows
            pd.DataFrame([["PLANT SHUTDOWN EVENT LOG - OFFICIAL RECORD"]]).to_excel(
                writer, sheet_name='ShutdownLog', index=False, header=False
            )
            pd.DataFrame([[f"Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]]).to_excel(
                writer, sheet_name='ShutdownLog', startrow=1, index=False, header=False
            )
            # Column headers with organizational context
            pd.DataFrame([[
                "ID", "Timestamp", "Country", "Company", "Unit/Asset", "Event Type",
                "Event Classification", "Main Cluster", "Subcluster",
                "Technical Details/Event Description", "First Cause", "RCA",
                "Actions", "Action by", "Reported by"
            ]]).to_excel(
                writer, sheet_name='ShutdownLog', startrow=2, index=False, header=False
            )
            # Data
            df.to_excel(writer, sheet_name='ShutdownLog', startrow=3, index=False, header=False)
        
        # Auto-fit column widths (basic approximation)
        from openpyxl import load_workbook
        wb = load_workbook(filepath)
        ws = wb.active
        for column_cells in ws.columns:
            length = max(len(str(cell.value or "")) for cell in column_cells)
            ws.column_dimensions[column_cells[0].column_letter].width = min(40, max(10, length + 2))
        wb.save(filepath)
        
        return filepath, f"✅ Exported {len(df)} shutdown events to Excel"
    except Exception as e:
        return None, f"❌ Export failed: {str(e)}"

# ======================
# GRADIO INTERFACE (PDF button removed)
# ======================
with gr.Blocks(
    title="Plant Shutdown Event Log",
    theme=gr.themes.Glass(),
    css="""
    .shutdown-header {background: linear-gradient(to right, #7da8cc, #a3c1e6); color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px}
    .fixed-field {background-color: #e9ecef; padding: 8px; border-radius: 4px; margin-bottom: 10px; font-weight: bold}
    """
) as demo:
    # Start scheduled reports BEFORE launching UI
    scheduler = start_scheduled_reports()

    # Launch info
    border = "=" * 70
    print(f"\n{border}")
    print("🚀 PLANT SHUTDOWN EVENT LOG - STANDALONE APPLICATION (ENHANCED SCHEMA)")
    print(border)
    print(f"📍 LOCAL ACCESS:  http://127.0.0.1:7860")
    if MYLOCALIP != "127.0.0.1":
        print(f"🌐 NETWORK ACCESS: http://{MYLOCALIP}:7860")
    print("-" * 70)
    print("ℹ️  ENHANCED FEATURES:")
    print("   • New classification schema: Event Type, Classification, Clusters, Subclusters")
    print("   • Hierarchical dropdown dependencies (Classification → Cluster → Subcluster)")
    print("   • Fixed organizational fields auto-populated (Country/Company/Unit)")
    print("   • Permanent audit trail with automatic schema migration")
    print("   • Excel exports with auto-fitted columns (PDF functionality removed)")
    print("   • ⏰ AUTOMATED SCHEDULED REPORTS at 07:50 & 17:50 (Africa/Brazzaville)")
    print("🔒 SECURITY: All entries permanent. Deletion prohibited per SP-SHUT-001")
    print(border)
    print("✅ Excel export available (openpyxl installed)")

    gr.Markdown("---")

    # EXPORT & EMAIL SECTION (PDF button removed)
    gr.Markdown("## 📤 Export & Distribution")
    with gr.Row():
        shutdown_export_excel_btn = gr.Button("📤 Export to Excel", variant="primary")
        shutdown_send_email_btn = gr.Button("✉️ Send to Managers", variant="primary")

    with gr.Row():
        shutdown_export_file = gr.File(label="📥 Download Export", type="filepath", visible=True)
        shutdown_email_status = gr.Textbox(label="📧 Email Status", interactive=False)

    gr.Markdown("---")

    # FILTER SECTION
    gr.Markdown("## 🔍 Filter Shutdown Events")
    shutdown_filter_inputs = {}
    with gr.Row():
        for col in SHUTDOWN_COLUMNS[:5]:
            shutdown_filter_inputs[col] = gr.Textbox(label=col, placeholder=f"Filter {col}...", container=False)
    with gr.Row():
        for col in SHUTDOWN_COLUMNS[5:10]:
            shutdown_filter_inputs[col] = gr.Textbox(label=col, placeholder=f"Filter {col}...", container=False)
    with gr.Row():
        for col in SHUTDOWN_COLUMNS[10:]:
            shutdown_filter_inputs[col] = gr.Textbox(label=col, placeholder=f"Filter {col}...", container=False)
    shutdown_filter_btn = gr.Button("Apply Filters", variant="secondary")

    # EVENTS TABLE
    shutdown_table = gr.Dataframe(
        headers=SHUTDOWN_COLUMNS,
        datatype=["str"] * len(SHUTDOWN_COLUMNS),
        interactive=False,
        wrap=True,
        label="Shutdown Events History"
    )

    gr.Markdown("---")

    # EVENT SELECTION
    gr.Markdown("## ➕ Add New Event / ✏️ Edit Existing Event")
    with gr.Row():
        shutdown_id_selector = gr.Dropdown(
            label="Select Event ID to Edit", 
            choices=[],
            interactive=True,
            scale=3
        )
        shutdown_load_event_btn = gr.Button("✏️ Load Selected Event", variant="primary", scale=1)

    # FIXED ORGANIZATIONAL FIELDS (read-only display)
    gr.Markdown("### 🏢 Organizational Context (Auto-populated)")
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown(f'<div class="fixed-field">Country:<br><strong>{FIXED_FIELDS["Country"]}</strong></div>', elem_id="country_field")
        with gr.Column(scale=1):
            gr.Markdown(f'<div class="fixed-field">Company:<br><strong>{FIXED_FIELDS["Company"]}</strong></div>', elem_id="company_field")
        with gr.Column(scale=1):
            gr.Markdown(f'<div class="fixed-field">Unit/Asset:<br><strong>{FIXED_FIELDS["Unit/Asset"]}</strong></div>', elem_id="unit_field")

    # CLASSIFICATION SECTION (hierarchical dropdowns)
    gr.Markdown("### 🔬 Event Classification")
    with gr.Row():
        shutdown_event_type = gr.Dropdown(
            label="Event Type", 
            choices=EVENT_TYPE_OPTIONS,
            value=EVENT_TYPE_OPTIONS[0],
            interactive=True
        )
        shutdown_event_classification = gr.Dropdown(
            label="Event Classification", 
            choices=EVENT_CLASSIFICATION_OPTIONS,
            value=EVENT_CLASSIFICATION_OPTIONS[0],
            interactive=True
        )
    with gr.Row():
        shutdown_main_cluster = gr.Dropdown(
            label="Main Cluster", 
            choices=MAIN_CLUSTER_OPTIONS[EVENT_CLASSIFICATION_OPTIONS[0]],
            value=MAIN_CLUSTER_OPTIONS[EVENT_CLASSIFICATION_OPTIONS[0]][0],
            interactive=True
        )
        shutdown_subcluster = gr.Dropdown(
            label="Subcluster", 
            choices=SUBCLUSTER_OPTIONS.get(
                f"{EVENT_CLASSIFICATION_OPTIONS[0]}|{MAIN_CLUSTER_OPTIONS[EVENT_CLASSIFICATION_OPTIONS[0]][0]}", 
                ["TBD"]
            ),
            value="TBD",
            interactive=True
        )

    # CORE EVENT DETAILS
    gr.Markdown("### 📝 Event Details")
    with gr.Row():
        shutdown_id = gr.Number(label="ID (Auto-generated for new events)", interactive=False, scale=1)
        shutdown_timestamp = gr.Textbox(
            label="Timestamp (YYYY-MM-DD HH:MM:SS)", 
            value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            scale=2
        )
    with gr.Row():
        shutdown_event_desc = gr.Textbox(
            label="Technical Details/Event Description", 
            lines=3, 
            max_lines=8, 
            placeholder="Describe the event including sequence of events, systems affected, and operational impact..."
        )
    with gr.Row():
        shutdown_first_cause = gr.Textbox(
            label="First Cause", 
            lines=2, 
            max_lines=5,
            placeholder="Immediate technical cause that initiated the shutdown sequence..."
        )
        shutdown_rca = gr.Textbox(
            label="RCA", 
            lines=2, 
            max_lines=5,
            value="Pending",
            placeholder="Root cause analysis (to be completed within 72h per procedure)..."
        )
    with gr.Row():
        shutdown_actions = gr.Textbox(
            label="Actions", 
            lines=3, 
            max_lines=8,
            value="Pending",
            placeholder="Corrective/preventive actions with owners and deadlines..."
        )
    with gr.Row():
        shutdown_action_by = gr.Textbox(label="Action by", placeholder="Name/Team responsible for actions")
        shutdown_reported_by = gr.Textbox(label="Reported by", placeholder="Name of reporter")

    # ACTION BUTTONS
    with gr.Row():
        shutdown_add_new_btn = gr.Button("➕ Add New Event", variant="primary")
        shutdown_save_btn = gr.Button("💾 Save Event", variant="primary", visible=False)
        shutdown_cancel_btn = gr.Button("↺ Cancel", variant="secondary")

    shutdown_status_msg = gr.Textbox(label="Operation Status", interactive=False)

    gr.Markdown("---")

    # FOOTER
    with gr.Row():
        with gr.Column(scale=1):
            try:
                gr.Image("logo.png", height=40, container=False, show_label=False)
            except:
                gr.Markdown("![Logo](logo.png)", visible=False)
        with gr.Column(scale=2):
            gr.Markdown(
                "**All rights reserved (C)**\n"
                "created by fabio.matricardi@key-solution.eu for NGUYA FLNG Project\n"
                f"visit [Key Solution SRL](https://key-solution.eu) | Network IP: {MYLOCALIP}"
            )

    # ======================
    # EVENT HANDLERS
    # ======================
    def refresh_shutdown_view(filters_dict=None):
        """Refresh table and ID selector"""
        if filters_dict is None:
            filters_dict = {col: "" for col in SHUTDOWN_COLUMNS}
        df = get_filtered_shutdowns(filters_dict)
        events = load_shutdown_events()
        id_choices = [str(e['ID']) for e in events] if events else []
        return (
            df,
            gr.update(choices=id_choices, value=None),
            gr.update(value=None, interactive=False),
            gr.update(value=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            gr.update(value=EVENT_TYPE_OPTIONS[0]),
            gr.update(value=EVENT_CLASSIFICATION_OPTIONS[0]),
            gr.update(value=MAIN_CLUSTER_OPTIONS[EVENT_CLASSIFICATION_OPTIONS[0]][0]),
            gr.update(value="TBD"),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(value="Pending"),
            gr.update(value="Pending"),
            gr.update(value=""),
            gr.update(value=""),
            gr.update(visible=False),
            ""
        )

    def update_main_cluster_options(classification):
        """Update Main Cluster options based on Event Classification"""
        options = MAIN_CLUSTER_OPTIONS.get(classification, [])
        return gr.update(choices=options, value=options[0] if options else "TBD")

    def update_subcluster_options(classification, main_cluster):
        """Update Subcluster options based on Classification + Main Cluster"""
        key = f"{classification}|{main_cluster}"
        options = SUBCLUSTER_OPTIONS.get(key, ["TBD"])
        return gr.update(choices=options, value=options[0] if options else "TBD")

    def load_selected_event(event_id_str):
        """Load event into form for editing"""
        if not event_id_str:
            return {shutdown_status_msg: "❌ Please select an Event ID"}
        
        try:
            event_id = int(event_id_str)
        except:
            return {shutdown_status_msg: "❌ Invalid Event ID"}
        
        events = load_shutdown_events()
        event = next((e for e in events if e['ID'] == event_id), None)
        
        if not event:
            return {shutdown_status_msg: f"❌ Event ID {event_id} not found"}
        
        # Get subcluster options based on stored values
        cluster_key = f"{event.get('Event Classification', 'GENUINE')}|{event.get('Main Cluster', '')}"
        sub_options = SUBCLUSTER_OPTIONS.get(cluster_key, ["TBD"])
        sub_value = event.get('Subcluster', "TBD") if event.get('Subcluster', "TBD") in sub_options else sub_options[0]
        
        return {
            shutdown_id: gr.update(value=event['ID'], interactive=False),
            shutdown_timestamp: gr.update(value=event.get('timestamp', '')),
            shutdown_event_type: gr.update(value=event.get('Event Type', EVENT_TYPE_OPTIONS[0])),
            shutdown_event_classification: gr.update(value=event.get('Event Classification', EVENT_CLASSIFICATION_OPTIONS[0])),
            shutdown_main_cluster: gr.update(value=event.get('Main Cluster', MAIN_CLUSTER_OPTIONS[EVENT_CLASSIFICATION_OPTIONS[0]][0])),
            shutdown_subcluster: gr.update(value=sub_value, choices=sub_options),
            shutdown_event_desc: gr.update(value=event.get('Technical Details/Event Description', '')),
            shutdown_first_cause: gr.update(value=event.get('First Cause', '')),
            shutdown_rca: gr.update(value=event.get('RCA', 'Pending')),
            shutdown_actions: gr.update(value=event.get('Actions', 'Pending')),
            shutdown_action_by: gr.update(value=event.get('Action by', '')),
            shutdown_reported_by: gr.update(value=event.get('Reported by', '')),
            shutdown_save_btn: gr.update(visible=True, value="💾 Update Event"),
            shutdown_status_msg: f"✏️ Editing Event ID #{event_id}. Make changes and click 'Save Event'"
        }

    def prepare_new_event():
        """Reset form for new event"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            shutdown_id: gr.update(value=None, interactive=False),
            shutdown_timestamp: gr.update(value=now),
            shutdown_event_type: gr.update(value=EVENT_TYPE_OPTIONS[0]),
            shutdown_event_classification: gr.update(value=EVENT_CLASSIFICATION_OPTIONS[0]),
            shutdown_main_cluster: gr.update(value=MAIN_CLUSTER_OPTIONS[EVENT_CLASSIFICATION_OPTIONS[0]][0]),
            shutdown_subcluster: gr.update(value="TBD", choices=SUBCLUSTER_OPTIONS.get(
                f"{EVENT_CLASSIFICATION_OPTIONS[0]}|{MAIN_CLUSTER_OPTIONS[EVENT_CLASSIFICATION_OPTIONS[0]][0]}", ["TBD"]
            )),
            shutdown_event_desc: gr.update(value=""),
            shutdown_first_cause: gr.update(value=""),
            shutdown_rca: gr.update(value="Pending"),
            shutdown_actions: gr.update(value="Pending"),
            shutdown_action_by: gr.update(value=""),
            shutdown_reported_by: gr.update(value=""),
            shutdown_save_btn: gr.update(visible=True, value="✅ Add New Event"),
            shutdown_status_msg: "➕ Creating new shutdown event. Fill required fields and click 'Add New Event'"
        }

    def save_shutdown_event(id_val, timestamp, event_type, classification, main_cluster, subcluster,
                          desc, cause, rca, actions, action_by, reported_by):
        """Save new or updated event with full schema"""
        # Validation (minimal - per your request)
        if not desc.strip():
            return {shutdown_status_msg: "❌ Technical Details/Event Description is required"}
        if not cause.strip():
            return {shutdown_status_msg: "❌ First Cause is required"}
        if not reported_by.strip():
            return {shutdown_status_msg: "❌ Reported by is required"}
        
        events = load_shutdown_events()
        
        # Prepare event data with fixed fields auto-injected
        event_data = {
            'ID': id_val,
            'timestamp': timestamp.strip() or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Country': FIXED_FIELDS['Country'],
            'Company': FIXED_FIELDS['Company'],
            'Unit/Asset': FIXED_FIELDS['Unit/Asset'],
            'Event Type': event_type,
            'Event Classification': classification,
            'Main Cluster': main_cluster,
            'Subcluster': subcluster,
            'Technical Details/Event Description': desc.strip(),
            'First Cause': cause.strip(),
            'RCA': rca.strip() if rca.strip() else "Pending",
            'Actions': actions.strip() if actions.strip() else "Pending",
            'Action by': action_by.strip(),
            'Reported by': reported_by.strip()
        }
        
        if id_val:  # Update existing
            for i, e in enumerate(events):
                if e['ID'] == id_val:
                    events[i] = event_data
                    break
            action = "updated"
        else:  # Create new
            new_id = max((e['ID'] for e in events), default=0) + 1
            event_data['ID'] = new_id
            events.append(event_data)
            action = "created"
        
        # Save with backup
        if save_shutdown_events(events):
            df = get_filtered_shutdowns({})
            id_choices = [str(e['ID']) for e in events]
            return {
                shutdown_table: df,
                shutdown_id_selector: gr.update(choices=id_choices),
                shutdown_id: gr.update(value=None, interactive=False),
                shutdown_timestamp: gr.update(value=datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                shutdown_event_type: gr.update(value=EVENT_TYPE_OPTIONS[0]),
                shutdown_event_classification: gr.update(value=EVENT_CLASSIFICATION_OPTIONS[0]),
                shutdown_main_cluster: gr.update(value=MAIN_CLUSTER_OPTIONS[EVENT_CLASSIFICATION_OPTIONS[0]][0]),
                shutdown_subcluster: gr.update(value="TBD"),
                shutdown_event_desc: gr.update(value=""),
                shutdown_first_cause: gr.update(value=""),
                shutdown_rca: gr.update(value="Pending"),
                shutdown_actions: gr.update(value="Pending"),
                shutdown_action_by: gr.update(value=""),
                shutdown_reported_by: gr.update(value=""),
                shutdown_save_btn: gr.update(visible=False),
                shutdown_status_msg: f"✅ Event ID #{event_data['ID']} successfully {action}! (Permanent audit record)"
            }
        else:
            return {shutdown_status_msg: "❌ Save failed. Check file permissions."}

    def apply_shutdown_filters(*filter_vals):
        """Apply filters to shutdown table"""
        filters = dict(zip(SHUTDOWN_COLUMNS, filter_vals))
        df = get_filtered_shutdowns(filters)
        events = load_shutdown_events()
        id_choices = [str(e['ID']) for e in events] if events else []
        return {
            shutdown_table: df,
            shutdown_id_selector: gr.update(choices=id_choices)
        }

    def export_shutdown_excel_handler():
        filepath, msg = export_shutdown_excel()
        if filepath and os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return filepath, msg, gr.update(visible=True)
        return None, msg, gr.update(visible=False)

    def send_shutdown_to_managers():
        """Send shutdown log Excel export to managers"""
        managers, error = read_manager_emails()
        if error:
            return error
        
        # Generate Excel export
        excel_path, excel_msg = export_shutdown_excel()
        if excel_path is None:
            return excel_msg
        
        # Send with shutdown-specific note
        custom_note = (
            f"SHUTDOWN LOG EXPORT\n"
            f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Congo FLNG Time)\n"
            f"Total Events: {len(load_shutdown_events())}\n"
            f"IP ADDRESS: {MYLOCALIP}"
        )
        
        status = send_email_with_exports(
            recipients=managers,
            excel_path=excel_path,
            custom_note=custom_note
        )
        
        # Cleanup temp file
        try:
            if excel_path and os.path.exists(excel_path):
                os.remove(excel_path)
        except:
            pass
        
        return status

    # ======================
    # EVENT BINDINGS
    # ======================
    # Hierarchical dropdown dependencies
    shutdown_event_classification.change(
        update_main_cluster_options,
        inputs=[shutdown_event_classification],
        outputs=[shutdown_main_cluster]
    )
    
    shutdown_main_cluster.change(
        update_subcluster_options,
        inputs=[shutdown_event_classification, shutdown_main_cluster],
        outputs=[shutdown_subcluster]
    )

    shutdown_filter_btn.click(
        apply_shutdown_filters,
        inputs=[*[shutdown_filter_inputs[col] for col in SHUTDOWN_COLUMNS]],
        outputs=[shutdown_table, shutdown_id_selector]
    )

    shutdown_load_event_btn.click(
        load_selected_event,
        inputs=[shutdown_id_selector],
        outputs=[
            shutdown_id, shutdown_timestamp, shutdown_event_type, shutdown_event_classification,
            shutdown_main_cluster, shutdown_subcluster, shutdown_event_desc, shutdown_first_cause,
            shutdown_rca, shutdown_actions, shutdown_action_by, shutdown_reported_by,
            shutdown_save_btn, shutdown_status_msg
        ]
    )

    shutdown_add_new_btn.click(
        prepare_new_event,
        outputs=[
            shutdown_id, shutdown_timestamp, shutdown_event_type, shutdown_event_classification,
            shutdown_main_cluster, shutdown_subcluster, shutdown_event_desc, shutdown_first_cause,
            shutdown_rca, shutdown_actions, shutdown_action_by, shutdown_reported_by,
            shutdown_save_btn, shutdown_status_msg
        ]
    )

    shutdown_save_btn.click(
        save_shutdown_event,
        inputs=[
            shutdown_id, shutdown_timestamp, shutdown_event_type, shutdown_event_classification,
            shutdown_main_cluster, shutdown_subcluster, shutdown_event_desc, shutdown_first_cause,
            shutdown_rca, shutdown_actions, shutdown_action_by, shutdown_reported_by
        ],
        outputs=[
            shutdown_table, shutdown_id_selector,
            shutdown_id, shutdown_timestamp, shutdown_event_type, shutdown_event_classification,
            shutdown_main_cluster, shutdown_subcluster, shutdown_event_desc, shutdown_first_cause,
            shutdown_rca, shutdown_actions, shutdown_action_by, shutdown_reported_by,
            shutdown_save_btn, shutdown_status_msg
        ]
    )

    shutdown_cancel_btn.click(
        refresh_shutdown_view,
        outputs=[
            shutdown_table, shutdown_id_selector,
            shutdown_id, shutdown_timestamp, shutdown_event_type, shutdown_event_classification,
            shutdown_main_cluster, shutdown_subcluster, shutdown_event_desc, shutdown_first_cause,
            shutdown_rca, shutdown_actions, shutdown_action_by, shutdown_reported_by,
            shutdown_save_btn, shutdown_status_msg
        ]
    )

    shutdown_export_excel_btn.click(
        export_shutdown_excel_handler,
        outputs=[shutdown_export_file, shutdown_email_status, shutdown_export_file]
    )

    shutdown_send_email_btn.click(
        send_shutdown_to_managers,
        outputs=[shutdown_email_status]
    )

    # Auto-refresh on app load
    demo.load(
        refresh_shutdown_view,
        outputs=[
            shutdown_table, shutdown_id_selector,
            shutdown_id, shutdown_timestamp, shutdown_event_type, shutdown_event_classification,
            shutdown_main_cluster, shutdown_subcluster, shutdown_event_desc, shutdown_first_cause,
            shutdown_rca, shutdown_actions, shutdown_action_by, shutdown_reported_by,
            shutdown_save_btn, shutdown_status_msg
        ]
    )

# ======================
# LAUNCH APPLICATION WITH SCHEDULER
# ======================
if __name__ == "__main__":
    # Verify critical files
    missing_files = []
    for asset in ["wisonLOGO.png", "congoFLNG.png", "ENIcongo.jpg", "logo.png"]:
        if not os.path.exists(asset):
            missing_files.append(asset)
    if missing_files:
        print(f"\n⚠️  MISSING ASSET FILES: {', '.join(missing_files)}")
        print("   Place required logo files in application directory for full UI experience")

    # Launch application
    try:
        demo.launch()
    finally:
        # Graceful shutdown of scheduler
        if scheduler and scheduler.running:
            print("\n🛑 Shutting down scheduled reports...")
            scheduler.shutdown(wait=False)
            print("✅ Scheduler stopped")