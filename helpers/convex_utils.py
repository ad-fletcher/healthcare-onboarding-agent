import requests
import httpx
import logging
import time
from typing import Union, Dict, Any
import httpx, logging
from typing import Dict, Tuple

from .shared_types import CONVEX_LOG_URL, MySessionInfo # Import from the new types file
from .data import AGGREGATE_DATA # Import AGGREGATE_DATA
from livekit.agents import RunContext # Needed for update_interview_progress type hint

logger = logging.getLogger(__name__)

# --- Moved Functions --- 

def get_user_metadata(clerk_id: str) -> dict:
    url = f"{CONVEX_LOG_URL}/get-user-metadata"
    try:
        resp = requests.post(url, json={"clerk_id": clerk_id})
        if resp.status_code == 200:
            payload = resp.json().get("data", {})
            return {
                "user_id": payload.get("_id"),
                "name":    payload.get("fullName"),
                # keep the rest if you like:
                **{k: v for k, v in payload.items() 
                   if k not in ("_id", "fullName")}
            }
        else:
             # Log or handle non-200 status appropriately
             logger.error(f"Failed to get user metadata for clerk_id {clerk_id}. Status: {resp.status_code}, Body: {resp.text}")
             return {"status": "error", "error_message": f"Server responded with {resp.status_code}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error getting user metadata for clerk_id {clerk_id}: {e}")
        return {"status": "error", "error_message": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error getting user metadata for clerk_id {clerk_id}: {e}")
        return {"status": "error", "error_message": str(e)}

def render_visualization(field: str, user_value: Union[str, int, float], interview_id: str, user_id: str) -> dict:
    """
    Generate a bar chart visualization configuration based on aggregate data, then upload it to Convex.

    Args:
        field (str): The demographic or wellness field (e.g. "age", "financialStability").
        user_value (any): The user-provided value.
        interview_id (str): The session/ interview identifier.
        user_id (str): The user identifier (needed to log with convex).

    Returns:
        dict: Visualization configuration (and any log error if occurred).
    """
    # Check that the aggregate data exists for the field.
    if field not in AGGREGATE_DATA:
        logger.warning(f"No aggregate data for field '{field}' in render_visualization.")
        return {
            "status": "error",
            "message": f"No aggregate data available for field '{field}'."
        }
    
    data_entry = AGGREGATE_DATA[field]
    bars = []
    chart_title = f"{field.capitalize()} Distribution"
    
    # Process numeric fields using distributions.
    if "distribution" in data_entry:
        distribution = data_entry["distribution"]
        try:
            numeric_value = float(user_value)
        except (ValueError, TypeError):
            logger.warning(f"Could not convert user_value '{user_value}' to float for field '{field}' in render_visualization.")
            numeric_value = None

        for bin_item in distribution:
            is_user = False
            start = bin_item.get("start")
            end   = bin_item.get("end")
            
            if numeric_value is not None:
                if end is None:
                    if numeric_value >= start:
                        is_user = True
                elif start is not None: # Ensure start is not None before comparison
                    if start <= numeric_value <= end:
                        is_user = True
            
            # Use the percentage value from the bin (accepts either "percentage" or "pct").
            pct_value = bin_item.get("percentage") or bin_item.get("pct")
            if pct_value is None:
                 logger.warning(f"Missing percentage/pct for bin {bin_item.get('label')} in field '{field}' distribution.")
                 pct_value = 0 # Default to 0 if missing

            bars.append({
                "label": bin_item.get("label", "Unknown Label"), # Provide default label
                "value": pct_value,
                "isUserValue": is_user,
            })
    
    # Process enumerated fields using mapping.
    elif "mapping" in data_entry:
        mapping = data_entry["mapping"]
        normalized_user_value = str(user_value).lower().strip()
        for key, info in mapping.items():
            # A simple case-insensitive check, comparing normalized values.
            # Safely handle None labels before calling .lower()
            label = info.get("label")
            is_user = (
                normalized_user_value == key.lower().strip() or 
                (label is not None and normalized_user_value == label.lower().strip())
            )
            pct_value = info.get("pct")
            if pct_value is None:
                logger.warning(f"Missing pct for key '{key}' in field '{field}' mapping.")
                pct_value = 0 # Default to 0
            bars.append({
                "label": info.get("label", "Unknown Label"), # Provide default label
                "value": pct_value,
                "isUserValue": is_user,
            })
    
    else:
        logger.warning(f"Field '{field}' lacks distribution or mapping data in render_visualization.")
        return {
            "status": "error",
            "message": f"Field '{field}' lacks distribution or mapping data."
        }
    
    # Map field names to more readable formats for chart titles
    field_name_mapping = {
        'age': 'Age',
        'lifeStage': 'Life Stage', 
        'livingArrangement': 'Living Arrangement',
        'location': 'Location',
        'educationLevel': 'Education Level',
        'careerField': 'Career Field',
        'financialStability': 'Financial Stability',
        'socialConnection': 'Social Connection', 
        'healthConfidence': 'Health Confidence',
        'lifeSatisfaction': 'Life Satisfaction'
    }
    
    # Update chart title with mapped name if available
    chart_title = f"{field_name_mapping.get(field, field.capitalize())} Distribution"

    
    # Package the visualization configuration.
    visualization = {
        "userId": user_id,
        "interviewId": interview_id,
        "question": field,
        "chartTitle": chart_title,
        "chartType": "bar",
        "bars": bars,
        "userValue": str(user_value), # Ensure userValue is stringified
        "timestamp": int(time.time() * 1000)
    }
    
    # Now POST this configuration to your Convex endpoint.
    if not CONVEX_LOG_URL or "YOUR_CONVEX_URL" in CONVEX_LOG_URL:
         logger.error("Cannot log visualization: CONVEX_LOG_URL not set correctly.")
         visualization["logError"] = "CONVEX_LOG_URL not configured."
         return visualization
    
    try:
        log_url = f"{CONVEX_LOG_URL}/log-visualization"
        response = requests.post(log_url, json=visualization, timeout=10.0) # Added timeout
        if response.status_code != 200:
            error_text = f"Server responded with error: {response.status_code} - {response.text}"
            logger.error(f"Error logging visualization to {log_url}: {error_text}")
            visualization["logError"] = error_text
        else:
            logger.info(f"Successfully logged visualization for field '{field}' to {log_url}")
    except requests.exceptions.RequestException as e:
        error_text = f"Network error logging visualization: {e}"
        logger.error(error_text)
        visualization["logError"] = error_text
    except Exception as e:
        error_text = f"Unexpected error logging visualization: {e}"
        logger.error(error_text)
        visualization["logError"] = error_text
    
    return visualization

def contextual_analysis_tool(field: str, user_value: Union[str, int, float]) -> str:
    """
    Return a short feedback sentence comparing the user's value or category
    to the community distribution or average, using data from AGGREGATE_DATA.
    """
    if field not in AGGREGATE_DATA:
        logger.warning(f"No aggregate data for field '{field}' in contextual_analysis_tool.")
        return f"Sorry, no contextual data is available for {field}."

    data_entry = AGGREGATE_DATA[field]
    normalized_user_value_str = str(user_value).lower().strip()

    # Handle numeric fields (including those with averages/distributions)
    if field in ["age", "financialStability", "healthConfidence", "lifeSatisfaction"]:
        try:
            numeric_value = float(user_value)
        except (ValueError, TypeError):
            logger.warning(f"Expected numeric value for field '{field}', got '{user_value}' in contextual_analysis_tool.")
            return f"I expected a numeric value for {field}, but got '{user_value}'."

        avg = data_entry.get("average")
        dist = data_entry.get("distribution", [])
        response_parts = []

        # Comparison to average (if available)
        if avg is not None:
            if numeric_value < avg:
                response_parts.append(f"Your {field} of {numeric_value:.1f} is below the community average of {avg:.1f}.")
            elif numeric_value > avg:
                response_parts.append(f"Your {field} of {numeric_value:.1f} is above the community average of {avg:.1f}.")
            else:
                response_parts.append(f"Your {field} is exactly the community average of {avg:.1f}.")
        else:
             # Only state the value if no average comparison is possible
             response_parts.append(f"You reported {field} as {numeric_value:.1f}.") 

        # Find distribution bin (if available)
        if dist:
            matching_bin = None
            for b in dist:
                start = b.get("start")
                end = b.get("end")
                if start is None: continue # Skip bins without a start

                if end is None:  # Open-ended bin (e.g., 65+)
                    if numeric_value >= start:
                        matching_bin = b
                        break
                else: # Range bin
                    if start <= numeric_value <= end:
                        matching_bin = b
                        break
            
            if matching_bin:
                bin_label = matching_bin.get("label", "this range")
                bin_pct = matching_bin.get("percentage") or matching_bin.get("pct")
                if bin_pct is not None:
                    response_parts.append(f"About {bin_pct:.0f}% of the community reports a {field} in the range '{bin_label}'.")
                else:
                     logger.warning(f"Missing percentage/pct for bin '{bin_label}' in field '{field}' distribution.")
            # No else needed, if no bin matches, we just don't add that part
        
        return " ".join(response_parts)

    # Handle categorical fields using mapping
    elif "mapping" in data_entry:
        data_map = data_entry["mapping"]
        matched_info = None
        
        # Try matching normalized user input against keys or labels in the map
        for key, info in data_map.items():
            if normalized_user_value_str == key.lower().strip() or normalized_user_value_str == info.get("label","").lower().strip():
                matched_info = info
                break
        
        if matched_info:
            label = matched_info.get("label")
            pct = matched_info.get("pct")
            if label and pct is not None and pct > 0:
                # Special phrasing for some fields if needed
                if field == "educationLevel":
                    return f"About {pct:.0f}% of the community has '{label}' as their highest education level."
                elif field == "careerField":
                    return f"About {pct:.0f}% of our community works in '{label}'."
                # Default phrasing
                return f"Around {pct:.0f}% of our community also reports '{label}'." 
            elif label:
                # Handle cases where pct might be 0 or missing
                 logger.info(f"Distribution data (pct) is zero or missing for '{label}' in field '{field}'.")
                 return f"You mentioned '{label}'. We're still gathering data on how common this is."
            else:
                 # Fallback if label is missing in the matched info
                 logger.warning(f"Label missing for matched key in field '{field}' mapping.")
                 return f"You mentioned '{user_value}'."
        else:
            # User input didn't match any known category exactly
            logger.warning(f"User value '{user_value}' did not match any category in field '{field}'.")
            # Attempt fuzzy matching or provide generic feedback
            # (Fuzzy matching logic omitted for brevity, could be added here)
            return f"Thanks for sharing '{user_value}'. I couldn't find specific comparison data for that response in {field}."

    # Fallback if field type isn't handled
    logger.error(f"Contextual analysis not implemented for field '{field}' type.")
    return f"Sorry, I don't have comparison data available for the field '{field}'."

async def log_message_to_convex(interview_id: str | None, author: str, text: str):
    if not interview_id:
        logger.warning("Cannot log message to Convex: interview_id is missing.")
        return
    if not CONVEX_LOG_URL or "YOUR_CONVEX_URL" in CONVEX_LOG_URL:
        logger.error("Cannot log message to Convex: CONVEX_LOG_URL not set correctly.")
        return

    endpoint_path = "/addMessage" # Convex HTTP functions are usually at the root unless defined otherwise
    url = f"{CONVEX_LOG_URL}{endpoint_path}"

    payload = {
        "interviewId": interview_id,
        "author":      author,
        "text":        text,
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status() # Raises exception for 4xx/5xx responses
            logger.info(f"Logged to Convex: {author=} interview_id='{interview_id}' status={resp.status_code}")
    except httpx.HTTPStatusError as e:
        # Log the specific error response from Convex
        try:
            error_body = await e.response.aread()
        except Exception:
            error_body = b"(Could not read error body)"
        logger.error(f"HTTP {e.response.status_code} from Convex log endpoint {url}: {error_body.decode()}")
    except httpx.RequestError as e:
        logger.error(f"Network error logging to Convex ({url}): {e}")
    except Exception as e:
        logger.error(f"Unexpected error logging to Convex ({url}): {e}")


async def update_demographic_field(user_id: str, field: str, value: Any) -> Dict[str, Any]:
    """
    Async version: updates a user's demographic field in Convex.
    Handles potential errors during the request.
    """
    if not user_id:
        logger.error("update_demographic_field called with no user_id.")
        return {"status": "error", "error_message": "User ID is missing."}
        
    if not CONVEX_LOG_URL or "YOUR_CONVEX_URL" in CONVEX_LOG_URL:
        logger.error("Cannot update demographic: CONVEX_LOG_URL not set correctly.")
        return {"status": "error", "error_message": "CONVEX_LOG_URL not configured."}

    url = f"{CONVEX_LOG_URL}/update-demographic"
    payload = {
        "user_id": user_id,
        "field":   field,
        "value":   value # Send the original value
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=5.0)
            resp.raise_for_status() # Check for HTTP errors
            logger.info(f"Successfully updated demographic field '{field}' for user '{user_id}'.")
            # Return the response from the Convex function if needed, or just success status
            try:
                return {"status": "success", "data": resp.json()} 
            except ValueError:
                 return {"status": "success", "message": f"{field} updated, no JSON response body."} # Handle cases with no JSON response

        except httpx.RequestError as e:
            logger.warning(f"update_demographic_field network error to {url}: {e}")
            return {"status": "error", "error_message": f"Network error: {e}"}
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            try:
                error_text = await e.response.aread()
                error_text = error_text.decode()
            except Exception:
                 error_text = "(Could not read error body)"
            logger.warning(f"update_demographic_field HTTP {status_code} from {url}: {error_text}")
            return {"status": "error", "error_message": f"Server error ({status_code}): {error_text}"}
        except Exception as e:
             logger.error(f"Unexpected error in update_demographic_field: {e}")
             return {"status": "error", "error_message": f"Unexpected error: {e}"}


# ──────────────────────────────────────────────────────────────────────────
# 🔄  Generic HTTP helper (shared by Phases 2‑4)
# ──────────────────────────────────────────────────────────────────────────
async def _post_convex_update(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Low‑level POST to Convex. Returns {"status": "...", ...}.
    """
    if not payload.get("user_id"):
        logger.error(f"{endpoint} called with no user_id.")
        return {"status": "error", "error_message": "User ID is missing."}

    if not CONVEX_LOG_URL or "YOUR_CONVEX_URL" in CONVEX_LOG_URL:
        logger.error(f"Cannot hit {endpoint}: CONVEX_LOG_URL not set correctly.")
        return {"status": "error", "error_message": "CONVEX_LOG_URL not configured."}

    url = f"{CONVEX_LOG_URL}/{endpoint}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=5.0)
            resp.raise_for_status()
            logger.info(f"✅ {endpoint}: {payload['field']} saved for {payload['user_id']}")
            try:
                return {"status": "success", "data": resp.json()}
            except ValueError:
                return {"status": "success", "message": "Saved (no JSON body)"}

        except httpx.RequestError as e:
            logger.warning(f"{endpoint} network error to {url}: {e}")
            return {"status": "error", "error_message": f"Network error: {e}"}

        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            try:
                body = await e.response.aread()
                body = body.decode()
            except Exception:
                body = "(Could not read body)"
            logger.warning(f"{endpoint} HTTP {status_code}: {body}")
            return {"status": "error", "error_message": f"Server error ({status_code}): {body}"}

        except Exception as e:
            logger.error(f"Unexpected error in {endpoint}: {e}")
            return {"status": "error", "error_message": f"Unexpected error: {e}"}


# ──────────────────────────────────────────────────────────────────────────
# 🆕  Phase‑specific update helpers
# ──────────────────────────────────────────────────────────────────────────
async def update_risk_tolerance_field(user_id: str, field: str, value: Any) -> Dict[str, Any]:
    """
    Phase 2 – write to users.riskTolerance.<field>.
    """
    return await _post_convex_update(
        "update-risk-tolerance",
        {"user_id": user_id, "field": field, "value": value},
    )


async def update_vitality_sign_field(user_id: str, field: str, value: Any) -> Dict[str, Any]:
    """
    Phase 3 – write to users.vitalitySigns.<field>.
    """
    return await _post_convex_update(
        "update-vitality-sign",
        {"user_id": user_id, "field": field, "value": value},
    )


async def update_medical_profile_field(user_id: str, field: str, value: Any) -> Dict[str, Any]:
    """
    Phase 4 – write to users.medicalProfile.<field>.
    """
    return await _post_convex_update(
        "update-medical-profile",
        {"user_id": user_id, "field": field, "value": value},
    )











async def update_interview_progress(context: RunContext[MySessionInfo], new_progress: int) -> Dict[str, Any]:
    """
    Tells our Convex HTTP route to set interviewProgress = 1 for this user.
    Uses clerk_id from the context's session userdata.
    """
    if not context or not context.session or not hasattr(context.session, 'userdata') or not isinstance(context.session.userdata, MySessionInfo):
         logger.error("Invalid context or userdata in update_interview_progress")
         return {"status": "error", "message": "Invalid context provided"}

    clerk_id = context.session.userdata.clerk_id
    if not clerk_id:
        logger.error("Cannot update interview progress: clerk_id missing from session userdata.")
        return {"status": "error", "message": "Clerk ID not found in session."}
        
    if not CONVEX_LOG_URL or "YOUR_CONVEX_URL" in CONVEX_LOG_URL:
        logger.error("Cannot update interview progress: CONVEX_LOG_URL not set correctly.")
        return {"status": "error", "message": "CONVEX_LOG_URL not configured."}

    url = f"{CONVEX_LOG_URL}/update-interview-progress"
    payload = {"clerkId": clerk_id, "newProgress": new_progress}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=5.0)
            resp.raise_for_status()
            logger.info(f"Successfully updated interview progress for clerkId '{clerk_id}'.")
            try:
                # Attempt to return JSON response if available
                return {"status": "success", "data": resp.json()} 
            except ValueError:
                # Handle cases where Convex might return non-JSON success (e.g., just 200 OK)
                return {"status": "success", "message": "Interview progress updated."} 
        except httpx.RequestError as e:
            logger.warning(f"update_interview_progress network error to {url}: {e}")
            return {"status": "error", "error_message": f"Network error: {e}"}
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            try:
                error_text = await e.response.aread()
                error_text = error_text.decode()
            except Exception:
                 error_text = "(Could not read error body)"
            logger.warning(f"update_interview_progress HTTP {status_code} from {url}: {error_text}")
            return {"status": "error", "error_message": f"Server error ({status_code}): {error_text}"}
        except Exception as e:
            logger.error(f"Unexpected error in update_interview_progress: {e}")
            return {"status": "error", "error_message": f"Unexpected error: {e}"}


async def get_progress(user_id: str, default_progress: Dict[str, bool]) -> dict:
    """
    Async query to Convex for which demographic fields are complete.
    Falls back to the provided default_progress on any error.
    Requires user_id.
    """
    if not user_id:
        logger.error("get_progress called without user_id.")
        return default_progress # Return default if no user_id
        
    if not CONVEX_LOG_URL or "YOUR_CONVEX_URL" in CONVEX_LOG_URL:
        logger.error("Cannot get progress: CONVEX_LOG_URL not set correctly.")
        return default_progress # Return default if URL not set

    url = f"{CONVEX_LOG_URL}/get-progress"
    payload = {"user_id": user_id}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
            # Ensure we only return the expected keys, merging with default
            # and casting values to bool defensively
            progress_data = {k: bool(data.get(k, False)) for k in default_progress}
            logger.info(f"Successfully fetched progress for user '{user_id}'.")
            return {**default_progress, **progress_data} # Merge ensures all default keys exist

        except httpx.RequestError as e:
            logger.warning(f"get_progress network error to {url}: {e}")
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            try:
                error_text = await e.response.aread()
                error_text = error_text.decode()
            except Exception:
                 error_text = "(Could not read error body)"
            logger.warning(f"get_progress HTTP {status_code} from {url}: {error_text}")
        except ValueError as e:
             # Handle cases where Convex returns non-JSON or invalid JSON
             try:
                  response_text = await resp.aread()
                  response_text = response_text.decode()
             except Exception:
                  response_text = "(Could not read response text)"
             logger.warning(f"get_progress received invalid JSON from {url}. Status: {resp.status_code}, Response: '{response_text}'. Error: {e}")
        except Exception as e:
             logger.error(f"Unexpected error in get_progress: {e}")

    # on any failure, return the default map passed to the function
    logger.warning(f"get_progress failed for user '{user_id}', returning default progress.")
    return default_progress 

TIMEOUT = 10.0


async def _call_convex_progress(user_id: str) -> dict | None:
    """Low‑level fetch: returns raw JSON from /get-progress or None on error."""
    if not user_id:
        logger.error("get_progress called without user_id.")
        return None
    if not CONVEX_LOG_URL or "YOUR_CONVEX_URL" in CONVEX_LOG_URL:
        logger.error("CONVEX_LOG_URL not set correctly.")
        return None

    url = f"{CONVEX_LOG_URL}/get-progress"
    payload = {"user_id": user_id}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"get_progress request failed: {e}")
            return None


async def get_phase_progress(
    user_id: str,
) -> Tuple[int | None, Dict[int, Dict[str, bool]]]:
    """
    Returns (earliest_incomplete_phase, phase_progress_dict).
    On network / parsing error, returns (None, {}).
    """
    data = await _call_convex_progress(user_id)
    if not data or not data.get("success"):
        return None, {}

    earliest = data.get("earliestIncompletePhase")
    raw_map = data.get("phaseProgress", {})
    # Convex keys come back as strings "1", "2"… ; cast to int for convenience
    phase_map: Dict[int, Dict[str, bool]] = {
        int(phase): {k: bool(v) for k, v in fields.items()}
        for phase, fields in raw_map.items()
    }
    return earliest, phase_map


async def get_progress_for_phase(
    user_id: str,
    phase: int,
    default_progress: Dict[str, bool],
) -> Dict[str, bool]:
    """
    Convenience wrapper: returns a progress‑map for *one* phase,
    merged with its DEFAULT_PROGRESS dict so all keys are present.
    """
    _, phase_map = await get_phase_progress(user_id)
    # If backend or this phase missing, fall back to defaults
    progress = phase_map.get(phase, {})
    merged = {**default_progress, **progress}
    # ensure bool typing
    return {k: bool(merged.get(k, False)) for k in default_progress}