import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import requests
import base64

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Udhyam AI Nudge Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    border-left: 5px solid #1a73e8;
}
.metric-value { font-size: 2.2rem; font-weight: 700; color: #1a73e8; }
.metric-label { font-size: 0.85rem; color: #666; margin-top: 4px; }
.status-sent    { background:#C6EFCE; color:#276221; padding:3px 10px; border-radius:12px; font-size:0.8rem; }
.status-pending { background:#FFEB9C; color:#7D6608; padding:3px 10px; border-radius:12px; font-size:0.8rem; }
.status-na      { background:#E8F0FE; color:#1a73e8; padding:3px 10px; border-radius:12px; font-size:0.8rem; }
.page-title     { font-size:1.8rem; font-weight:700; color:#1a73e8; margin-bottom:4px; }
.page-subtitle  { color:#666; margin-bottom:24px; }
</style>
""", unsafe_allow_html=True)

# ── Data loader ───────────────────────────────────────────────
CSV_PATH = "data/students.csv"

@st.cache_data(ttl=30)
def load_data():
    df = pd.read_csv(CSV_PATH)
    df["days_inactive"]  = pd.to_numeric(df["days_inactive"],  errors="coerce").fillna(0).astype(int)
    df["nudge_count"]    = pd.to_numeric(df["nudge_count"],    errors="coerce").fillna(0).astype(int)
    df["nudge_required"] = df["nudge_required"].fillna("No")
    df["nudge_sent"]     = df["nudge_sent"].fillna("No")
    df["nudge_type"]     = df["nudge_type"].fillna("")
    return df

def save_data(df):
    df.to_csv(CSV_PATH, index=False)
    st.cache_data.clear()

def row_color(row):
    if row["nudge_type"] == "CONGRATULATIONS":
        return ["background-color: #C6EFCE"] * len(row)
    elif row["days_inactive"] > 15:
        return ["background-color: #FFC7CE"] * len(row)
    elif row["nudge_required"] == "Yes":
        return ["background-color: #FFEB9C"] * len(row)
    return ["background-color: #C6EFCE"] * len(row)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Udhyam_Learning_Foundation_Logo.png/200px-Udhyam_Learning_Foundation_Logo.png",
             use_container_width=True) if False else None
    st.markdown("## 🎯 Udhyam Nudge")
    st.markdown("**AI-Powered Student Engagement**")
    st.divider()

    page = st.radio(
        "Navigate",
        ["📊 Student Overview", "📤 Send Nudges", "📈 Analytics"],
        label_visibility="collapsed"
    )
    st.divider()

    df_all = load_data()
    total      = len(df_all)
    on_track   = len(df_all[df_all["nudge_type"] == "CONGRATULATIONS"])
    need_nudge = len(df_all[(df_all["nudge_required"] == "Yes") & (df_all["nudge_sent"] == "No")])
    sent_today = len(df_all[df_all["nudge_sent"] == "Yes"])

    st.markdown(f"**Total Students:** {total}")
    st.markdown(f"🟢 On Track: **{on_track}**")
    st.markdown(f"🟡 Need Nudge: **{need_nudge}**")
    st.markdown(f"✅ Nudged: **{sent_today}**")
    st.divider()

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

# ═══════════════════════════════════════════════════════════════
#  PAGE 1 — STUDENT OVERVIEW
# ═══════════════════════════════════════════════════════════════
if page == "📊 Student Overview":
    st.markdown('<p class="page-title">📊 Student Overview</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">All 25 students with nudge status and submission progress</p>', unsafe_allow_html=True)

    df = load_data()

    # Metric cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{total}</div>
            <div class="metric-label">Total Students</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card" style="border-color:#34a853">
            <div class="metric-value" style="color:#34a853">{on_track}</div>
            <div class="metric-label">On Track ✅</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card" style="border-color:#fbbc04">
            <div class="metric-value" style="color:#fbbc04">{need_nudge}</div>
            <div class="metric-label">Need Nudge 🟡</div></div>""", unsafe_allow_html=True)
    with c4:
        inactive_count = len(df[df["days_inactive"] > 15])
        st.markdown(f"""<div class="metric-card" style="border-color:#ea4335">
            <div class="metric-value" style="color:#ea4335">{inactive_count}</div>
            <div class="metric-label">Very Inactive 🔴</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Filters
    st.markdown("#### Filters")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        states = ["All"] + sorted(df["state"].unique().tolist())
        sel_state = st.selectbox("State", states)
    with f2:
        btypes = ["All"] + sorted(df["business_type"].unique().tolist())
        sel_btype = st.selectbox("Business Type", btypes)
    with f3:
        nudge_opts = ["All", "Yes", "No"]
        sel_nudge = st.selectbox("Nudge Required", nudge_opts)
    with f4:
        sent_opts = ["All", "Sent", "Pending"]
        sel_sent = st.selectbox("Nudge Status", sent_opts)

    filtered = df.copy()
    if sel_state  != "All": filtered = filtered[filtered["state"]         == sel_state]
    if sel_btype  != "All": filtered = filtered[filtered["business_type"] == sel_btype]
    if sel_nudge  != "All": filtered = filtered[filtered["nudge_required"]== sel_nudge]
    if sel_sent == "Sent":    filtered = filtered[filtered["nudge_sent"] == "Yes"]
    if sel_sent == "Pending": filtered = filtered[filtered["nudge_sent"] == "No"]

    st.markdown(f"**Showing {len(filtered)} students**")

    # Display columns
    display_cols = ["student_id", "name", "class", "state", "business_type",
                    "business_idea", "days_inactive", "nudge_required",
                    "nudge_type", "nudge_sent", "nudge_count"]

    styled = filtered[display_cols].style.apply(row_color, axis=1)
    st.dataframe(styled, use_container_width=True, height=500)

    st.markdown("---")
    st.markdown("**Color Legend:**  🟢 On Track &nbsp;&nbsp; 🟡 Needs Nudge &nbsp;&nbsp; 🔴 Very Inactive (>15 days)")

# ═══════════════════════════════════════════════════════════════
#  PAGE 2 — SEND NUDGES
# ═══════════════════════════════════════════════════════════════
elif page == "📤 Send Nudges":
    st.markdown('<p class="page-title">📤 Send Nudges</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Generate AI Hindi messages and send via WhatsApp</p>', unsafe_allow_html=True)

    df = load_data()
    pending = df[(df["nudge_required"] == "Yes") & (df["nudge_sent"] == "No")].copy()

    if len(pending) == 0:
        st.success("✅ Sab students ko nudge bheja ja chuka hai! Koi pending nahi.")
        st.stop()

    st.info(f"**{len(pending)} students** mein nudge bhejna baaki hai.")

    # Select students
    st.markdown("#### Students Select Karo")
    col_sel, col_btn = st.columns([3, 1])
    with col_btn:
        if st.button("☑️ Select All", use_container_width=True):
            st.session_state["selected_all"] = True
        if st.button("☐ Deselect All", use_container_width=True):
            st.session_state["selected_all"] = False

    selected_ids = []
    for _, row in pending.iterrows():
        default = st.session_state.get("selected_all", False)
        label = (f"**{row['student_id']}** — {row['name']} | "
                 f"{row['business_type']} | {row['nudge_type']} | "
                 f"{row['days_inactive']} days inactive")
        checked = st.checkbox(label, value=default, key=f"chk_{row['student_id']}")
        if checked:
            selected_ids.append(row["student_id"])

    st.markdown("---")

    if not selected_ids:
        st.warning("Koi student select nahi kiya.")
        st.stop()

    st.markdown(f"**{len(selected_ids)} students selected**")

    # API keys from st.secrets
    def get_secret(key, fallback=""):
        try:
            return st.secrets[key]
        except Exception:
            return fallback

    ANTHROPIC_KEY  = get_secret("ANTHROPIC_API_KEY")
    TWILIO_SID     = get_secret("TWILIO_ACCOUNT_SID")
    TWILIO_TOKEN   = get_secret("TWILIO_AUTH_TOKEN")
    TWILIO_FROM    = get_secret("TWILIO_FROM", "whatsapp:+14155238886")
    DEFAULT_NUMBER = get_secret("DEFAULT_WHATSAPP_NUMBER", "")

    if not ANTHROPIC_KEY:
        st.error("ANTHROPIC_API_KEY not set in Streamlit Secrets. Go to Settings → Secrets.")
        st.stop()

    # Generate + Send button
    col_gen, col_send = st.columns(2)
    do_generate = col_gen.button("🤖 Generate Messages Only",  use_container_width=True, type="secondary")
    do_send     = col_send.button("🚀 Generate + Send WhatsApp", use_container_width=True, type="primary")

    SYSTEM_PROMPT = """You are a mentor sending WhatsApp messages to government school students in India who are working on their business projects.

Write messages in clean Hindi (Devanagari script only, no Roman Hindi).

Follow this EXACT structure for every message:

1. नमस्ते [student name]! 🙏
2. [Acknowledge what they have completed - be specific]
3. अब अगला कदम है — [specific next action based on nudge type]
4. [X] दिन से यह pending है, आज ही पूरा करें।

Rules:
- Pure Hindi Devanagari only, no English words except proper nouns
- Maximum 5 lines
- Mention student's actual business idea
- Be specific about which step is pending
- Tone: encouraging teacher, not casual friend
- No phrases like 'miss kiya' or 'yaad aa rahi thi'

Nudge type actions:
- IDEA_REMINDER: अपना बिज़नेस आइडिया लिखकर submit करें
- PROTOTYPE_REMINDER: अपने product की photo खींचकर submit करें
- PITCH_REMINDER: अपना business pitch video बनाकर submit करें
- REENGAGEMENT: वापस आएं और अपना पहला कदम उठाएं"""

    def call_claude(name, business_idea, business_type, nudge_type, days):
        headers = {
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        body = {
            "model": "claude-sonnet-4-6",
            "max_tokens": 300,
            "system": SYSTEM_PROMPT,
            "messages": [{
                "role": "user",
                "content": (f"Student: {name}\nBusiness Idea: {business_idea}\n"
                            f"Business Type: {business_type}\nNudge Type: {nudge_type}\n"
                            f"Days Pending: {days}\n\nWrite WhatsApp nudge message in Hindi.")
            }]
        }
        r = requests.post("https://api.anthropic.com/v1/messages", json=body, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json()["content"][0]["text"].strip()

    def send_whatsapp(to_number, message):
        if not TWILIO_SID or not TWILIO_TOKEN:
            return False, "Twilio credentials missing"
        url  = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
        auth = base64.b64encode(f"{TWILIO_SID}:{TWILIO_TOKEN}".encode()).decode()
        data = {
            "From": TWILIO_FROM,
            "To":   f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number,
            "Body": message
        }
        r = requests.post(url, data=data, headers={"Authorization": f"Basic {auth}"}, timeout=15)
        result = r.json()
        if r.status_code in [200, 201]:
            return True, result.get("sid", "")
        return False, result.get("message", "Unknown error")

    if do_generate or do_send:
        selected_rows = pending[pending["student_id"].isin(selected_ids)]
        results = []

        progress_bar = st.progress(0)
        status_box   = st.empty()
        log_area     = st.container()

        for i, (_, student) in enumerate(selected_rows.iterrows()):
            sid  = student["student_id"]
            name = student["name"]

            status_box.info(f"Processing **{sid} — {name}**... ({i+1}/{len(selected_rows)})")

            # Generate message
            try:
                msg = call_claude(
                    name, student["business_idea"], student["business_type"],
                    student["nudge_type"], student["days_inactive"]
                )
                gen_ok = True
            except Exception as e:
                msg    = ""
                gen_ok = False
                log_area.error(f"❌ **{sid}** — Claude API failed: {e}")

            # Send WhatsApp
            sent_ok = False
            twilio_status = ""
            if gen_ok and do_send:
                phone = str(student.get("phone_number", DEFAULT_NUMBER) or DEFAULT_NUMBER)
                if phone:
                    sent_ok, twilio_status = send_whatsapp(phone, msg)
                else:
                    twilio_status = "No phone number"

            # Update dataframe
            if gen_ok:
                today     = datetime.now().strftime("%Y-%m-%d")
                next_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
                idx = df[df["student_id"] == sid].index[0]
                df.at[idx, "last_message"]    = msg
                df.at[idx, "nudge_count"]     = int(df.at[idx, "nudge_count"]) + 1
                if do_send and sent_ok:
                    df.at[idx, "nudge_sent"]      = "Yes"
                    df.at[idx, "nudge_sent_date"] = today
                    df.at[idx, "next_nudge_date"] = next_date

                results.append({
                    "student": f"{sid} — {name}",
                    "nudge_type": student["nudge_type"],
                    "message": msg,
                    "whatsapp": "✅ Sent" if sent_ok else ("⏭️ Generated only" if not do_send else f"❌ {twilio_status}")
                })

            progress_bar.progress((i + 1) / len(selected_rows))
            time.sleep(0.5)

        # Save updated data
        save_data(df)
        status_box.success(f"✅ Done! Processed {len(results)} out of {len(selected_rows)} students.")

        # Show results
        st.markdown("---")
        st.markdown("### Generated Messages")
        for r in results:
            with st.expander(f"{r['whatsapp']}  |  {r['student']}  |  {r['nudge_type']}"):
                st.markdown(r["message"])

        # Download updated CSV
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Updated CSV",
            data=csv_bytes,
            file_name=f"students_updated_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# ═══════════════════════════════════════════════════════════════
#  PAGE 3 — ANALYTICS
# ═══════════════════════════════════════════════════════════════
elif page == "📈 Analytics":
    st.markdown('<p class="page-title">📈 Analytics</p>', unsafe_allow_html=True)
    st.markdown('<p class="page-subtitle">Engagement trends and nudge performance</p>', unsafe_allow_html=True)

    df = load_data()

    # Row 1 — Bar + Pie
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Nudge Type Distribution")
        nudge_counts = df[df["nudge_required"] == "Yes"]["nudge_type"].value_counts().reset_index()
        nudge_counts.columns = ["Nudge Type", "Count"]
        fig1 = px.bar(
            nudge_counts, x="Nudge Type", y="Count",
            color="Nudge Type",
            color_discrete_map={
                "REENGAGEMENT":       "#ea4335",
                "IDEA_REMINDER":      "#fbbc04",
                "PROTOTYPE_REMINDER": "#1a73e8",
                "PITCH_REMINDER":     "#34a853",
                "CONGRATULATIONS":    "#46bdc6"
            },
            text="Count"
        )
        fig1.update_traces(textposition="outside")
        fig1.update_layout(showlegend=False, height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("#### Submission Completion Rate")
        s1 = len(df[df["submission_1_status"] == "Submitted"])
        s2 = len(df[df["submission_2_status"] == "Submitted"])
        s3 = len(df[df["submission_3_status"] == "Submitted"])
        not_started = len(df[df["submission_1_status"] == "Not Submitted"])
        pie_data = pd.DataFrame({
            "Stage": ["All 3 Done", "Idea Only", "Idea + Prototype", "Not Started"],
            "Count": [
                len(df[(df["submission_1_status"]=="Submitted") & (df["submission_2_status"]=="Submitted") & (df["submission_3_status"]=="Submitted")]),
                len(df[(df["submission_1_status"]=="Submitted") & (df["submission_2_status"]=="Not Submitted")]),
                len(df[(df["submission_1_status"]=="Submitted") & (df["submission_2_status"]=="Submitted") & (df["submission_3_status"]=="Not Submitted")]),
                not_started
            ]
        })
        fig2 = px.pie(
            pie_data, names="Stage", values="Count",
            color_discrete_sequence=["#34a853","#fbbc04","#1a73e8","#ea4335"],
            hole=0.4
        )
        fig2.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig2, use_container_width=True)

    # Row 2 — Bar by Business Type + Days Inactive histogram
    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### Students by Business Type")
        btype_counts = df.groupby("business_type")["nudge_required"].value_counts().reset_index()
        btype_counts.columns = ["Business Type", "Nudge Required", "Count"]
        fig3 = px.bar(
            btype_counts, x="Business Type", y="Count",
            color="Nudge Required",
            color_discrete_map={"Yes": "#ea4335", "No": "#34a853"},
            barmode="stack", text="Count"
        )
        fig3.update_traces(textposition="inside")
        fig3.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown("#### Days Inactive Distribution")
        fig4 = px.histogram(
            df, x="days_inactive", nbins=10,
            color_discrete_sequence=["#1a73e8"],
            labels={"days_inactive": "Days Inactive", "count": "Students"}
        )
        fig4.add_vline(x=7,  line_dash="dash", line_color="#fbbc04", annotation_text="7d threshold")
        fig4.add_vline(x=15, line_dash="dash", line_color="#ea4335", annotation_text="15d threshold")
        fig4.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig4, use_container_width=True)

    # Row 3 — State-wise table + Nudge sent summary
    col5, col6 = st.columns(2)

    with col5:
        st.markdown("#### State-wise Summary")
        state_summary = df.groupby("state").agg(
            Total=("student_id", "count"),
            Need_Nudge=("nudge_required", lambda x: (x == "Yes").sum()),
            Nudge_Sent=("nudge_sent", lambda x: (x == "Yes").sum()),
            Avg_Inactive=("days_inactive", "mean")
        ).reset_index()
        state_summary["Avg_Inactive"] = state_summary["Avg_Inactive"].round(1)
        st.dataframe(state_summary, use_container_width=True, hide_index=True)

    with col6:
        st.markdown("#### Nudge Sent vs Pending")
        sent_summary = df[df["nudge_required"] == "Yes"]["nudge_sent"].value_counts().reset_index()
        sent_summary.columns = ["Status", "Count"]
        sent_summary["Status"] = sent_summary["Status"].map({"Yes": "Sent ✅", "No": "Pending 🟡"})
        fig5 = px.pie(
            sent_summary, names="Status", values="Count",
            color_discrete_sequence=["#34a853", "#fbbc04"],
            hole=0.5
        )
        fig5.update_layout(height=300, margin=dict(t=20, b=20))
        st.plotly_chart(fig5, use_container_width=True)

    # Recent nudges table
    st.markdown("---")
    st.markdown("#### Recent Nudges Sent")
    sent_df = df[df["nudge_sent"] == "Yes"][
        ["student_id", "name", "business_type", "nudge_type",
         "nudge_sent_date", "nudge_count", "last_message"]
    ].copy()

    if len(sent_df) == 0:
        st.info("Abhi tak koi nudge nahi bheja gaya. 'Send Nudges' page pe jao.")
    else:
        st.dataframe(sent_df, use_container_width=True, hide_index=True)
