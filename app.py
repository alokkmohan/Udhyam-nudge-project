import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import base64
import time
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Udhyam Nudge Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
[data-testid="stMetric"] {
    background: white;
    border-radius: 10px;
    padding: 16px 20px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.07);
}
[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700 !important; }
div[data-testid="stMetricLabel"] { font-size: 0.8rem !important; }
.chart-title { font-size: 0.95rem; font-weight: 600; color: #333; margin-bottom: 4px; }
.section-header {
    font-size: 1rem; font-weight: 700; color: #1a73e8;
    border-bottom: 2px solid #e8f0fe; padding-bottom: 6px; margin: 20px 0 12px 0;
}
</style>
""", unsafe_allow_html=True)

# ── DATA ──────────────────────────────────────────────────────
CSV_PATH = "data/students.csv"

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(CSV_PATH)
    df["days_inactive"] = pd.to_numeric(df["days_inactive"], errors="coerce").fillna(0).astype(int)
    df["nudge_count"]   = pd.to_numeric(df["nudge_count"],   errors="coerce").fillna(0).astype(int)
    for col in ["nudge_required", "nudge_sent", "nudge_type",
                "submission_1_status", "submission_2_status", "submission_3_status"]:
        df[col] = df[col].fillna("").astype(str).str.strip()
    return df

df = load_data()

# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 Udhyam Nudge")
    st.markdown("AI-Powered Student Engagement")
    st.divider()

    page = st.radio("", ["🏠 Home", "📋 Nudge List"], label_visibility="collapsed")
    st.divider()

    if page == "📋 Nudge List":
        st.markdown("**Filters**")
        states = ["All"] + sorted(df["state"].unique().tolist())
        btypes = ["All"] + sorted(df["business_type"].unique().tolist())
        ntypes = ["All"] + sorted([x for x in df["nudge_type"].unique() if x])

        f_state  = st.selectbox("State",         states)
        f_btype  = st.selectbox("Business Type", btypes)
        f_ntype  = st.selectbox("Nudge Type",    ntypes)
        f_search = st.text_input("Search Name",  placeholder="Type name...")
        st.divider()

    if st.button("🔄 Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Updated: {datetime.now().strftime('%H:%M:%S')}")

# ══════════════════════════════════════════════════════════════
#  PAGE 1 — HOME
# ══════════════════════════════════════════════════════════════
if page == "🏠 Home":

    st.markdown("## 🏠 Student Overview & Analytics")

    # ── Metrics ───────────────────────────────────────────────
    total     = len(df)
    on_track  = len(df[df["nudge_type"] == "CONGRATULATIONS"])
    need_nudge= len(df[(df["nudge_required"] == "Yes") & (df["nudge_sent"] == "No")])
    very_inact= len(df[df["days_inactive"] > 15])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Students",  total,      delta=None)
    c2.metric("✅ On Track",      on_track,   delta=None)
    c3.metric("⚠️ Need Nudge",   need_nudge, delta=None)
    c4.metric("🔴 Very Inactive", very_inact, delta=None)

    # colour the metric borders via CSS injection
    st.markdown(f"""
    <style>
    [data-testid="stMetric"]:nth-child(1) {{ border-left: 5px solid #1a73e8; }}
    [data-testid="stMetric"]:nth-child(2) {{ border-left: 5px solid #34a853; }}
    [data-testid="stMetric"]:nth-child(3) {{ border-left: 5px solid #fb8c00; }}
    [data-testid="stMetric"]:nth-child(4) {{ border-left: 5px solid #ea4335; }}
    </style>""", unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────
    st.markdown('<div class="section-header">📊 Analytics</div>', unsafe_allow_html=True)
    ch1, ch2, ch3 = st.columns(3)

    # Pie — Nudge Type
    with ch1:
        st.markdown('<div class="chart-title">Nudge Type Distribution</div>', unsafe_allow_html=True)
        nudge_df = df[df["nudge_type"] != ""]["nudge_type"].value_counts().reset_index()
        nudge_df.columns = ["Nudge Type", "Count"]
        color_map = {
            "CONGRATULATIONS":   "#34a853",
            "REENGAGEMENT":      "#ea4335",
            "IDEA_REMINDER":     "#fbbc04",
            "PROTOTYPE_REMINDER":"#1a73e8",
            "PITCH_REMINDER":    "#46bdc6",
        }
        fig1 = px.pie(
            nudge_df, names="Nudge Type", values="Count",
            color="Nudge Type", color_discrete_map=color_map,
            hole=0.4
        )
        fig1.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=270,
                           legend=dict(font_size=10, orientation="v"))
        fig1.update_traces(textfont_size=11)
        st.plotly_chart(fig1, use_container_width=True)

    # Bar — By State
    with ch2:
        st.markdown('<div class="chart-title">Students by State</div>', unsafe_allow_html=True)
        state_df = df.groupby("state").size().reset_index(name="Count").sort_values("Count", ascending=True)
        fig2 = px.bar(
            state_df, x="Count", y="state", orientation="h",
            color="Count", color_continuous_scale=["#c8e6ff","#1a73e8"],
            text="Count"
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=270,
                           coloraxis_showscale=False,
                           yaxis_title="", xaxis_title="Students")
        st.plotly_chart(fig2, use_container_width=True)

    # Bar — By Business Type
    with ch3:
        st.markdown('<div class="chart-title">Students by Business Type</div>', unsafe_allow_html=True)
        btype_df = df.groupby("business_type").size().reset_index(name="Count").sort_values("Count", ascending=True)
        fig3 = px.bar(
            btype_df, x="Count", y="business_type", orientation="h",
            color="Count", color_continuous_scale=["#c8e6c9","#34a853"],
            text="Count"
        )
        fig3.update_traces(textposition="outside")
        fig3.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=270,
                           coloraxis_showscale=False,
                           yaxis_title="", xaxis_title="Students")
        st.plotly_chart(fig3, use_container_width=True)

    # ── Submission Progress Bars ───────────────────────────────
    st.markdown('<div class="section-header">📝 Submission Progress</div>', unsafe_allow_html=True)

    s1_pct = round(len(df[df["submission_1_status"] == "Submitted"]) / total * 100)
    s2_pct = round(len(df[df["submission_2_status"] == "Submitted"]) / total * 100)
    s3_pct = round(len(df[df["submission_3_status"] == "Submitted"]) / total * 100)

    p1, p2, p3 = st.columns(3)

    with p1:
        st.markdown(f"**Submission 1 — Business Idea** &nbsp; `{s1_pct}%`")
        st.progress(s1_pct / 100)
        st.caption(f"{len(df[df['submission_1_status']=='Submitted'])} of {total} students submitted")

    with p2:
        st.markdown(f"**Submission 2 — Prototype** &nbsp; `{s2_pct}%`")
        st.progress(s2_pct / 100)
        st.caption(f"{len(df[df['submission_2_status']=='Submitted'])} of {total} students submitted")

    with p3:
        st.markdown(f"**Submission 3 — Pitch** &nbsp; `{s3_pct}%`")
        st.progress(s3_pct / 100)
        st.caption(f"{len(df[df['submission_3_status']=='Submitted'])} of {total} students submitted")

# ══════════════════════════════════════════════════════════════
#  PAGE 2 — NUDGE LIST
# ══════════════════════════════════════════════════════════════
elif page == "📋 Nudge List":

    st.markdown("## 📋 Student Nudge List")

    # ── Apply Filters ─────────────────────────────────────────
    filtered = df.copy()
    if f_state  != "All": filtered = filtered[filtered["state"]         == f_state]
    if f_btype  != "All": filtered = filtered[filtered["business_type"] == f_btype]
    if f_ntype  != "All": filtered = filtered[filtered["nudge_type"]    == f_ntype]
    if f_search:          filtered = filtered[filtered["name"].str.contains(f_search, case=False, na=False)]

    st.caption(f"Showing **{len(filtered)}** of {len(df)} students")

    # ── Build Display DataFrame ───────────────────────────────
    def sub_icon(val):
        return "✅ Done" if val == "Submitted" else "🔴 Pending"

    def sent_icon(val):
        return "✅ Sent" if val == "Yes" else "⏳ Pending"

    def days_label(d):
        d = int(d)
        if d < 7:   return f"🟢 {d}d"
        elif d <= 15: return f"🟠 {d}d"
        else:         return f"🔴 {d}d"

    display = pd.DataFrame({
        "ID":           filtered["student_id"],
        "Name":         filtered["name"],
        "Class":        filtered["class"],
        "State":        filtered["state"],
        "Business Type":filtered["business_type"],
        "Business Idea":filtered["business_idea"],
        "Sub 1":        filtered["submission_1_status"].apply(sub_icon),
        "Sub 2":        filtered["submission_2_status"].apply(sub_icon),
        "Sub 3":        filtered["submission_3_status"].apply(sub_icon),
        "Days Inactive":filtered["days_inactive"].apply(days_label),
        "Nudge Type":   filtered["nudge_type"].replace("", "—"),
        "Nudge Sent":   filtered["nudge_sent"].apply(sent_icon),
        "_nt":          filtered["nudge_type"],   # hidden for styling
    })

    # ── Row Colouring ─────────────────────────────────────────
    def row_color(row):
        nt = row["_nt"]
        if nt == "CONGRATULATIONS":
            bg = "background-color: #e8f5e9"
        elif nt == "REENGAGEMENT":
            bg = "background-color: #ffebee"
        elif nt in ("IDEA_REMINDER", "PROTOTYPE_REMINDER", "PITCH_REMINDER"):
            bg = "background-color: #fff8e1"
        else:
            bg = "background-color: #e8f5e9"
        return [bg] * len(row)

    visible_cols = ["ID","Name","Class","State","Business Type","Business Idea",
                    "Sub 1","Sub 2","Sub 3","Days Inactive","Nudge Type","Nudge Sent"]

    styled = display.style.apply(row_color, axis=1).hide(axis="index")

    st.dataframe(
        styled,
        use_container_width=True,
        height=480,
        column_order=visible_cols,
    )

    # ── Legend ────────────────────────────────────────────────
    st.markdown(
        "🟩 On Track &nbsp;&nbsp; 🟨 Needs Reminder &nbsp;&nbsp; 🟥 Reengagement Required",
        unsafe_allow_html=True
    )

    # ── Send Nudge Section ────────────────────────────────────
    st.divider()
    st.markdown("### 🚀 Send Nudges")

    pending = filtered[(filtered["nudge_required"] == "Yes") & (filtered["nudge_sent"] == "No")]

    if len(pending) == 0:
        st.success("✅ Is filter mein koi pending nudge nahi hai.")
    else:
        st.info(f"**{len(pending)} students** is filter mein nudge ke liye eligible hain.")

        selected_names = st.multiselect(
            "Students select karo:",
            options=pending["name"].tolist(),
            default=pending["name"].tolist()
        )

        col_gen, col_send = st.columns(2)
        do_generate = col_gen.button("🤖 Generate Messages Only",    use_container_width=True, type="secondary")
        do_send     = col_send.button("📲 Generate + Send WhatsApp", use_container_width=True, type="primary")

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

Nudge type actions:
- IDEA_REMINDER: अपना बिज़नेस आइडिया लिखकर submit करें
- PROTOTYPE_REMINDER: अपने product की photo खींचकर submit करें
- PITCH_REMINDER: अपना business pitch video बनाकर submit करें
- REENGAGEMENT: वापस आएं और अपना पहला कदम उठाएं"""

        def get_secret(key, fallback=""):
            try:    return st.secrets[key]
            except: return fallback

        def call_claude(row):
            key = get_secret("ANTHROPIC_API_KEY")
            if not key:
                return "⚠️ ANTHROPIC_API_KEY missing in secrets."
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={
                    "model": "claude-sonnet-4-6", "max_tokens": 300,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content":
                        f"Student: {row['name']}\nBusiness Idea: {row['business_idea']}\n"
                        f"Business Type: {row['business_type']}\nNudge Type: {row['nudge_type']}\n"
                        f"Days Pending: {row['days_inactive']}\n\nWrite WhatsApp nudge message in Hindi."
                    }]
                }, timeout=30
            )
            r.raise_for_status()
            return r.json()["content"][0]["text"].strip()

        def send_whatsapp(phone, message):
            sid   = get_secret("TWILIO_ACCOUNT_SID")
            token = get_secret("TWILIO_AUTH_TOKEN")
            frm   = get_secret("TWILIO_FROM", "whatsapp:+14155238886")
            if not sid or not token:
                return False, "Twilio credentials missing"
            to  = f"whatsapp:{phone}" if not phone.startswith("whatsapp:") else phone
            auth = base64.b64encode(f"{sid}:{token}".encode()).decode()
            r = requests.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
                headers={"Authorization": f"Basic {auth}"},
                data={"From": frm, "To": to, "Body": message}, timeout=15
            )
            res = r.json()
            if r.status_code in [200, 201]:
                return True, res.get("sid", "")
            return False, res.get("message", "Unknown error")

        if do_generate or do_send:
            if not selected_names:
                st.warning("Koi student select nahi kiya.")
            else:
                sel_rows = pending[pending["name"].isin(selected_names)]
                results  = []
                bar      = st.progress(0, text="Processing...")
                status   = st.empty()

                for i, (_, row) in enumerate(sel_rows.iterrows()):
                    status.info(f"⏳ Processing **{row['student_id']} — {row['name']}** ({i+1}/{len(sel_rows)})")

                    try:
                        msg    = call_claude(row)
                        gen_ok = True
                    except Exception as e:
                        msg    = ""
                        gen_ok = False
                        st.error(f"❌ Claude failed for {row['student_id']}: {e}")

                    sent_ok      = False
                    twilio_note  = ""
                    if gen_ok and do_send:
                        phone = str(row.get("phone_number", get_secret("DEFAULT_WHATSAPP_NUMBER")) or "")
                        if phone:
                            sent_ok, twilio_note = send_whatsapp(phone, msg)
                        else:
                            twilio_note = "No phone number"

                    results.append({
                        "student": f"{row['student_id']} — {row['name']}",
                        "nudge_type": row["nudge_type"],
                        "message": msg,
                        "status": "✅ Sent" if sent_ok else ("🤖 Generated" if not do_send else f"❌ {twilio_note}"),
                        "gen_ok": gen_ok,
                        "sent_ok": sent_ok,
                        "idx": row.name
                    })

                    bar.progress((i + 1) / len(sel_rows), text=f"Done {i+1}/{len(sel_rows)}")
                    time.sleep(0.5)

                status.success(f"✅ Complete! {sum(r['gen_ok'] for r in results)} messages generated.")

                # Show results
                st.markdown("---")
                for r in results:
                    with st.expander(f"{r['status']}  |  {r['student']}  |  {r['nudge_type']}"):
                        st.text(r["message"])

                # Download
                out_df = pd.DataFrame([{
                    "student": r["student"], "nudge_type": r["nudge_type"],
                    "message": r["message"],  "status": r["status"],
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                } for r in results if r["gen_ok"]])

                st.download_button(
                    "⬇️ Download Results CSV",
                    data=out_df.to_csv(index=False).encode("utf-8"),
                    file_name=f"nudges_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
