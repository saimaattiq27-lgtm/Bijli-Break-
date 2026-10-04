import streamlit as st
from groq import Groq

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Bijli Break",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------- CSS ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* { font-family: Inter, sans-serif; }

.stApp {
    background: #f7f8fb;
}

.block-container {
    max-width: 1100px;
    padding-top: 1rem;
    padding-bottom: 3rem;
}

.hero {
    background: linear-gradient(135deg, #fff7d8, #fffdf7);
    border: 1px solid #f1df9a;
    border-radius: 24px;
    padding: 20px 24px;
    margin-bottom: 18px;
}

.brand {
    color: #17324d;
    font-size: 30px;
    font-weight: 800;
    margin: 0;
}

.tagline {
    color: #5d6d7e;
    font-size: 15px;
}

.section-title {
    color: #17324d;
    font-size: 24px;
    font-weight: 800;
    margin-top: 8px;
}

.section-subtitle {
    color: #69798a;
    margin-bottom: 18px;
}

.card {
    background: white;
    border: 1px solid #e7ebf0;
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 12px;
    box-shadow: 0 4px 16px rgba(20, 40, 60, .05);
}

.light-block {
    background: #fff5cc;
    border: 1px solid #f1d66d;
    border-radius: 18px;
    padding: 16px;
    margin: 8px 0 16px;
}

.outage-block {
    background: #4d5663;
    color: white;
    border-radius: 18px;
    padding: 16px;
    margin: 8px 0 16px;
}

.task-light, .task-dark {
    border-radius: 11px;
    padding: 10px 12px;
    margin-top: 9px;
}

.task-light {
    background: rgba(255,255,255,.82);
    color: #24384c;
}

.task-dark {
    background: rgba(255,255,255,.12);
    color: white;
}

.next-banner {
    background: #fff0b9;
    border: 1px solid #f1d26a;
    border-radius: 16px;
    padding: 14px 16px;
    margin: 12px 0 18px;
}

.metric {
    background: white;
    border: 1px solid #e7ebf0;
    border-radius: 15px;
    padding: 13px;
    text-align: center;
}

.metric-number {
    color: #17324d;
    font-size: 24px;
    font-weight: 800;
}

.metric-label {
    color: #718092;
    font-size: 12px;
}

.badge {
    display: inline-block;
    background: #eef2f6;
    color: #56687b;
    border-radius: 20px;
    padding: 4px 9px;
    margin: 5px 4px 0 0;
    font-size: 12px;
}

div.stButton > button {
    border-radius: 12px;
    font-weight: 700;
    min-height: 42px;
}

div.stButton > button[kind="primary"] {
    background: #f7c83f;
    border-color: #f7c83f;
    color: #172d43;
}

div.stButton > button[kind="primary"]:hover {
    background: #edb82c;
    border-color: #edb82c;
}

@media (max-width: 700px) {
    .block-container {
        padding-left: .75rem;
        padding-right: .75rem;
    }
    .brand { font-size: 25px; }
}
</style>
""", unsafe_allow_html=True)

# ---------------- STATE ----------------
if "page" not in st.session_state:
    st.session_state.page = "Setup"

if "outages" not in st.session_state:
    st.session_state.outages = [
        {"start": "10:00", "end": "12:00"},
        {"start": "16:00", "end": "18:00"},
    ]

if "tasks" not in st.session_state:
    st.session_state.tasks = [
        {"id": 1, "name": "Finish assignment", "mins": 90, "type": "Screen", "priority": "High", "done": False},
        {"id": 2, "name": "Revise Chapter 4 notes", "mins": 60, "type": "Offline", "priority": "Normal", "done": False},
        {"id": 3, "name": "Past paper", "mins": 60, "type": "Offline", "priority": "Normal", "done": False},
    ]

if "day_start" not in st.session_state:
    st.session_state.day_start = "08:00"

if "day_end" not in st.session_state:
    st.session_state.day_end = "23:00"

if "next_id" not in st.session_state:
    st.session_state.next_id = 4

# ---------------- HELPERS ----------------
def to_min(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m

def fmt_time(m):
    h = (m // 60) % 24
    minute = m % 60
    suffix = "AM" if h < 12 else "PM"
    display_h = h % 12 or 12
    return f"{display_h}:{minute:02d} {suffix}"

def get_blocks():
    start = to_min(st.session_state.day_start)
    end = to_min(st.session_state.day_end)
    cursor = start
    blocks = []

    for outage in sorted(st.session_state.outages, key=lambda x: to_min(x["start"])):
        a = max(to_min(outage["start"]), start)
        b = min(to_min(outage["end"]), end)

        if a >= b:
            continue

        if a > cursor:
            blocks.append({"type": "light", "from": cursor, "to": a})

        blocks.append({"type": "outage", "from": a, "to": b})
        cursor = b

    if cursor < end:
        blocks.append({"type": "light", "from": cursor, "to": end})

    return blocks

def plan_tasks():
    blocks = get_blocks()
    capacities = [b["to"] - b["from"] for b in blocks]
    used = [0] * len(blocks)
    placed = []
    moved = []

    pending = [t for t in st.session_state.tasks if not t["done"]]
    pending.sort(key=lambda t: (0 if t["priority"] == "High" else 1, t["id"]))

    for task in pending:
        remaining = task["mins"]

        for i, block in enumerate(blocks):
            if remaining <= 0:
                break

            if task["type"] == "Screen" and block["type"] != "light":
                continue

            if task["type"] == "Offline" and block["type"] != "outage":
                continue

            available = capacities[i] - used[i]
            if available <= 0:
                continue

            take = min(remaining, available)
            start = block["from"] + used[i]
            end = start + take

            placed.append({
                "block": i,
                "start": start,
                "end": end,
                "task": task,
            })

            used[i] += take
            remaining -= take

        if remaining > 0:
            moved.append({
                "name": task["name"],
                "mins": remaining,
                "type": task["type"],
            })

    return blocks, placed, moved

def next_outage():
    # Uses the current clock for a simple banner.
    from datetime import datetime
    now = datetime.now()
    current = now.hour * 60 + now.minute

    upcoming = [
        to_min(o["start"])
        for o in st.session_state.outages
        if to_min(o["start"]) > current
    ]

    if not upcoming:
        return "No more outages scheduled today."

    diff = min(upcoming) - current
    return f"Next outage in {diff // 60}h {diff % 60}m"

def ask_groq():
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    model = st.secrets.get("GROQ_MODEL", "openai/gpt-oss-20b")

    prompt = f"""
You are the AI study assistant inside an app called Bijli Break.

The student's outage slots are:
{st.session_state.outages}

Suggest:
1. Three offline study tasks suitable for outage periods.
2. Three screen/internet tasks suitable for light periods.

Keep suggestions practical and short for a student.
Return exactly two headings: OFFLINE TASKS and SCREEN TASKS.
Use bullet points only.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    return response.choices[0].message.content

# ---------------- HEADER ----------------
st.markdown("""
<div class="hero">
    <div class="brand">⚡ Bijli Break</div>
    <div class="tagline">Plan your day with light ☀️</div>
</div>
""", unsafe_allow_html=True)

# ---------------- NAV ----------------
nav1, nav2, nav3 = st.columns(3)

with nav1:
    if st.button("⚙️ Setup", use_container_width=True):
        st.session_state.page = "Setup"
        st.rerun()

with nav2:
    if st.button("📝 Tasks", use_container_width=True):
        st.session_state.page = "Tasks"
        st.rerun()

with nav3:
    if st.button("📅 Today", use_container_width=True):
        st.session_state.page = "Today"
        st.rerun()

st.divider()

# ============================================================
# SETUP
# ============================================================
if st.session_state.page == "Setup":

    st.markdown('<div class="section-title">Today\'s outage times</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Add the times when there will be no electricity in your area.</div>',
        unsafe_allow_html=True
    )

    for i, outage in enumerate(st.session_state.outages):
        c1, c2, c3 = st.columns([4, 4, 1])

        with c1:
            value = st.time_input(
                "Start" if i == 0 else " ",
                value=__import__("datetime").datetime.strptime(outage["start"], "%H:%M").time(),
                key=f"start_{i}"
            )
            outage["start"] = value.strftime("%H:%M")

        with c2:
            value = st.time_input(
                "End" if i == 0 else "  ",
                value=__import__("datetime").datetime.strptime(outage["end"], "%H:%M").time(),
                key=f"end_{i}"
            )
            outage["end"] = value.strftime("%H:%M")

        with c3:
            st.write("")
            if st.button("🗑️", key=f"delete_{i}"):
                st.session_state.outages.pop(i)
                st.rerun()

    if st.button("＋ Add Outage", use_container_width=True):
        st.session_state.outages.append({"start": "10:00", "end": "12:00"})
        st.rerun()

    st.markdown("###")

    c1, c2 = st.columns(2)

    with c1:
        value = st.time_input(
            "Day starts",
            value=__import__("datetime").datetime.strptime(
                st.session_state.day_start, "%H:%M"
            ).time()
        )
        st.session_state.day_start = value.strftime("%H:%M")

    with c2:
        value = st.time_input(
            "Day ends",
            value=__import__("datetime").datetime.strptime(
                st.session_state.day_end, "%H:%M"
            ).time()
        )
        st.session_state.day_end = value.strftime("%H:%M")

    if st.button("Continue  →", type="primary", use_container_width=True):
        st.session_state.page = "Tasks"
        st.rerun()

# ============================================================
# TASKS
# ============================================================
elif st.session_state.page == "Tasks":

    st.markdown('<div class="section-title">Add Tasks</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Add the work you need to finish today.</div>',
        unsafe_allow_html=True
    )

    with st.container(border=True):
        name = st.text_input("Task name", placeholder="e.g. Finish assignment")
        mins = st.number_input(
            "Time needed (minutes)",
            min_value=5,
            max_value=600,
            value=60,
            step=5
        )

        task_type = st.radio(
            "Type",
            ["Screen", "Offline", "Either"],
            horizontal=True
        )

        priority = st.radio(
            "Priority",
            ["High", "Normal"],
            horizontal=True
        )

        if st.button("＋ Add Task", type="primary", use_container_width=True):
            if name.strip():
                st.session_state.tasks.append({
                    "id": st.session_state.next_id,
                    "name": name.strip(),
                    "mins": int(mins),
                    "type": task_type,
                    "priority": priority,
                    "done": False
                })
                st.session_state.next_id += 1
                st.success("Task added!")
                st.rerun()
            else:
                st.warning("Please enter a task name.")

    st.markdown("### Your tasks")

    for i, task in enumerate(st.session_state.tasks):
        c1, c2 = st.columns([9, 1])

        with c1:
            status = "☑️" if task["done"] else "⬜"
            st.markdown(
                f"""
                <div class="card">
                    <b>{status} {task['name']}</b><br>
                    <span class="badge">{task['mins']} min</span>
                    <span class="badge">{task['type']}</span>
                    <span class="badge">{task['priority']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c2:
            if st.button("🗑️", key=f"task_delete_{task['id']}"):
                st.session_state.tasks.pop(i)
                st.rerun()

    if st.button("Plan My Day  →", type="primary", use_container_width=True):
        st.session_state.page = "Today"
        st.rerun()

    st.markdown("### ✨ AI Study Assistant")

    if st.button("Ask Groq for study ideas", use_container_width=True):
        try:
            result = ask_groq()
            st.markdown(
                f'<div class="card">{result.replace(chr(10), "<br>")}</div>',
                unsafe_allow_html=True
            )
        except Exception as e:
            st.error("Groq could not be used. Check your Streamlit Secrets.")
            st.caption(str(e))

# ============================================================
# TODAY
# ============================================================
elif st.session_state.page == "Today":

    st.markdown('<div class="section-title">Today</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Your study day arranged around the electricity you have.</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="next-banner">
            🔔 <b>{next_outage()}</b><br>
            <span>Don't forget to charge your devices!</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    blocks, placed, moved = plan_tasks()

    total = sum(t["mins"] for t in st.session_state.tasks)
    completed = sum(t["mins"] for t in st.session_state.tasks if t["done"])

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f'<div class="metric"><div class="metric-number">{len(st.session_state.tasks)}</div><div class="metric-label">Tasks</div></div>',
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f'<div class="metric"><div class="metric-number">{total}</div><div class="metric-label">Total minutes</div></div>',
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            f'<div class="metric"><div class="metric-number">{completed}</div><div class="metric-label">Completed minutes</div></div>',
            unsafe_allow_html=True
        )

    st.markdown("###")

    for index, block in enumerate(blocks):

        items = [p for p in placed if p["block"] == index]

        if block["type"] == "light":
            st.markdown(
                f"""
                <div class="light-block">
                    <b>☀️ LIGHT</b>
                    <span style="float:right">{fmt_time(block["from"])} – {fmt_time(block["to"])}</span>
                """,
                unsafe_allow_html=True
            )
            task_class = "task-light"
        else:
            st.markdown(
                f"""
                <div class="outage-block">
                    <b>🔌 OUTAGE</b>
                    <span style="float:right">{fmt_time(block["from"])} – {fmt_time(block["to"])}</span>
                """,
                unsafe_allow_html=True
            )
            task_class = "task-dark"

        if items:
            for item in items:
                task = item["task"]
                st.markdown(
                    f"""
                    <div class="{task_class}">
                        ⬜ <b>{task['name']}</b><br>
                        <small>{item['end'] - item['start']} min • {task['type']} • {task['priority']}</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                f'<div class="{task_class}">Free time</div>',
                unsafe_allow_html=True
            )

        st.markdown("</div>", unsafe_allow_html=True)

    if moved:
        st.markdown("### 📌 Moved to tomorrow")

        for task in moved:
            st.warning(
                f"{task['name']} — {task['mins']} min remaining ({task['type']})"
            )

    st.markdown("###")

    if st.button("← Back to Tasks", use_container_width=True):
        st.session_state.page = "Tasks"
        st.rerun()
