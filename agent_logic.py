import os
import json

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIError
import ollama

from tools import (
    create_reminder,
    get_activity_history,
    get_bus_booking_history,
    analyze_user_routine,
    compare_user_daily_routine,
    generate_routine_suggestion,
    generate_routine_action,
    search_bus_options,
    select_bus,
    book_bus,
    search_routine_memory,
    calculate_expression,
    create_calendar_event,
    get_calendar_events,
    get_weather,
    convert_currency,
    search_places,
    web_search,
    get_available_tools
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

# ============================================================
# OPENAI CLIENT
# ============================================================

openai_api_key = os.getenv("OPENAI_API_KEY")

client = (
    OpenAI(api_key=openai_api_key)
    if openai_api_key
    else None
)


# ============================================================
# LAST BUS SEARCH CONTEXT
# ============================================================
# Stores the latest bus search result for each anonymous user.
#
# Example:
# {
#     "anonymous_user_id": {
#         "status": "success",
#         "source": "Bangalore",
#         "destination": "Hyderabad",
#         "travel_date": "25 September 2026",
#         "buses": [...]
#     }
# }
# ============================================================

last_bus_search = {}


# ============================================================
# SEMI-AGENTIC AI LOGIC
# ============================================================

def generate_suggestion(change_result):

    if change_result["status"] == "change_detected":

        previous_activity = change_result["previous_activity"]
        latest_activity = change_result["latest_activity"]

        return {
            "status": "suggestion",
            "message": (
                f"Your recent activity changed from "
                f"'{previous_activity}' to '{latest_activity}'. "
                "Would you like to continue your usual activity later "
                "or adjust your routine for today?"
            )
        }

    elif change_result["status"] == "no_change":

        return {
            "status": "normal",
            "message": (
                "Your recent activity looks consistent "
                "with your routine."
            )
        }

    else:

        return {
            "status": "not_enough_data",
            "message": (
                "I need more activity data before I can suggest "
                "a routine adjustment."
            )
        }


# ============================================================
# REMINDER REQUEST UNDERSTANDING
# ============================================================

def understand_reminder_request(user_message):
    if client is None:
        return False
    response = client.responses.create(
        model="gpt-5.6-luna",

        instructions=(
            "You extract reminder information from the user's message. "
            "Return ONLY valid JSON with exactly two fields: "
            "'task' and 'minutes'. "
            "'task' must be the reminder task. "
            "'minutes' must be an integer representing the number of "
            "minutes from now. "
            "Do not include any extra text."
        ),

        input=user_message
    )

    return json.loads(
        response.output_text
    )


# ============================================================
# EXECUTE CONFIRMED ACTION
# ============================================================

def execute_pending_action(
    user_id,
    pending_action
):

    action = pending_action["action"]

    # ========================================================
    # REMINDER ACTION
    # ========================================================

    if action == "create_reminder":

        task = pending_action["task"]

        minutes = int(
            pending_action["minutes"]
        )

        result = create_reminder(
            user_id,
            task,
            minutes
        )

        return {
            "status": "agent_action_completed",
            "message": result["message"]
        }


    # ========================================================
    # BUS BOOKING ACTION
    # ========================================================

    if action == "book_bus":

        result = book_bus(
            user_id,
            pending_action["source"],
            pending_action["destination"],
            pending_action["travel_date"],
            pending_action["bus_name"],
            pending_action["departure"],
            pending_action["bus_type"],
            pending_action["price"]
        )

        return {
            "status": "agent_action_completed",
            "message": result["message"]
        }


    # ========================================================
    # UNKNOWN ACTION
    # ========================================================

    return {
        "status": "error",
        "message": "Unknown pending action."
    }

def ollama_general_answer(user_message):
    response = ollama.chat(
        model="qwen3:8b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Anon Agent, a helpful AI assistant. "
                    "Answer the user's question clearly and accurately. "
                    "Keep the answer easy to understand."
                )
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )

    return response["message"]["content"]

def local_agent_fallback(user_message, user_id):

    """
    Local fallback agent.

    Handles common requests without requiring OpenAI API.
    Uses Ollama for general questions.
    """

    message = user_message.lower().strip()

    # ============================================================
    # REMINDER
    # ============================================================

    if "remind me" in message or "reminder" in message:

        import re

        minutes = None

        hour_match = re.search(
            r"in\s+(\d+)\s+(hour|hours)",
            message
        )

        minute_match = re.search(
            r"in\s+(\d+)\s+(minute|minutes)",
            message
        )

        if hour_match:
            minutes = int(hour_match.group(1)) * 60

        elif minute_match:
            minutes = int(minute_match.group(1))

        if minutes:

            task = message

            task = task.replace(
                "remind me to",
                ""
            )

            task = re.sub(
                r"in\s+\d+\s+(hour|hours|minute|minutes)",
                "",
                task
            )

            task = task.strip()

            return {
                "status": "confirmation_required",
                "message": (
                    f"🔔 I can create a reminder for "
                    f"'{task}' in {minutes} minutes. "
                    f"Would you like me to proceed?"
                ),
                "pending_action": {
                    "action": "create_reminder",
                    "task": task,
                    "minutes": minutes
                }
            }

        return {
            "status": "reminder_request",
            "message": (
                "⏰ Sure! Tell me what you want "
                "to be reminded about and when."
            )
        }

    # ============================================================
    # ACTIVITY HISTORY
    # ============================================================

    if any(word in message for word in [
        "activity history",
        "recent activities",
        "activities did i do",
        "what activities"
    ]):

        result = get_activity_history(
            user_id
        )

        return {
            "status": "activity_history",
            "message": result
        }

    # ============================================================
    # ROUTINE MEMORY / RAG
    # ============================================================

    if any(word in message for word in [
        "usually",
        "normally",
        "routine memory",
        "what do i usually",
        "what have i practiced"
    ]):

        result = search_routine_memory(
            user_message
        )

        return {
            "status": "rag",
            "message": result
        }

    # ============================================================
    # ROUTINE ANALYSIS
    # ============================================================

    if (
        "analyze my routine" in message
        or "analyse my routine" in message
        or "routine analysis" in message
    ):

        result = analyze_user_routine(
            user_id
        )

        return {
            "status": "routine_analysis",
            "message": result
        }

    # ============================================================
    # DAILY ROUTINE COMPARISON
    # ============================================================

    if (
        "compare today" in message
        or "today vs yesterday" in message
        or "compare my routine" in message
    ):

        result = compare_user_daily_routine(
            user_id
        )

        return {
            "status": "daily_comparison",
            "message": result
        }

    # ============================================================
    # BUS SEARCH
    # ============================================================

    if (
        "find buses" in message
        or "search buses" in message
        or "bus from" in message
        or "buses from" in message
    ):

        import re

        route_match = re.search(
            r"from\s+(.+?)\s+to\s+(.+?)\s+on\s+(\d{4}-\d{2}-\d{2})",
            user_message,
            re.IGNORECASE
        )

        if not route_match:

            return {
                "status": "bus_search",
                "message": (
                    "🚌 Please provide the route and date like: "
                    "Find buses from Bangalore to Hyderabad "
                    "on 2026-10-10"
                )
            }

        source = route_match.group(1).strip()

        destination = route_match.group(2).strip()

        travel_date = route_match.group(3).strip()

        result = search_bus_options(
            source,
            destination,
            travel_date
        )

        # Save latest bus search
        last_bus_search[user_id] = result

        return {
            "status": "bus_search",
            "message": result
        }

    # ============================================================
    # BUS SELECTION
    # ============================================================

    if (
        "select " in message
        or "choose " in message
    ) and any(bus_name in message for bus_name in [
        "express travels",
        "city travels",
        "night rider"
    ]):

        selected_bus = None

        if "express travels" in message:
            selected_bus = "Express Travels"

        elif "city travels" in message:
            selected_bus = "City Travels"

        elif "night rider" in message:
            selected_bus = "Night Rider"

        # --------------------------------------------------------
        # Check previous bus search
        # --------------------------------------------------------

        previous_search = last_bus_search.get(
            user_id
        )

        if not previous_search:

            return {
                "status": "bus_selection",
                "message": (
                    "🚌 Please search for buses first, "
                    "then select a bus."
                )
            }

        # --------------------------------------------------------
        # Get previous search information
        # --------------------------------------------------------

        source = previous_search.get(
            "source"
        )

        destination = previous_search.get(
            "destination"
        )

        travel_date = previous_search.get(
            "travel_date"
        )

        # --------------------------------------------------------
        # Find selected bus details
        # --------------------------------------------------------

        selected_details = None

        for bus in previous_search.get(
            "buses",
            []
        ):

            if bus.get("bus_name") == selected_bus:

                selected_details = bus
                break

        # --------------------------------------------------------
        # Bus not found
        # --------------------------------------------------------

        if not selected_details:

            return {
                "status": "bus_selection",
                "message": (
                    f"❌ {selected_bus} is not available "
                    "in the previous bus search."
                )
            }

        # --------------------------------------------------------
        # Select bus using tool
        # --------------------------------------------------------

        result = select_bus(
            source,
            destination,
            travel_date,
            selected_details["bus_name"],
            selected_details["departure"],
            selected_details["bus_type"],
            selected_details["price"]
        )

        # --------------------------------------------------------
        # Check selection result
        # --------------------------------------------------------

        if result["status"] != "bus_selected":

            return {
                "status": "bus_selection",
                "message": result["message"]
            }

        # --------------------------------------------------------
        # Ask user for confirmation
        # --------------------------------------------------------

        return {
            "status": "confirmation_required",

            "message": (
                f"🎫 You selected "
                f"{result['bus_name']} "
                f"departing at "
                f"{result['departure']}. "
                f"Bus type: "
                f"{result['bus_type']}. "
                f"Price: ₹{result['price']}. "
                "Would you like me to confirm this booking?"
            ),

            "pending_action": {
                "action": "book_bus",

                "source": result["source"],

                "destination": result["destination"],

                "travel_date": result["travel_date"],

                "bus_name": result["bus_name"],

                "departure": result["departure"],

                "bus_type": result["bus_type"],

                "price": result["price"]
            }
        }

    # ============================================================
    # BUS BOOKING HISTORY
    # ============================================================

    if (
        "bus booking history" in message
        or "my bus bookings" in message
        or "booked buses" in message
    ):

        result = get_bus_booking_history(
            user_id
        )

        return {
            "status": "bus_booking_history",
            "message": result
        }

    # ============================================================
    # CALCULATOR
    # ============================================================

    if any(op in message for op in [
        "calculate",
        "what is",
        "compute"
    ]) and any(op in user_message for op in [
        "+",
        "-",
        "*",
        "/",
        "%"
    ]):

        expression = (
            user_message.lower()
            .replace("calculate", "")
            .replace("compute", "")
            .replace("what is", "")
            .strip()
        )

        result = calculate_expression(
            expression
        )

        if result["status"] == "success":

            return {
                "status": "calculator",
                "message": (
                    f"🧮 {expression} = "
                    f"{result['result']}"
                )
            }

        return result

    # ============================================================
    # GET CALENDAR EVENTS
    # ============================================================

    if any(phrase in message for phrase in [
        "what events do i have",
        "what events do i have?",
        "show my events",
        "list my events",
        "show calendar",
        "my calendar",
        "upcoming events",
        "scheduled events",
        "calendar events"
    ]):

        result = get_calendar_events(
            user_id
        )

        return {
            "status": "calendar_events",
            "message": result["message"]
        }

    # ============================================================
    # CALENDAR EVENT
    # ============================================================

    if any(word in message for word in [
        "schedule",
        "calendar",
        "event",
        "meeting",
        "appointment"
    ]):

        import re

        # --------------------------------------------------------
        # Find date: YYYY-MM-DD
        # --------------------------------------------------------

        date_match = re.search(
            r"\b\d{4}-\d{2}-\d{2}\b",
            message
        )

        # --------------------------------------------------------
        # Find time: HH:MM
        # --------------------------------------------------------

        time_match = re.search(
            r"\b\d{1,2}:\d{2}\b",
            message
        )

        # --------------------------------------------------------
        # If date and time are available
        # --------------------------------------------------------

        if date_match and time_match:

            event_date = date_match.group()

            event_time = time_match.group()

            # ----------------------------------------------------
            # Extract event title
            # ----------------------------------------------------

            title = message

            for word in [
                "schedule",
                "calendar",
                "event",
                "meeting",
                "appointment",
                "on",
                "at"
            ]:

                title = title.replace(
                    word,
                    ""
                )

            # Remove date

            title = title.replace(
                event_date,
                ""
            )

            # Remove time

            title = title.replace(
                event_time,
                ""
            )

            title = title.strip()

            # Default title

            if not title:

                title = "Calendar Event"

            # ----------------------------------------------------
            # Save calendar event
            # ----------------------------------------------------

            result = create_calendar_event(
                user_id=user_id,
                title=title,
                event_date=event_date,
                event_time=event_time,
                description=""
            )

            return {
                "status": "calendar_created",
                "message": result["message"]
            }

        # --------------------------------------------------------
        # Date/time missing
        # --------------------------------------------------------

        return {
            "status": "calendar_request",
            "message": (
                "📅 Please provide the event title, "
                "date in YYYY-MM-DD format, and "
                "time in HH:MM format.\n\n"
                "Example:\n"
                "Schedule Python interview "
                "on 2026-10-01 at 10:00"
            )
        }
        
        # ============================================================
    # CURRENCY CONVERTER
    # ============================================================

    if (
        "convert" in message
        and any(currency in message for currency in [
            "usd",
            "inr",
            "eur",
            "gbp"
        ])
    ):

        import re

        currency_match = re.search(
            r"(\d+(?:\.\d+)?)\s*(usd|inr|eur|gbp)\s*(?:to|into)\s*(usd|inr|eur|gbp)",
            message,
            re.IGNORECASE
        )

        if not currency_match:

            return {
                "status": "currency_request",
                "message": (
                    "💱 Please provide the amount and currencies.\n\n"
                    "Example:\n"
                    "Convert 100 USD to INR"
                )
            }

        amount = float(
            currency_match.group(1)
        )

        from_currency = currency_match.group(2).upper()

        to_currency = currency_match.group(3).upper()

        result = convert_currency(
            amount,
            from_currency,
            to_currency
        )

        return {
            "status": "currency",
            "message": result["message"]
        }
        
        # ============================================================
    # PLACES SEARCH
    # ============================================================

    if any(word in message for word in [
        "find restaurants",
        "find restaurant",
        "restaurants in",
        "find hospitals",
        "find hospital",
        "hospitals in",
        "find hotels",
        "find hotel",
        "hotels in",
        "find cafes",
        "find cafe",
        "cafes in",
        "cafe in"
    ]):

        import re

        place_type = None

        if "restaurant" in message:
            place_type = "restaurant"

        elif "hospital" in message:
            place_type = "hospital"

        elif "hotel" in message:
            place_type = "hotel"

        elif "cafe" in message:
            place_type = "cafe"

        city_match = re.search(
            r"\b(?:in|near)\s+([a-zA-Z]+(?:\s+[a-zA-Z]+)?)",
            message,
            re.IGNORECASE
        )

        if not city_match:

            return {
                "status": "places_request",
                "message": (
                    "📍 Please mention a city.\n\n"
                    "Example:\n"
                    "Find restaurants in Bangalore"
                )
            }

        city = city_match.group(1).strip()

        result = search_places(
            place_type,
            city
        )

        return {
            "status": "places",
            "message": result["message"]
        }
        
        # ============================================================
    # WEB SEARCH
    # ============================================================

    if any(word in message for word in [
        "search the web",
        "search online",
        "web search",
        "search for",
        "latest news",
        "latest information"
    ]):

        query = user_message

        # Remove common command words
        for phrase in [
            "search the web for",
            "search online for",
            "web search for",
            "search for",
            "search online",
            "web search"
        ]:
            query = query.replace(
                phrase,
                "",
                1
            )

        query = query.strip()

        if not query:

            return {
                "status": "web_search_request",
                "message": (
                    "🔎 Please tell me what you want "
                    "to search for.\n\n"
                    "Example:\n"
                    "Search for latest AI news"
                )
            }

        result = web_search(
            query
        )

        return {
            "status": "web_search",
            "message": result["message"]
        }
    
    # ============================================================
    # WEATHER
    # ============================================================

    if any(word in message for word in [
        "weather",
        "temperature",
        "climate"
    ]):
        city = user_message.lower()
        for known_city in [
            "bangalore",
            "hyderabad",
            "chennai",
            "delhi",
            "mumbai"
        ]:
            if known_city in city:
                result = get_weather(
                    known_city.title()
                )
                return {
                    "status": "weather",
                    "message": result["message"]
                }
        return {
            "status": "weather",
            "message": "🌤️ Please mention a supported city."
        }

    # ============================================================
    # GENERAL AI ANSWER USING OLLAMA
    # ============================================================

    return {
        "status": "general",
        "message": ollama_general_answer(
            user_message
        )
    }
# ============================================================
# MULTI-STEP AGENTIC AI
# ============================================================

# ============================================================
# MULTI-STEP AGENTIC AI
# ============================================================

def run_agent(user_id, user_message):

    # ========================================================
    # CHECK FOR PREVIOUS BUS SEARCH
    # ========================================================

    previous_bus_context = last_bus_search.get(
        user_id
    )

    # ========================================================
    # BUILD USER INPUT
    # ========================================================

    input_items = []

    # --------------------------------------------------------
    # Previous bus search context
    # --------------------------------------------------------

    if previous_bus_context:

        input_items.append(
            {
                "role": "user",
                "content": (
                    "Previous bus search context:\n"
                    + json.dumps(
                        previous_bus_context,
                        indent=2
                    )
                    + "\n\n"
                    "Use this information if the user is "
                    "selecting one of the buses from this search."
                )
            }
        )

    # --------------------------------------------------------
    # Current user message
    # --------------------------------------------------------

    input_items.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    # ========================================================
    # DETECT WHETHER USER IS ASKING FOR A REMINDER
    # ========================================================

    is_reminder_request = (
        "remind me" in user_message.lower()
        or "set a reminder" in user_message.lower()
        or "create a reminder" in user_message.lower()
    )

    # ========================================================
    # ALLOW MULTIPLE TOOL STEPS
    # ========================================================

    for step in range(5):

        # ====================================================
        # AGENT INSTRUCTIONS
        # ====================================================

        instructions = (

            "You are the Agentic AI of AnonSense AI. "

            "Understand the user's goal and use the available "
            "tools when necessary. "

            # ------------------------------------------------
            # REMINDER
            # ------------------------------------------------

            "Use create_reminder when the user asks for a reminder. "

            "Before creating a reminder, the application will ask "
            "the user for confirmation. "

            "Never execute the reminder directly. "

            # ------------------------------------------------
            # ACTIVITY HISTORY
            # ------------------------------------------------

            "Use get_activity_history when the user asks to see "
            "or review their activity history. "

            # ------------------------------------------------
            # RAG
            # ------------------------------------------------

            "Use search_routine_memory when the user asks about "
            "their usual activities, previous routine, historical "
            "activity patterns, or what they usually practice. "

            # ------------------------------------------------
            # BUS HISTORY
            # ------------------------------------------------

            "Use get_bus_booking_history when the user asks "
            "to see, review, or check their previous bus bookings. "

            # ------------------------------------------------
            # ROUTINE ANALYSIS
            # ------------------------------------------------

            "Use analyze_user_routine when the user asks to analyze, "
            "understand, or summarize their routine. "

            # ------------------------------------------------
            # DAILY COMPARISON
            # ------------------------------------------------

            "You can use compare_user_daily_routine when the user asks "
            "to compare today's routine with yesterday's routine. "

            # ------------------------------------------------
            # ROUTINE SUGGESTION
            # ------------------------------------------------

            "Use generate_routine_suggestion when the user's routine "
            "differs from yesterday and the user wants a specific "
            "suggestion or reminder for a missing routine activity. "

            # ------------------------------------------------
            # ROUTINE ACTION
            # ------------------------------------------------

            "Use generate_routine_action when the user wants the "
            "system to suggest an action based on a routine change. "

            # ------------------------------------------------
            # BUS SEARCH
            # ------------------------------------------------

            "Use search_bus_options when the user asks to find, "
            "search, or check buses between a source and destination "
            "for a specific travel date. "

            # ------------------------------------------------
            # BUS SELECTION
            # ------------------------------------------------

            "When the user selects a bus such as "
            "Express Travels, City Travels, or Night Rider, "
            "check the previous bus search context first. "

            "If previous bus search context is available, "
            "use its source, destination, travel date, and "
            "the selected bus details. "

            "Do not ask the user again for source, destination, "
            "travel date, departure time, bus type, or price "
            "when those details are already available in the "
            "previous bus search context. "

            "Use select_bus with all required details from the "
            "previous bus search context. "

            "The selected bus must be one of the buses returned "
            "by the previous search. "

            # ------------------------------------------------
            # BUS BOOKING
            # ------------------------------------------------

            "When select_bus identifies the user's selected bus, "
            "the application will ask for confirmation before "
            "creating the booking. "

            "Never directly complete a bus booking without "
            "user confirmation. "

            # ------------------------------------------------
            # CALENDAR
            # ------------------------------------------------

            "Use create_calendar_event when the user asks to "
            "schedule a meeting, appointment, interview, event, "
            "or any calendar event. "

            "The calendar event should contain a title, date, "
            "time, and optional description. "

            "Use get_calendar_events when the user asks to "
            "see, list, check, or review their saved calendar "
            "events or upcoming events. "

            # ------------------------------------------------
            # CALCULATOR
            # ------------------------------------------------

            "Use calculate_expression when the user asks to "
            "calculate a mathematical expression, including "
            "addition, subtraction, multiplication, division, "
            "percentages, or parentheses. "

            # ------------------------------------------------
            # MULTI-STEP
            # ------------------------------------------------

            "You can use multiple tools in sequence when needed. "

            "For example, you may analyze the user's routine first "
            "and then request confirmation before creating a reminder. "

            "For bus travel, you may first search buses and then "
            "select a bus from the search result. "

            "After completing the required actions, provide a "
            "clear final response to the user."
        )

        # ====================================================
        # OPENAI RESPONSE
        # ====================================================

        try:

            # ------------------------------------------------
            # OpenAI unavailable → use local fallback
            # ------------------------------------------------

            if client is None:

                return local_agent_fallback(
                    user_message,
                    user_id
                )

            response = client.responses.create(

                model="gpt-5.6-luna",

                instructions=instructions,

                input=input_items,

                tools=get_available_tools(),

                # ------------------------------------------------
                # Force reminder tool when request is a reminder
                # ------------------------------------------------

                tool_choice=(
                    {
                        "type": "function",
                        "name": "create_reminder"
                    }
                    if is_reminder_request
                    else "auto"
                )
            )

        # ====================================================
        # OPENAI RATE LIMIT
        # ====================================================

        except RateLimitError:

            return local_agent_fallback(
                user_message,
                user_id
            )

        # ====================================================
        # OPENAI API ERROR
        # ====================================================

        except APIError as error:

            return {
                "status": "error",
                "message": (
                    "⚠️ An OpenAI API error occurred while "
                    f"running Agentic AI: {error}"
                )
            }

        # ====================================================
        # OTHER ERROR
        # ====================================================

        except Exception as error:

            return {
                "status": "error",
                "message": (
                    "⚠️ An unexpected error occurred while "
                    f"running Agentic AI: {error}"
                )
            }

        # ====================================================
        # ADD MODEL OUTPUT TO CONVERSATION
        # ====================================================

        input_items += response.output

        # ====================================================
        # TRACK WHETHER A TOOL WAS USED
        # ====================================================

        tool_was_used = False

        # ====================================================
        # PROCESS TOOL CALLS
        # ====================================================

        for item in response.output:

            if item.type != "function_call":
                continue

            tool_was_used = True

            # =================================================
            # TOOL 1: CREATE REMINDER
            # =================================================

            if item.name == "create_reminder":

                arguments = json.loads(
                    item.arguments
                )

                task = arguments["task"]

                minutes = int(
                    arguments["minutes"]
                )

                # ------------------------------------------------
                # Ask confirmation
                # ------------------------------------------------

                return {
                    "status": "confirmation_required",

                    "message": (
                        f"🔔 I can create a reminder for "
                        f"'{task}' in {minutes} minutes. "
                        "Would you like me to proceed?"
                    ),

                    "pending_action": {
                        "action": "create_reminder",
                        "task": task,
                        "minutes": minutes
                    }
                }

            # =================================================
            # TOOL 2: ACTIVITY HISTORY
            # =================================================

            elif item.name == "get_activity_history":

                result = get_activity_history(
                    user_id
                )

            # =================================================
            # TOOL 3: BUS BOOKING HISTORY
            # =================================================

            elif item.name == "get_bus_booking_history":

                result = get_bus_booking_history(
                    user_id
                )

            # =================================================
            # TOOL 4: ROUTINE ANALYSIS
            # =================================================

            elif item.name == "analyze_user_routine":

                result = analyze_user_routine(
                    user_id
                )

            # =================================================
            # TOOL 5: DAILY ROUTINE COMPARISON
            # =================================================

            elif item.name == "compare_user_daily_routine":

                result = compare_user_daily_routine(
                    user_id
                )

            # =================================================
            # TOOL 6: ROUTINE MEMORY / RAG
            # =================================================

            elif item.name == "search_routine_memory":

                arguments = json.loads(
                    item.arguments
                )

                query = arguments.get(
                    "query",
                    user_message
                )

                result = search_routine_memory(
                    query
                )

            # =================================================
            # TOOL 7: ROUTINE SUGGESTION
            # =================================================

            elif item.name == "generate_routine_suggestion":

                result = generate_routine_suggestion(
                    user_id
                )

            # =================================================
            # TOOL 8: ROUTINE ACTION
            # =================================================

            elif item.name == "generate_routine_action":

                result = generate_routine_action(
                    user_id
                )

            # =================================================
            # TOOL 9: BUS SEARCH
            # =================================================

            elif item.name == "search_bus_options":

                arguments = json.loads(
                    item.arguments
                )

                result = search_bus_options(
                    arguments["source"],
                    arguments["destination"],
                    arguments["travel_date"]
                )

                # ------------------------------------------------
                # Save latest bus search
                # ------------------------------------------------

                last_bus_search[user_id] = result

            # =================================================
            # TOOL 10: BUS SELECTION
            # =================================================

            elif item.name == "select_bus":

                arguments = json.loads(
                    item.arguments
                )

                # ------------------------------------------------
                # Get previous bus search information
                # ------------------------------------------------

                previous_search = last_bus_search.get(
                    user_id
                )

                # ------------------------------------------------
                # Use previous search context
                # ------------------------------------------------

                if previous_search:

                    source = previous_search.get(
                        "source",
                        arguments["source"]
                    )

                    destination = previous_search.get(
                        "destination",
                        arguments["destination"]
                    )

                    travel_date = previous_search.get(
                        "travel_date",
                        arguments["travel_date"]
                    )

                else:

                    source = arguments["source"]

                    destination = arguments["destination"]

                    travel_date = arguments["travel_date"]

                # ------------------------------------------------
                # Select bus
                # ------------------------------------------------

                result = select_bus(

                    source,

                    destination,

                    travel_date,

                    arguments["bus_name"],

                    arguments["departure"],

                    arguments["bus_type"],

                    arguments["price"]
                )

                # ------------------------------------------------
                # Check selection
                # ------------------------------------------------

                if result["status"] != "bus_selected":

                    return {
                        "status": "agent_action_completed",
                        "message": result["message"]
                    }

                # ------------------------------------------------
                # Ask confirmation
                # ------------------------------------------------

                return {

                    "status": "confirmation_required",

                    "message": (
                        f"🎫 You selected "
                        f"{result['bus_name']} "
                        f"departing at "
                        f"{result['departure']}. "
                        f"Bus type: "
                        f"{result['bus_type']}. "
                        f"Price: ₹{result['price']}. "
                        "Would you like me to confirm this booking?"
                    ),

                    "pending_action": {

                        "action": "book_bus",

                        "source": result["source"],

                        "destination": result["destination"],

                        "travel_date": result["travel_date"],

                        "bus_name": result["bus_name"],

                        "departure": result["departure"],

                        "bus_type": result["bus_type"],

                        "price": result["price"]
                    }
                }

            # =================================================
            # TOOL 11: BUS BOOKING
            # =================================================

            elif item.name == "book_bus":

                arguments = json.loads(
                    item.arguments
                )

                return {

                    "status": "confirmation_required",

                    "message": (
                        f"🎫 You selected "
                        f"{arguments['bus_name']} "
                        f"at {arguments['departure']} "
                        f"for ₹{arguments['price']}. "
                        "Would you like me to confirm this booking?"
                    ),

                    "pending_action": {

                        "action": "book_bus",

                        "source": arguments["source"],

                        "destination": arguments["destination"],

                        "travel_date": arguments["travel_date"],

                        "bus_name": arguments["bus_name"],

                        "departure": arguments["departure"],

                        "bus_type": arguments["bus_type"],

                        "price": arguments["price"]
                    }
                }

            # =================================================
            # TOOL 12: CALCULATOR
            # =================================================

            elif item.name == "calculate_expression":

                arguments = json.loads(
                    item.arguments
                )

                result = calculate_expression(
                    arguments["expression"]
                )

            # =================================================
            # TOOL 13: GET CALENDAR EVENTS
            # =================================================

            elif item.name == "get_calendar_events":

                result = get_calendar_events(
                    user_id
                )

            # =================================================
            # TOOL 14: CREATE CALENDAR EVENT
            # =================================================

            elif item.name == "create_calendar_event":

                arguments = json.loads(
                    item.arguments
                )

                result = create_calendar_event(

                    user_id=user_id,

                    title=arguments["title"],

                    event_date=arguments["event_date"],

                    event_time=arguments["event_time"],

                    description=arguments.get(
                        "description",
                        ""
                    )
                )

            # =================================================
            # UNKNOWN TOOL
            # =================================================

            else:

                result = {
                    "status": "error",
                    "message": "Unknown tool requested."
                }

            # =================================================
            # SEND TOOL RESULT BACK TO AI
            # =================================================

            input_items.append(
                {
                    "type": "function_call_output",

                    "call_id": item.call_id,

                    "output": json.dumps(
                        result
                    )
                }
            )

        # ====================================================
        # NO MORE TOOLS NEEDED
        # ====================================================

        if not tool_was_used:

            return {
                "status": "agent_action_completed",
                "message": response.output_text
            }

    # ========================================================
    # SAFETY STOP
    # ========================================================

    return {
        "status": "agent_action_completed",

        "message": (
            "I completed the available actions, "
            "but stopped after several steps."
        )
    }