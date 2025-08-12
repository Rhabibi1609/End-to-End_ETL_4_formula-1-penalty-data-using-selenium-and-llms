import os
import json
import csv
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


# --- SETUP LLM ---
# Set your Gemini API key as an environment variable or pass it to the model if required.
os.environ["GOOGLE_API_KEY"] = "nope"

# Initialize the Gemini model
# We use a low temperature (0.0) to make the output more predictable and structured, which is ideal for JSON generation.
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash" \
"", temperature=0.0)

# --- PROMPT TEMPLATE ---
# The prompt is well-structured and doesn't need changes. It will work well with Gemini.
prompt_template = PromptTemplate(
    input_variables=["input_text"],
    template="""
You are an F1 steward. The text below contains incident report(s).

For each incident, extract these fields as a JSON array of objects (one object per incident).
If a field is not mentioned, set it to null.

Fields:
- type_of_document (e.g. "technical delegate report", "stewards decision", "team report", "driver report" or anything else) [str]
- year [int]
- grand_prix [str]
- description (brief summary of what happened) [str]
- session_type (e.g. "FP1", "FP2", "Qualifying", "Race") [str]
- track (if mentioned) [str]
- lap_number (if mentioned) [int]
- turn_number (if mentioned) [str]
- safety_car_or_vsc_involved (if mentioned) [str]
- penalty_given [str]
- type_of_incident (if mentioned) [str]
- was_contact_made (if mentioned) [str]
- immediate_advantage_gained (if mentioned) [str]
- drivers_involved (if mentioned) [str]
- teams_involved (if mentioned) [str]
- rule_violated or relevant_rule (if mentioned) [str]
- decision_notes (any justification or rationale given) [str]

for example:
for the text below, 
2022 ABU DHABI GRAND PRIX
18 - 20 November 2022
From The FIA Formula One Media Delegate Document 3
To All Teams, All Officials Date 17 November 2022
Time 11:30
Title Car Display Procedure
Description Car Display Procedure
Enclosed UAE DOC 3 - Car Display Procedure.pdf
Tom Wood
The FIA Formula One Media Delegate
2022 A D G P
BU HABI RAND RIX
17 – 20 November 2022
From The FIA Formula One Media Delegate Document 3
To All Officials, All Teams Date 17 November 2022
Time 11:30
NOTE TO TEAMS: CAR DISPLAY PROCEDURES
In addition to the requirements set out in Article 19 of the FIA Formula One Sporting Regulations, please
note the following procedures for the Car Display at this event:
(cid:120) Between 12:30 and 13:30 on Friday, one car from each team must be positioned as shown in the
attached drawing, with the other car positioned and available for viewing inside your garage.
(cid:120) The car outside may be used for pit stop practice but when no pit stop practice is taking place the
car must return to the same position.
(cid:120) At any event where it is raining during this presentation, we would ask you to leave the cars in
position and use your grid easy ups.
(cid:120) There must be enough space around the car on display to allow people to move safely.
(cid:120) The following specific timings have been allocated to assist the media and avoid overlapping of
any presentations or Q&A sessions teams may wish to hold (any presentations are not
mandatory for the Pre-Event Display):
Time Team
12:30 - 12:36 Mercedes
12:36 - 12:42 Red Bull Racing
12:42 - 12:48 Ferrari
12:48 - 12:54 McLaren
12:54 - 13:00 Alpine
13:00 - 13:06 AlphaTauri
13:06 - 13:12 Aston Martin
13:12 - 13:18 Williams
13:18 - 13:24 Alfa Romeo
13:24 - 13:30 Haas
(cid:120) Teams may conduct additional interviews and discussions outside of these times should they
wish, but it is highly recommended that these times are used by all teams to maximise efficiency.
1
(cid:120) After Qualifying, three cars for the presentation will be selected for display at this event, which
will take place on Sunday commencing five hours before the scheduled start of the formation lap.
This selection will be communicated to the teams by the FIA Technical Delegate after Qualifying.
(cid:120) The Post-Qualifying presentations will take place in the pit lane or team garages depending upon
activities taking place in the pit lane at the below timings:
o 12:05
o 12:20
o 12:35
(cid:120) Each team that is selected must have the technical representative indicated previously to the FIA
available at these times.
Tom Wood
The FIA Formula One Media Delegate
2

the output should be:
[
  {{
    "type_of_document": "Media delegate note / procedural document",
    "year": 2022,
    "grand_prix": "Abu Dhabi Grand Prix",
    "description": "Car Display Procedure for the event, specifying display times, arrangements, and post-qualifying car display instructions.",
    "session_type": null,
    "track": "Yas Marina Circuit",
    "lap_number": null,
    "turn_number": null,
    "safety_car_or_vsc_involved": null,
    "penalty_given": null,
    "type_of_incident": null,
    "was_contact_made": null,
    "immediate_advantage_gained": null,
    "drivers_involved": null,
    "teams_involved": ["Mercedes", "Red Bull Racing", "Ferrari", "McLaren", "Alpine", "AlphaTauri", "Aston Martin", "Williams", "Alfa Romeo", "Haas"],
    "rule_violated": null,
    "decision_notes": "Additional procedures for car displays; details given for pre-event and post-qualifying display arrangements."
  }}
]


Return **ONLY valid JSON**, no extra commentary.


Incident text:
{input_text}
"""
)

chain = prompt_template | llm | StrOutputParser()

# --- FUNCTION: Annotate whole text (single-shot) with retries ---
def annotate_text(input_text, retries=3, delay=10):
    """Invokes the LLM chain to extract data, with retries for robustness."""
    for attempt in range(retries):
        try:
            print(f"  ... Invoking LLM (Attempt {attempt + 1}/{retries})")
            result_str = chain.invoke({"input_text": input_text})
            
            # Gemini often wraps its response in a JSON markdown block. This cleans it.
            if result_str.strip().startswith("```json"):
                result_str = result_str.strip()[7:-3].strip()
            elif result_str.strip().startswith("```"):
                 result_str = result_str.strip()[3:-3].strip()
            
            parsed = json.loads(result_str)
            
            # Ensure the output is always a list of objects
            if isinstance(parsed, dict):
                parsed = [parsed] 
            return parsed

        except json.JSONDecodeError as e:
            print(f"  ❌ JSON Decode Error on attempt {attempt + 1}/{retries}: {e}")
            print("  ... LLM output may be malformed. Retrying after delay.")
            print("  ... Partial output received:\n", result_str[:500])
        except Exception as e:
            print(f"  ❌ Unexpected error on attempt {attempt + 1}/{retries}: {e}")
            print("  ... Retrying after delay.")

        time.sleep(delay)

    print("❌ All retries failed for this file.")
    return []

# --- FUNCTION: Save to CSV ---
def save_annotations_csv(annotations, output_csv_file):
    """Appends a list of annotation dictionaries to a CSV file."""
    # Define the full set of fields to ensure consistent column order
    fields = [
        "type_of_document", "year", "grand_prix", "description", "session_type",
        "track", "lap_number", "turn_number", "safety_car_or_vsc_involved",
        "penalty_given", "type_of_incident", "was_contact_made",
        "immediate_advantage_gained", "drivers_involved", "teams_involved",
        "rule_violated", "decision_notes", "source_file"
    ]

    write_header = not os.path.exists(output_csv_file)

    with open(output_csv_file, "a", newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        if write_header:
            writer.writeheader()
        writer.writerows(annotations)

# --- MAIN PROCESSOR ---
def process_folder(input_folder, output_csv_file, cool_down_time=20):
    """Processes all .txt files in a folder, extracting annotations and saving to CSV."""
    processed_files = set()

    # Pre-populate the set of already processed files to avoid re-processing
    if os.path.exists(output_csv_file):
        try:
            with open(output_csv_file, "r", encoding="utf-8") as f:
                # Use a simple reader to avoid issues if the file is empty
                # DictReader needs a header row to work
                if f.readline(): # check if file is not empty
                    f.seek(0) # go back to the beginning
                    reader = csv.DictReader(f)
                    if "source_file" in reader.fieldnames:
                         processed_files = {row["source_file"] for row in reader}
            print(f"Found {len(processed_files)} previously processed files.")
        except Exception as e:
            print(f"Could not read existing CSV to check for processed files: {e}")


    files_to_process = [
        f for f in os.listdir(input_folder)
        if f.endswith(".txt") and f not in processed_files
    ]
    
    if not files_to_process:
        print("🎉 No new files to process. All done!")
        return

    print(f"Found {len(files_to_process)} new files to process.")

    for i, filename in enumerate(files_to_process):
        file_path = os.path.join(input_folder, filename)
        print(f"\n🔎 Processing file {i + 1}/{len(files_to_process)}: {filename}")

        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        annotations = annotate_text(raw_text)

        if annotations:
            # Add the source filename to each extracted record
            for item in annotations:
                item["source_file"] = filename

            save_annotations_csv(annotations, output_csv_file)
            print(f"✅ Saved {len(annotations)} annotation(s) for {filename}")
        else:
            print(f"⚠️ No annotations were generated or saved for {filename}")

        if i < len(files_to_process) - 1: # No need to cool down after the last file
            print(f"🕒 Cooling down for {cool_down_time} seconds...")
            time.sleep(cool_down_time)

    print("\n🎉 All files processed!")

# --- ENTRY POINT ---
if __name__ == "__main__":
    input_folder = r"folder loc here"
    output_csv_file = r"folder loc here"
    
    # Using a shorter cool-down time as we are not running a local model that heats up
    # However, a cool-down can still be useful to avoid hitting API rate limits.
    process_folder(input_folder, output_csv_file, cool_down_time=5)