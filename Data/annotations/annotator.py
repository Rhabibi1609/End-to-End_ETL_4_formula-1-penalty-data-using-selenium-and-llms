import os
import json
import csv
import time
from langchain_community.llms import Ollama
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- SETUP LLM ---
llm = OllamaLLM(model="llama3.2:latest")

# --- PROMPT TEMPLATE ---
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
    for attempt in range(retries):
        try:
            result_str = chain.invoke({"input_text": input_text})
            result_str = result_str.strip()

            # Clean code block markers if any
            if result_str.startswith("```json"):
                result_str = result_str[7:]
            if result_str.endswith("```"):
                result_str = result_str[:-3]

            parsed = json.loads(result_str)
            if isinstance(parsed, dict):
                parsed = [parsed]
            return parsed

        except json.JSONDecodeError as e:
            print(f"JSON error: {e}. Retrying attempt {attempt + 1}/{retries}")
            print("Partial output:\n", result_str[:300])
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying attempt {attempt + 1}/{retries}")

        time.sleep(delay)

    print("❌ All retries failed for this file.")
    return []

# --- FUNCTION: Save to CSV ---
def save_annotations_csv(annotations, output_csv_file):
    fields = list(annotations[0].keys())

    write_header = not os.path.exists(output_csv_file)

    with open(output_csv_file, "a", newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        if write_header:
            writer.writeheader()
        writer.writerows(annotations)

# --- MAIN PROCESSOR ---
def process_folder(input_folder, output_csv_file, cool_down_time=20):
    processed_files = set()

    if os.path.exists(output_csv_file):
        with open(output_csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            processed_files = {row["source_file"] for row in reader if "source_file" in row}

    files_to_process = [
        f for f in os.listdir(input_folder)
        if f.endswith(".txt") and f not in processed_files
    ]

    for i, filename in enumerate(files_to_process):
        file_path = os.path.join(input_folder, filename)
        print(f"\n🔎 Processing file {i + 1}/{len(files_to_process)}: {filename}")

        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        annotations = annotate_text(raw_text)

        if annotations:
            # Add source file tag
            for item in annotations:
                item["source_file"] = filename

            save_annotations_csv(annotations, output_csv_file)
            print(f"✅ Saved annotations for {filename}")
        else:
            print(f"⚠️ No annotations saved for {filename}")

        print(f"🕒 Cooling down for {cool_down_time} seconds...\n")
        time.sleep(cool_down_time)

    print("🎉 All files processed!")

# --- ENTRY POINT ---
if __name__ == "__main__":
    input_folder = r"folder location here"  # Replace with your folder path
    output_csv_file = r"folder location here/annotations.csv"  # Replace with your output CSV path
    process_folder(input_folder, output_csv_file, cool_down_time=30)
