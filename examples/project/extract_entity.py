import os
from collections import Counter


def process_markdown_files(directory_path, output_filename="sorted_headings.txt"):
    """
    Processes all markdown files in a directory to extract headings.

    Args:
        directory_path (str): The path to the directory containing .md files.
        output_filename (str): The name of the file to save the sorted headings.

    Returns:
        dict: A dictionary where keys are md file basenames and values are lists
              of headings (lines starting with '## ', '### ', '#### ').
              Returns None if the directory is not found.
    """
    if not os.path.isdir(directory_path):
        print(f"Error: Directory not found at '{directory_path}'")
        return None

    file_headings_map = {}
    all_headings = []

    # Define the prefixes to look for
    heading_prefixes = ('## ', '### ', '#### ')

    print(f"Scanning directory: {directory_path}\n")

    # Iterate over each file in the specified directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".md"):
            file_path = os.path.join(directory_path, filename)

            # Use os.path.basename for cross-platform compatibility
            basename = os.path.basename(file_path)

            current_file_headings = []
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        # Check if the line starts with any of the defined prefixes
                        if line.strip().startswith(heading_prefixes):
                            # Add the cleaned-up line to our lists
                            clean_line = line.strip()
                            for prefix in heading_prefixes:
                                if clean_line.startswith(prefix):
                                    clean_line = clean_line[len(prefix):].strip().lower()
                                    break
                            current_file_headings.append(clean_line)
                            all_headings.append(clean_line)

                # Add the result to our dictionary
                if current_file_headings:
                    file_headings_map[basename] = current_file_headings
                    print(f"Found {len(current_file_headings)} headings in '{basename}'")

            except Exception as e:
                print(f"Could not read file {filename} due to error: {e}")

    # Part 2: Merge, count frequency, sort, and save
    if not all_headings:
        print("\nNo headings were found in any .md files.")
        return file_headings_map

    # Count the frequency of each heading
    heading_counts = Counter(all_headings)

    # Sort the unique headings by frequency in descending order
    # The result of most_common() is a list of (item, count) tuples
    sorted_headings = [(item, count) for item, count in heading_counts.most_common()]

    # Save the sorted list to a text file
    output_path = output_filename
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for heading, count in sorted_headings:
                f.write(f"{heading} (count: {count})\n")
        print(f"\nSuccessfully saved sorted headings to '{output_path}'")
    except Exception as e:
        print(f"Could not write to output file due to error: {e}")
    return file_headings_map


def create_sample_files(directory_name="sample_md_files"):
    """Creates a sample directory with markdown files for testing."""
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)

    # Sample file 1
    with open(os.path.join(directory_name, "post1.md"), "w", encoding='utf-8') as f:
        f.write("# Introduction\n\nSome intro text.\n\n")
        f.write("## Getting Started\n\nDetails on how to get started.\n\n")
        f.write("### Installation\n\nInstall instructions.\n\n")
        f.write("## Core Concepts\n\nExplaining the core ideas.\n\n")

    # Sample file 2
    with open(os.path.join(directory_name, "tutorial.md"), "w", encoding='utf-8') as f:
        f.write("# Tutorial Guide\n\nWelcome!\n\n")
        f.write("## Getting Started\n\nThis is a prerequisite.\n\n")
        f.write("### Configuration\n\nHow to configure the tool.\n\n")
        f.write("#### Advanced Settings\n\nFor power users.\n\n")

    # Sample file 3 (empty md file)
    open(os.path.join(directory_name, "empty.md"), "w", encoding='utf-8').close()

    # Non-md file to be ignored
    with open(os.path.join(directory_name, "notes.txt"), "w", encoding='utf-8') as f:
        f.write("This is a regular text file.")

    print(f"Created sample directory and files in '{directory_name}'\n")
    return directory_name


# --- Main execution ---
if __name__ == "__main__":
    # Create a sample directory and files to demonstrate the script
    # sample_dir = create_sample_files()

    sample_dir = 'medical_guide_markdown'
    # Run the main function
    headings_dict = process_markdown_files(sample_dir)

    if headings_dict is not None:
        print("\n--- Generated Dictionary ---")
        # Using a loop for cleaner printing of the dictionary
        for filename, headings in headings_dict.items():
            print(f"'{filename}': {headings}")
        print("--------------------------\n")

    # You can uncomment the line below to clean up the sample files after running
    # import shutil
    # shutil.rmtree(sample_dir)
    # print(f"Cleaned up sample directory: {sample_dir}")
