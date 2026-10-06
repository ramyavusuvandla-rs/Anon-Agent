# ============================================================
# BASIC ROUTINE ANALYSIS
# ============================================================

def analyze_routine(activities):

    if not activities:

        return {
            "status": "no_data",
            "message": "Not enough activity data to analyze."
        }


    activity_names = [
        normalize_activity(activity[0])
        for activity in activities
    ]


    activity_counts = {}


    for activity in activity_names:

        activity_counts[activity] = (
            activity_counts.get(activity, 0) + 1
        )


    most_common_activity = max(
        activity_counts,
        key=activity_counts.get
    )


    return {
        "status": "success",
        "total_activities": len(activity_names),
        "most_common_activity": most_common_activity,
        "activity_counts": activity_counts
    }


# ============================================================
# RECENT ROUTINE CHANGE DETECTION
# ============================================================

def detect_routine_change(activities):

    if len(activities) < 2:

        return {
            "status": "not_enough_data",
            "message": (
                "Not enough activity data to detect "
                "a routine change."
            )
        }


    latest_activity = activities[0][0]

    previous_activity = activities[1][0]


    if latest_activity != previous_activity:

        return {
            "status": "change_detected",
            "previous_activity": previous_activity,
            "latest_activity": latest_activity,
            "message": (
                f"Your recent activity changed from "
                f"'{previous_activity}' to "
                f"'{latest_activity}'."
            )
        }


    return {
        "status": "no_change",
        "previous_activity": previous_activity,
        "latest_activity": latest_activity,
        "message": (
            "Your recent activity looks consistent "
            "with your routine."
        )
    }


# ============================================================
# DAILY ROUTINE COMPARISON
# ============================================================

def compare_daily_routine(
    today_activities,
    yesterday_activities
):

    # --------------------------------------------------------
    # No data for either day
    # --------------------------------------------------------

    if not today_activities and not yesterday_activities:

        return {
            "status": "no_data",
            "message": (
                "There is not enough activity data "
                "to compare your daily routine."
            )
        }


    # --------------------------------------------------------
    # Yesterday exists but today has no activity
    # --------------------------------------------------------

    if yesterday_activities and not today_activities:

        yesterday_names = [
            activity[0]
            for activity in yesterday_activities
        ]


        return {
            "status": "routine_deviation",
            "message": (
                "No activities have been recorded today, "
                "while activities were recorded yesterday."
            ),
            "yesterday_activities": yesterday_names,
            "today_activities": []
        }


    # --------------------------------------------------------
    # Today exists but yesterday has no activity
    # --------------------------------------------------------

    if today_activities and not yesterday_activities:

        today_names = [
            activity[0]
            for activity in today_activities
        ]


        return {
            "status": "not_enough_comparison_data",
            "message": (
                "Today's activities are available, "
                "but there is no activity data from yesterday "
                "for comparison."
            ),
            "today_activities": today_names,
            "yesterday_activities": []
        }


    # --------------------------------------------------------
    # Extract activity names
    # --------------------------------------------------------

    today_names = [
        normalize_activity(activity[0])
        for activity in today_activities
    ]


    yesterday_names = [
        normalize_activity(activity[0])
        for activity in yesterday_activities
    ]


    # --------------------------------------------------------
    # Convert to sets for comparison
    # --------------------------------------------------------

    today_set = set(today_names)

    yesterday_set = set(yesterday_names)


    # Activities missing today
    missing_today = list(
        yesterday_set - today_set
    )


    # New activities today
    new_today = list(
        today_set - yesterday_set
    )


    # --------------------------------------------------------
    # Detect routine deviation
    # --------------------------------------------------------

    if missing_today or new_today:

        return {
            "status": "routine_deviation",

            "message": (
                "Your activity pattern today is different "
                "from yesterday."
            ),

            "today_activities": today_names,

            "yesterday_activities": yesterday_names,

            "missing_today": missing_today,

            "new_today": new_today
        }


    # --------------------------------------------------------
    # No major difference
    # --------------------------------------------------------

    return {
        "status": "no_deviation",

        "message": (
            "Your activity pattern today is similar "
            "to yesterday."
        ),

        "today_activities": today_names,

        "yesterday_activities": yesterday_names,

        "missing_today": [],

        "new_today": []
    }
    
# ============================================================
# ACTIVITY NORMALIZATION
# ============================================================

def normalize_activity(activity):

    text = activity.lower().strip()

    if "python" in text:
        return "Python"

    if "sql" in text:
        return "SQL"

    if "exercise" in text or "workout" in text or "gym" in text:
        return "Exercise"

    if "study" in text or "studied" in text:
        return "Study"

    if "sleep" in text or "slept" in text:
        return "Sleep"

    if "walk" in text or "walking" in text:
        return "Walking"

    return activity.strip()