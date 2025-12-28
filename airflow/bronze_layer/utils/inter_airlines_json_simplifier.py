import json


def transform_airline_codes(input_file: str, output_file: str):
    """
    Transform airline codes from complex structure to simple name->code mapping.

    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
    """
    try:
        # Load the original data
        with open(input_file, "r", encoding="utf-8") as f:
            airlines = json.load(f)

        # Create simplified mapping
        simplified = {}

        for airline in airlines:
            # Get airline name from name_translations or name field
            name = None
            if "name_translations" in airline and "en" in airline["name_translations"]:
                name = airline["name_translations"]["en"]
            elif "name" in airline:
                name = airline["name"]

            # Get airline code
            code = airline.get("code")

            # Add to mapping if both name and code are available
            if name and code:
                # Remove "Airlines", "Air", etc. for better matching
                clean_name = name.replace(" Airlines", "").replace(" Air", "").strip()
                simplified[clean_name] = code

                # Also add the full name
                simplified[name] = code

        # Save simplified mapping
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(simplified, f, indent=2, ensure_ascii=False)

        print(f"Transformed {len(airlines)} airlines to {len(simplified)} entries")
        print(f"Saved to {output_file}")

        # Show some examples
        print("\nSample entries:")
        for i, (name, code) in enumerate(list(simplified.items())[:10]):
            print(f"  {name}: {code}")

        return simplified

    except Exception as e:
        print(f"Error transforming airline codes: {e}")
        return {}


# Run the transformation
if __name__ == "__main__":
    input_file = "airlines.json"  # Your input file
    output_file = "airline_codes_simple.json"
    transform_airline_codes(input_file, output_file)
