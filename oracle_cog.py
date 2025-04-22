import os
import dotenv
import json
import random
import openai
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv

# Full path to your .env file
env_path = r"C:\AIRPG\.env"

# Load the .env file
load_dotenv(dotenv_path=env_path)

# --- Configure OpenAI API ---
openai.api_key = os.environ.get("OPENAI_API_KEY")
if not openai.api_key:
    print("Warning: OPENAI_API_KEY environment variable not set. The bot might not function correctly.")
client = openai.OpenAI(api_key=openai.api_key)

# --- Oracle File Configuration ---
ORACLE_JSON_PATH = ".\oracle\oracle.json"
OUTPUT_DIR = ".\oracle"  # Directory to save results

# --- Oracle Generation ---
def generate_oracle(tone="proto-transhuman solarpunk apocalypse"):
    prompt = f"""
Create a JSON structure with four oracle tables for a story-driven RPG in the style of In a Wicked Age.
Each table should contain 13 vivid, tone-appropriate story elements. The tone is: "{tone}"

Respond only with raw JSON using this structure:
{{
  "Oracle of [Table Name]": [
    "Element 1",
    "Element 2",
    ... up to 13
  ],
  ...
}}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a generator of RPG oracle tables."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
    )

    content = response.choices[0].message.content.strip()
    print("\n--- GPT RESPONSE START ---")
    print(content)
    print("--- GPT RESPONSE END ---\n")

    # Try to extract JSON if GPT wraps in markdown
    if content.startswith("```json"):
        content = content.strip("```json").strip("```").strip()

    try:
        oracle_json = json.loads(content)
    except json.JSONDecodeError as e:
        print("❌ Failed to parse JSON from GPT response.")
        print("Error:", e)
        return {}

    os.makedirs(os.path.dirname(ORACLE_JSON_PATH), exist_ok=True)
    with open(ORACLE_JSON_PATH, "w") as f:
        json.dump(oracle_json, f, indent=2)
    return oracle_json

async def consult_the_oracle(json_file_path=ORACLE_JSON_PATH, num_elements=4):
    try:
        if not os.path.exists(json_file_path):
            return f"Error: JSON file not found at '{json_file_path}'"

        with open(json_file_path, 'r') as f:
            oracle_data = json.load(f)

    except json.JSONDecodeError:
        return f"Error: Could not decode JSON from file '{json_file_path}'. Check formatting."
    except Exception as e:
        return f"An unexpected error occurred while loading the file: {e}"

    table_names = list(oracle_data.keys())
    if not table_names:
        return "Error: JSON data seems empty or has no tables."

    rows_per_table = 0
    for table in table_names:
        if not isinstance(oracle_data[table], list) or not oracle_data[table]:
            continue
        if rows_per_table == 0:
            rows_per_table = len(oracle_data[table])
        elif len(oracle_data[table]) != rows_per_table:
            pass

    if rows_per_table == 0:
        return "Error: No valid rows found in any table."

    total_combinations = len(table_names) * rows_per_table
    if num_elements > total_combinations:
        num_elements = total_combinations

    selected_elements = []
    used_combinations = set()

    while len(selected_elements) < num_elements:
        chosen_table = random.choice(table_names)

        if len(oracle_data[chosen_table]) != rows_per_table:
            continue

        chosen_row_index = random.randrange(len(oracle_data[chosen_table]))
        combination_id = (chosen_table, chosen_row_index)

        if combination_id not in used_combinations:
            used_combinations.add(combination_id)
            element = oracle_data[chosen_table][chosen_row_index]
            selected_elements.append(element)

        if len(used_combinations) >= total_combinations and len(selected_elements) < num_elements:
            break

    return selected_elements

async def generate_conflict_map(oracle_results):
    if not oracle_results or isinstance(oracle_results, str):
        return "Could not generate conflict map due to an issue with the Oracle.", None, None

    prompt = f"""
You are generating four protagonist characters for a story-driven roleplaying game inspired by these oracle elements:

Elements:
{oracle_results}

Each character must be based on one oracle element and must be a fully fleshed-out protagonist.

For each character, include:
- name
- origin_element (from the list above)
- description (who they are, how they relate to the setting, one sentence of 5 to 10 words.)
- particular_strength (name + short effect)
- two best_interests:
     - A short 5–8 word sentence that includes another character’s name
     - Can be achieved within a single roleplaying session
     - It must reflect a goal that can **only be achieved at that other character’s expense**
     - Not grand goals.
     - Immediate actions.
     - The characters are *not allies*. Their goals are mutually exclusive.
- approaches (assign one of each: d12, d10, d8, d6, d6, d4 to: covertly, directly, for myself, for others, with love, with violence)

Also return a **conflict matrix**, listing for each character:
- Who they are in conflict with
- The reason for the conflict
- The type of animosity (choose from: betrayal, envy, vengeance, desire, ambition, duty, prophecy, desperation, family, ideology, romance)


Respond in this exact structure as raw JSON:

{{ "elements": [...], "characters": [...], "conflicts": [...] }}

"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a narrative conflict mapping assistant for RPG worldbuilding.  Your response should be in JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
        )
        raw_response_content = response.choices[0].message.content  # Get the raw text
        print(f"Raw OpenAI Response:\n{raw_response_content}")  # Print the raw response

        # 1.5. Remove leading/trailing triple quotes and 'json' label
        # raw_response_content = raw_response_content.strip()  # Remove leading/trailing whitespace
        #raw_response_content = raw_response_content[7:]  # Remove leading "'''json"
        #raw_response_content = raw_response_content[:-3]  # Remove trailing "'''"
        #raw_response_content = raw_response_content.strip()  # Remove any extra whitespace

        # Clean markdown
        if raw_response_content.startswith("```json"):
           raw_response_content = raw_response_content.replace("```json", "").replace("```", "").strip()

        # Parse the JSON response
        try:
            json_response = json.loads(raw_response_content)
            
              # Print the raw response
            
            elements = json_response.get("elements", [])
            characters = json_response.get("characters", [])
            conflicts = json_response.get("conflicts", [])
            return elements, characters, conflicts
        except json.JSONDecodeError:
            return "Error: Could not decode JSON from AI response.", None, None

    except openai.APIError as e:
        return f"Error generating conflict map: {e}", None, None



async def save_results_to_json(oracle_elements, conflicts, characters): #changed conflict_map to conflicts
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = os.path.join(OUTPUT_DIR, f"oracle_results_{timestamp}")

    try:
        # Save Oracle Elements
        with open(f"{base_filename}_elements.json", 'w') as f:
            json.dump(oracle_elements, f, indent=4)

        # Save Characters
        with open(f"{base_filename}_characters.json", 'w') as f:
            json.dump(characters, f, indent=4)

        # Save Conflict Map
        with open(f"{base_filename}_conflicts.json", 'w') as f:
            json.dump(conflicts, f, indent=4)  # Use the 'conflicts' variable

        return f"Results saved to {base_filename}_elements.json, {base_filename}_characters.json, and {base_filename}_conflicts.json"
    except Exception as e:
        return f"Error saving results to JSON files: {e}"

class OracleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="oracle", help="Consult the Story Oracle for story elements and generate a conflict map.")
    async def oracle_command(self, ctx, num_elements: int = 4):
        await ctx.send("Consulting the Story Oracle...")
        oracle_results = await consult_the_oracle(num_elements=num_elements)

        if isinstance(oracle_results, str):
            await ctx.send(oracle_results)
            return

        if oracle_results:
            elements_str = "\n".join([f"{i+1}. {element}" for i, element in enumerate(oracle_results)])
            await ctx.send(f"The Oracle reveals the following elements for your story:\n```\n{elements_str}\n```")

            await ctx.send("Generating a conflict map based on these elements...")
            conflicts, original_elements, characters = await generate_conflict_map(oracle_results) # changed conflict_map to conflicts
            if conflicts:
                await ctx.send(f"**Conflict Map:**\n```\n{conflicts}\n```")
                await ctx.send(f"**Characters:**\n```\n{characters}\n```")
                save_message = await save_results_to_json(original_elements, conflicts, characters)
                await ctx.send(save_message)
            else:
                await ctx.send(conflicts) #send the error message
        else:
            await ctx.send("Could not retrieve elements from the Oracle.")

async def setup(bot):
    await bot.add_cog(OracleCog(bot))

if __name__ == "__main__":
    import asyncio

    async def main():
        print("Consulting the Story Oracle (direct execution)...")
        results = await consult_the_oracle(num_elements=4)

        if isinstance(results, str):
            print(results)
        elif results:
            print("\nThe Oracle reveals the following elements for your story:")
            print("-" * 50)
            for i, element in enumerate(results, 1):
                print(f"{i}. {element}")
            print("-" * 50)

            conflict_map_output, original_elements, characters = await generate_conflict_map(results) # changed conflict_map_output to conflicts
            if conflict_map_output:
                print("\nConflict Map:")
                print(conflict_map_output)
                print("\nCharacters:")
                print(characters)
                save_message = await save_results_to_json(original_elements, conflict_map_output, characters)
                print(save_message)
            else:
                print(conflict_map_output)
        else:
            print("Could not retrieve elements from the Oracle.")

    asyncio.run(main())
