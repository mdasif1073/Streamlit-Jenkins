import streamlit as st
import pandas as pd
from datetime import datetime, date, time

st.set_page_config(page_title="Predict + Scheduler", page_icon="📅", layout="wide")

# -----------------------------
# Helpers
# -----------------------------
def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, x))

def predict_productivity(sleep_hours, focus_hours, workload_level, exercise_mins):
    """
    Simple scoring model (rule-based prediction):
    - Sleep & focus improve score
    - High workload reduces score
    - Exercise improves score
    """
    score = 50
    score += (sleep_hours - 6) * 6         # ideal around 7–8
    score += (focus_hours - 3) * 5         # ideal around 4–6
    score -= (workload_level - 3) * 7      # higher workload => lower score
    score += (exercise_mins / 10) * 1.5    # exercise helps

    return clamp(int(round(score)))

def init_state():
    if "events" not in st.session_state:
        st.session_state.events = []  # list of dicts

def add_event(title, event_date, event_time, duration_mins, notes):
    dt = datetime.combine(event_date, event_time)
    st.session_state.events.append({
        "Title": title.strip(),
        "Date": event_date.isoformat(),
        "Time": event_time.strftime("%H:%M"),
        "Duration(min)": int(duration_mins),
        "Notes": notes.strip(),
        "SortDT": dt
    })

def events_df():
    if not st.session_state.events:
        return pd.DataFrame(columns=["Title", "Date", "Time", "Duration(min)", "Notes"])
    df = pd.DataFrame(st.session_state.events)
    df = df.sort_values("SortDT").drop(columns=["SortDT"]).reset_index(drop=True)
    return df

# -----------------------------
# UI
# -----------------------------
init_state()

st.title("📅 Smart Scheduler (Update 1)")
st.caption("Simple mobile-calendar style agenda ✅ Updated via Jenkins")


tab1, tab2 = st.tabs(["📅 Scheduler", "🔮 Prediction"])

# =========================================================
# TAB 1: Scheduler
# =========================================================
with tab1:
    left, right = st.columns([1.1, 1.4])

    with left:
        st.subheader("Add Event")

        title = st.text_input("Event title", placeholder="Eg: ML Lab / Gym / Meeting")
        event_date = st.date_input("Date", value=date.today())
        event_time = st.time_input("Time", value=time(10, 0))
        duration = st.number_input("Duration (minutes)", min_value=5, max_value=600, value=60, step=5)
        notes = st.text_area("Notes (optional)", height=80, placeholder="Eg: Bring notebook / call link...")

        c1, c2 = st.columns(2)
        with c1:
            add_btn = st.button("➕ Add to Calendar", use_container_width=True)
        with c2:
            clear_btn = st.button("🧹 Clear All", use_container_width=True)

        if add_btn:
            if not title.strip():
                st.error("Please enter an event title.")
            else:
                add_event(title, event_date, event_time, duration, notes)
                st.success("Event added!")

        if clear_btn:
            st.session_state.events = []
            st.warning("All events cleared.")

    with right:
        st.subheader("Agenda (Mobile Calendar Style)")

        df = events_df()

        # Filter like calendar day view
        filter_day = st.date_input("View events for date", value=date.today(), key="filter_day")
        if not df.empty:
            df_day = df[df["Date"] == filter_day.isoformat()].reset_index(drop=True)
        else:
            df_day = df

        if df_day.empty:
            st.info("No events for this date. Add one from the left panel.")
        else:
            # Pretty agenda list
            for i, row in df_day.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['Time']} — {row['Title']}**")
                    st.write(f"⏳ {row['Duration(min)']} min")
                    if row["Notes"]:
                        st.caption(row["Notes"])

        st.write("---")
        st.subheader("All Events")
        if df.empty:
            st.info("No events yet.")
        else:
            st.dataframe(df, use_container_width=True)

            # Download CSV
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download Events CSV",
                data=csv,
                file_name="events.csv",
                mime="text/csv",
                use_container_width=True
            )

            # Delete event by index
            st.write("Delete an event")
            idx = st.number_input(
                "Enter row number to delete (from All Events table)",
                min_value=0,
                max_value=max(len(df) - 1, 0),
                value=0,
                step=1
            )
            del_btn = st.button("🗑️ Delete Selected Row", use_container_width=True)
            if del_btn:
                # rebuild list by sorting with SortDT again
                # easiest: recreate full list from current df excluding idx
                df2 = df.drop(index=int(idx)).reset_index(drop=True)

                # rebuild session_state.events
                rebuilt = []
                for _, r in df2.iterrows():
                    dt = datetime.fromisoformat(r["Date"] + "T" + r["Time"] + ":00")
                    rebuilt.append({
                        "Title": r["Title"],
                        "Date": r["Date"],
                        "Time": r["Time"],
                        "Duration(min)": int(r["Duration(min)"]),
                        "Notes": r["Notes"],
                        "SortDT": dt
                    })
                st.session_state.events = rebuilt
                st.success("Deleted!")

# =========================================================
# TAB 2: Prediction
# =========================================================
with tab2:
    st.subheader("Predict Tomorrow’s Productivity (0–100)")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        sleep_hours = st.slider("😴 Sleep (hours)", 0.0, 10.0, 7.0, 0.5)
    with c2:
        focus_hours = st.slider("🎯 Focus time (hours)", 0.0, 10.0, 4.0, 0.5)
    with c3:
        workload = st.slider("📚 Workload (1–5)", 1, 5, 3, 1)
    with c4:
        exercise = st.slider("🏃 Exercise (minutes)", 0, 120, 20, 5)

    if st.button("🔮 Predict Score", use_container_width=True):
        score = predict_productivity(sleep_hours, focus_hours, workload, exercise)

        st.metric("Predicted Productivity Score", f"{score}/100")
        st.progress(score / 100)

        if score >= 80:
            st.success("Excellent! Tomorrow looks highly productive ✅")
        elif score >= 60:
            st.warning("Good, but can be improved 💡")
        else:
            st.error("High risk of low productivity ❌ Try improving sleep/focus/exercise.")

        st.write("### Quick Suggestions")
        tips = []
        if sleep_hours < 6.5:
            tips.append("Sleep at least 7 hours.")
        if focus_hours < 3:
            tips.append("Plan 1–2 deep work blocks (45–60 mins).")
        if workload > 3:
            tips.append("Reduce tasks: pick top 3 priorities only.")
        if exercise < 15:
            tips.append("Add 15–20 mins walk or workout.")
        if not tips:
            tips.append("Keep the same routine. You’re on track!")

        for t in tips:
            st.write("•", t)

st.caption("✅ Tip: Edit this app text/title and push to GitHub — Jenkins will redeploy automatically.")
