from database import save_reminder
from datetime import datetime, timedelta

from rag.rag_engine import generate_rag_response
# ============================================================
# CREATE REMINDER
# ============================================================

def create_reminder(user_id, task, minutes):

    reminder_time = datetime.now() + timedelta(minutes=minutes)

    save_reminder(
        user_id,
        task,
        reminder_time.strftime("%Y-%m-%d %H:%M:%S")
    )

    return {
        "status": "success",
        "task": task,
        "reminder_time": reminder_time.strftime("%Y-%m-%d %H:%M:%S"),
        "message": (
            f"Reminder created for '{task}' "
            f"at {reminder_time.strftime('%H:%M:%S')}."
        )
    }
# ============================================================
# CREATE CALENDAR EVENT
# ============================================================

def create_calendar_event(
    user_id,
    title,
    event_date,
    event_time,
    description=""
):

    import sqlite3

    conn = sqlite3.connect("anonsense.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO calendar_events
        (
            user_id,
            title,
            event_date,
            event_time,
            description
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            title,
            event_date,
            event_time,
            description
        )
    )

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "title": title,
        "event_date": event_date,
        "event_time": event_time,
        "description": description,
        "message": (
            f"📅 Calendar event '{title}' "
            f"scheduled for {event_date} at {event_time}."
        )
    }
# ============================================================
# GET CALENDAR EVENTS
# ============================================================

def get_calendar_events(user_id):

    import sqlite3

    conn = sqlite3.connect("anonsense.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            title,
            event_date,
            event_time,
            description
        FROM calendar_events
        WHERE user_id = ?
        ORDER BY event_date ASC, event_time ASC
        """,
        (user_id,)
    )

    events = cursor.fetchall()

    conn.close()

    if not events:
        return {
            "status": "no_events",
            "message": "📅 You don't have any calendar events yet."
        }

    event_list = []

    for title, event_date, event_time, description in events:

        event_text = (
            f"📅 {title} — "
            f"{event_date} at {event_time}"
        )

        if description:
            event_text += f" — {description}"

        event_list.append(event_text)

    return {
        "status": "success",
        "events": events,
        "message": "\n".join(event_list)
    }
# ============================================================
# GET ACTIVITY HISTORY
# ============================================================

def get_activity_history(user_id):

    from database import get_user_activities

    activities = get_user_activities(user_id)

    if not activities:

        return {
            "status": "no_data",
            "message": "No activity history found."
        }

    history = []

    for activity, timestamp in activities:

        history.append(
            f"{activity} — {timestamp}"
        )

    return {
        "status": "success",
        "activities": history
    }


# ============================================================
# GET BUS BOOKING HISTORY
# ============================================================

def get_bus_booking_history(user_id):

    from database import get_bus_bookings

    bookings = get_bus_bookings(user_id)

    if not bookings:
        return {
            "status": "no_data",
            "message": "No bus bookings found."
        }

    history = []

    for booking in bookings:

        (
            source,
            destination,
            travel_date,
            bus_name,
            departure,
            bus_type,
            price,
            booking_status,
            created_at
        ) = booking

        history.append({
            "source": source,
            "destination": destination,
            "travel_date": travel_date,
            "bus_name": bus_name,
            "departure": departure,
            "bus_type": bus_type,
            "price": price,
            "booking_status": booking_status,
            "created_at": created_at
        })

    return {
        "status": "success",
        "bookings": history
    }

# ============================================================
# ANALYZE USER ROUTINE
# ============================================================

def analyze_user_routine(user_id):

    from database import get_recent_activities
    from routine_analysis import analyze_routine

    activities = get_recent_activities(
        user_id,
        limit=10
    )

    result = analyze_routine(activities)

    if result["status"] != "success":

        return {
            "status": result["status"],
            "message": result["message"]
        }

    return {
        "status": "success",
        "total_activities": result["total_activities"],
        "most_common_activity": result["most_common_activity"],
        "activity_counts": result["activity_counts"]
    }


# ============================================================
# COMPARE USER DAILY ROUTINE
# ============================================================

def compare_user_daily_routine(user_id):

    from database import (
        get_today_activities,
        get_yesterday_activities
    )

    from routine_analysis import (
        compare_daily_routine
    )

    today_activities = get_today_activities(
        user_id
    )

    yesterday_activities = get_yesterday_activities(
        user_id
    )

    result = compare_daily_routine(
        today_activities,
        yesterday_activities
    )

    return result


# ============================================================
# GENERATE ROUTINE ACTION
# ============================================================

def generate_routine_action(user_id):

    result = compare_user_daily_routine(user_id)

    if result["status"] == "routine_deviation":

        return {
            "status": "action_suggested",
            "message": (
                "Your routine is different from yesterday. "
                "Would you like me to help you get back to your usual routine?"
            )
        }

    elif result["status"] == "no_deviation":

        return {
            "status": "normal",
            "message": (
                "Your routine is similar to yesterday. "
                "No adjustment is needed."
            )
        }

    else:

        return {
            "status": result["status"],
            "message": result["message"]
        }


# ============================================================
# GENERATE ROUTINE SUGGESTION
# ============================================================

def generate_routine_suggestion(user_id):

    result = compare_user_daily_routine(user_id)

    if result["status"] == "routine_deviation":

        missing_today = result.get(
            "missing_today",
            []
        )

        if missing_today:

            activity = missing_today[0]

            return {
                "status": "suggestion",
                "activity": activity,
                "message": (
                    f"You usually do '{activity}', "
                    f"but it has not been recorded today. "
                    "Would you like me to set a reminder for this activity? "
                    "If yes, tell me when you want the reminder."
                )
            }

    if result["status"] == "no_deviation":

        return {
            "status": "normal",
            "message": (
                "Your routine looks similar to yesterday."
            )
        }

    return {
        "status": "no_suggestion",
        "message": (
            "There is not enough routine information "
            "to generate a suggestion."
        )
    }


# ============================================================
# GET AVAILABLE TOOLS
# ============================================================

def get_available_tools():

    return [

        # ========================================================
        # Tool 1: Create Reminder
        # ========================================================

        {
            "type": "function",
            "name": "create_reminder",
            "description": "Create a reminder for the user.",
            "parameters": {
                "type": "object",
                "properties": {

                    "task": {
                        "type": "string",
                        "description": (
                            "What the user wants to be reminded about."
                        )
                    },

                    "minutes": {
                        "type": "integer",
                        "description": (
                            "Number of minutes from now."
                        )
                    }
                },

                "required": [
                    "task",
                    "minutes"
                ],

                "additionalProperties": False
            },

            "strict": True
        },
        # ============================================================
# CALCULATOR TOOL
# ============================================================

{
    "type": "function",
    "name": "calculate_expression",
    "description": (
        "Calculate basic mathematical expressions such as "
        "addition, subtraction, multiplication, division, "
        "percentages, and parentheses."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": (
                    "A basic mathematical expression to calculate. "
                    "Example: 25 * 48"
                )
            }
        },
        "required": ["expression"],
        "additionalProperties": False
    },
    "strict": True
},
        
        
      


        # ========================================================
        # Tool 2: Activity History
        # ========================================================
        {
    "type": "function",
    "name": "create_calendar_event",
    "description": (
        "Create and save a calendar event for the user "
        "with a title, date, time, and optional description."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title or name of the calendar event."
            },
            "event_date": {
                "type": "string",
                "description": (
                    "Event date in YYYY-MM-DD format."
                )
            },
            "event_time": {
                "type": "string",
                "description": (
                    "Event time in HH:MM format."
                )
            },
            "description": {
                "type": "string",
                "description": (
                    "Optional description or notes for the event."
                )
            }
        },
        "required": [
            "title",
            "event_date",
            "event_time",
            "description"
        ],
        "additionalProperties": False
    },
    "strict": True
},
        
{
    "type": "function",
    "name": "get_calendar_events",
    "description": (
        "Get the user's saved calendar events. "
        "Use this when the user asks about upcoming, "
        "scheduled, or saved calendar events."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False
    },
    "strict": True
},
        {
            "type": "function",
            "name": "get_activity_history",
            "description": (
                "Get the user's activity history."
            ),

            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },

            "strict": True
        },
        
        # Tool: Bus Booking History
        {
            "type": "function",
            "name": "get_bus_booking_history",
            "description": (
                "Get the user's previous bus booking history."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },
            "strict": True
        },


        # ========================================================
        # Tool 3: Routine Analysis
        # ========================================================

        {
            "type": "function",
            "name": "analyze_user_routine",
            "description": (
                "Analyze the user's recent routine "
                "and identify the most common activity."
            ),

            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },

            "strict": True
        },


        # ========================================================
        # Tool 4: Daily Routine Comparison
        # ========================================================

        {
            "type": "function",
            "name": "compare_user_daily_routine",
            "description": (
                "Compare the user's activities today "
                "with yesterday and detect routine differences."
            ),

            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },

            "strict": True
        },


        # ========================================================
        # Tool 5: Routine Action
        # ========================================================

        {
            "type": "function",
            "name": "generate_routine_action",
            "description": (
                "Suggest an action when the user's routine "
                "has changed compared with yesterday."
            ),

            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },

            "strict": True
        },


        # ========================================================
        # Tool 6: Bus Search
        # ========================================================

        {
            "type": "function",
            "name": "search_bus_options",
            "description": (
                "Search for bus travel options between "
                "a source and destination on a given date."
            ),

            "parameters": {
                "type": "object",
                "properties": {

                    "source": {
                        "type": "string",
                        "description": (
                            "Starting city or location."
                        )
                    },

                    "destination": {
                        "type": "string",
                        "description": (
                            "Destination city or location."
                        )
                    },

                    "travel_date": {
                        "type": "string",
                        "description": (
                            "Date of travel."
                        )
                    }
                },

                "required": [
                    "source",
                    "destination",
                    "travel_date"
                ],

                "additionalProperties": False
            },

            "strict": True
        },


        # ========================================================
        # Tool 7: Select Bus
        # ========================================================

        {
            "type": "function",
            "name": "select_bus",

            "description": (
                "Select one of the available bus options "
                "chosen by the user. Use the source, destination, "
                "travel date, and selected bus details."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "source": {
                        "type": "string",
                        "description": (
                            "Starting city or location."
                        )
                    },

                    "destination": {
                        "type": "string",
                        "description": (
                            "Destination city or location."
                        )
                    },

                    "travel_date": {
                        "type": "string",
                        "description": (
                            "Date of travel."
                        )
                    },

                    "bus_name": {
                        "type": "string",
                        "description": (
                            "Name of the selected bus."
                        )
                    },

                    "departure": {
                        "type": "string",
                        "description": (
                            "Departure time of the selected bus."
                        )
                    },

                    "bus_type": {
                        "type": "string",
                        "description": (
                            "Type of bus, such as AC Sleeper "
                            "or Non-AC Sleeper."
                        )
                    },

                    "price": {
                        "type": "integer",
                        "description": (
                            "Ticket price of the selected bus."
                        )
                    }
                },

                "required": [
                    "source",
                    "destination",
                    "travel_date",
                    "bus_name",
                    "departure",
                    "bus_type",
                    "price"
                ],

                "additionalProperties": False
            },

            "strict": True
        },


        # ========================================================
        # Tool 8: Book Bus
        # ========================================================

        {
            "type": "function",
            "name": "book_bus",
            "description": (
                "Create a demo bus booking after the user "
                "has confirmed the selected bus."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "source": {
                        "type": "string"
                    },

                    "destination": {
                        "type": "string"
                    },

                    "travel_date": {
                        "type": "string"
                    },

                    "bus_name": {
                        "type": "string"
                    },

                    "departure": {
                        "type": "string"
                    },

                    "bus_type": {
                        "type": "string"
                    },

                    "price": {
                        "type": "integer"
                    }
                },

                "required": [
                    "source",
                    "destination",
                    "travel_date",
                    "bus_name",
                    "departure",
                    "bus_type",
                    "price"
                ],

                "additionalProperties": False
            },

            "strict": True
        },
        
        {
            "type": "function",
            "name": "search_routine_memory",
            "description": (
                "Search the user's historical routine and "
                "activity memory using RAG. Use this when "
                "the user asks about previous activities, "
                "usual routines, or historical patterns."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Question about the user's "
                            "historical routine or activities."
                        )
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            },
            "strict": True
        },



        # ========================================================
        # Tool 9: Routine Suggestion
        # ========================================================

        {
            "type": "function",
            "name": "generate_routine_suggestion",
            "description": (
                "Generate a proactive suggestion when the user's "
                "routine differs from yesterday."
            ),

            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            },

            "strict": True
        }
    ]


# ============================================================
# BUS SEARCH TOOL
# ============================================================

def search_bus_options(
    source,
    destination,
    travel_date
):

    bus_options = [

        {
            "bus_name": "Express Travels",
            "departure": "21:00",
            "bus_type": "AC Sleeper",
            "price": 850
        },

        {
            "bus_name": "City Travels",
            "departure": "22:30",
            "bus_type": "AC Sleeper",
            "price": 1050
        },

        {
            "bus_name": "Night Rider",
            "departure": "23:15",
            "bus_type": "Non-AC Sleeper",
            "price": 750
        }
    ]

    return {

        "status": "success",

        "source": source,

        "destination": destination,

        "travel_date": travel_date,

        "buses": bus_options
    }


# ============================================================
# BUS SELECTION TOOL
# ============================================================

def select_bus(
    source,
    destination,
    travel_date,
    bus_name,
    departure,
    bus_type,
    price
):

    bus_details = {

        "Express Travels": {
            "departure": "21:00",
            "bus_type": "AC Sleeper",
            "price": 850
        },

        "City Travels": {
            "departure": "22:30",
            "bus_type": "AC Sleeper",
            "price": 1050
        },

        "Night Rider": {
            "departure": "23:15",
            "bus_type": "Non-AC Sleeper",
            "price": 750
        }
    }

    if bus_name not in bus_details:

        return {
            "status": "not_found",
            "message": (
                f"Bus '{bus_name}' was not found "
                "in the available options."
            )
        }

    selected = bus_details[bus_name]

    return {

        "status": "bus_selected",

        "source": source,

        "destination": destination,

        "travel_date": travel_date,

        "bus_name": bus_name,

        "departure": selected["departure"],

        "bus_type": selected["bus_type"],

        "price": selected["price"],

        "message": (
            f"You selected {bus_name} "
            f"departing at {selected['departure']}. "
            f"Bus type: {selected['bus_type']}. "
            f"Price: ₹{selected['price']}."
        )
    }


# ============================================================
# BUS BOOKING TOOL
# ============================================================

def book_bus(
    user_id,
    source,
    destination,
    travel_date,
    bus_name,
    departure,
    bus_type,
    price
):

    from database import save_bus_booking

    save_bus_booking(
        user_id,
        source,
        destination,
        travel_date,
        bus_name,
        departure,
        bus_type,
        price
    )

    return {

        "status": "booking_confirmed",

        "message": (
            f"🎫 Bus booking confirmed for {bus_name}. "
            f"{source} → {destination} on {travel_date} "
            f"at {departure}. "
            f"Bus type: {bus_type}. "
            f"Ticket price: ₹{price}."
        )
    }
    
# ============================================================
# RAG ROUTINE MEMORY
# ============================================================

def search_routine_memory(query):

    """
    Search the user's historical routine using RAG.
    """

    return generate_rag_response(query)

# ============================================================
# CALCULATOR TOOL
# ============================================================

# ============================================================
# CALCULATOR TOOL
# ============================================================

def calculate_expression(expression):
    """
    Safely evaluate basic mathematical expressions.
    Supports normal calculations and percentages.
    """

    try:
        expression = expression.strip().lower().rstrip("?")

        # ----------------------------------------------------
        # Percentage calculations
        # Example: 15% of 850
        # ----------------------------------------------------
        if "%" in expression and "of" in expression:

            parts = expression.split("% of")

            percentage = float(parts[0].strip())
            number = float(parts[1].strip())

            result = (percentage / 100) * number

            return {
                "status": "success",
                "expression": expression,
                "result": result
            }

        # ----------------------------------------------------
        # Basic mathematical expressions
        # Example: 25 * 48
        # ----------------------------------------------------
        allowed_chars = set(
            "0123456789+-*/().% "
        )

        if not all(
            char in allowed_chars
            for char in expression
        ):
            return {
                "status": "error",
                "message": (
                    "❌ Only basic mathematical "
                    "expressions are supported."
                )
            }

        # ----------------------------------------------------
        # Calculate expression
        # ----------------------------------------------------
        result = eval(
            expression,
            {
                "__builtins__": {}
            },
            {}
        )

        return {
            "status": "success",
            "expression": expression,
            "result": result
        }

    except Exception:
        return {
            "status": "error",
            "message": (
                "❌ I couldn't calculate that expression."
            )
        }
        
def get_weather(city):
    """
    Get weather information for a city.
    """

    weather_data = {
        "Bangalore": "🌤️ 28°C, Partly Cloudy",
        "Hyderabad": "☀️ 30°C, Sunny",
        "Chennai": "🌤️ 31°C, Partly Cloudy",
        "Delhi": "☀️ 29°C, Sunny",
        "Mumbai": "🌧️ 27°C, Rainy"
    }

    city = city.strip().title()

    if city in weather_data:
        return {
            "status": "success",
            "city": city,
            "weather": weather_data[city],
            "message": f"🌤️ Weather in {city}: {weather_data[city]}"
        }

    return {
        "status": "error",
        "message": f"❌ Weather data is not available for {city}."
    }
    
def convert_currency(amount, from_currency, to_currency):
    """
    Convert currency using demo exchange rates.
    """

    rates = {
        "USD": 83.0,
        "EUR": 90.0,
        "GBP": 105.0,
        "INR": 1.0
    }

    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if from_currency not in rates or to_currency not in rates:
        return {
            "status": "error",
            "message": "❌ Supported currencies: USD, EUR, GBP, INR"
        }

    amount_in_inr = amount * rates[from_currency]
    converted_amount = amount_in_inr / rates[to_currency]

    return {
        "status": "success",
        "message": (
            f"💱 {amount} {from_currency} = "
            f"{converted_amount:.2f} {to_currency}"
        )
    }
    
def search_places(place_type, city):
    """
    Demo places search tool.
    """

    places = {
        "restaurant": [
            "🍽️ Paradise Restaurant",
            "🍽️ Meghana Foods",
            "🍽️ Absolute Barbecues"
        ],
        "hospital": [
            "🏥 Apollo Hospital",
            "🏥 Manipal Hospital",
            "🏥 Fortis Hospital"
        ],
        "hotel": [
            "🏨 Taj Hotel",
            "🏨 ITC Hotel",
            "🏨 Marriott Hotel"
        ],
        "cafe": [
            "☕ Starbucks",
            "☕ Third Wave Coffee",
            "☕ Cafe Coffee Day"
        ]
    }

    place_type = place_type.lower().strip()
    city = city.strip().title()

    if place_type not in places:
        return {
            "status": "error",
            "message": (
                "❌ Supported places: "
                "restaurant, hospital, hotel, cafe"
            )
        }

    results = "\n".join(
        f"{i + 1}. {place}"
        for i, place in enumerate(places[place_type])
    )

    return {
        "status": "success",
        "message": (
            f"📍 {place_type.title()}s in {city}:\n\n"
            f"{results}"
        )
    }
    
def web_search(query):
    """
    Search the web using DuckDuckGo.
    """

    from ddgs import DDGS

    try:
        results = DDGS().text(
            query,
            max_results=5
        )

        if not results:
            return {
                "status": "error",
                "message": "❌ No search results found."
            }

        output = "🔎 Web Search Results:\n\n"

        for i, result in enumerate(results, start=1):

            title = result.get(
                "title",
                "No title"
            )

            body = result.get(
                "body",
                "No description"
            )

            url = result.get(
                "href",
                ""
            )

            output += (
                f"{i}. {title}\n"
                f"{body}\n"
                f"{url}\n\n"
            )

        return {
            "status": "success",
            "message": output
        }

    except Exception as e:

        return {
            "status": "error",
            "message": f"❌ Web search failed: {str(e)}"
        }