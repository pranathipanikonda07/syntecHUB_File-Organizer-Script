# syntecHUB_File-Organizer-Script

Small, flexible Python script to keep a messy folder organized by moving files into subfolders based on their extensions.

Features
- Moves files into intuitive subfolders (Images, Documents, Archives, Code, Video, Audio, Others)
- Safe collision handling (appends numeric suffix to conflicting names)
- Dry-run mode so you can preview changes without modifying anything
- CSV and human-readable logging of operations
- Optional per-user extension mapping via a CSV file

Quick start
1. Ensure Python 3.8+ is installed and available on your PATH.
2. From a command prompt or PowerShell, run:

	python file_organizer.py --path "C:\Users\You\Downloads" --dry-run

3. Check the printed summary and CSV log (organizer_log.csv by default) to verify what would move.

Usage examples
- Dry-run recursive scan:

	python file_organizer.py -p "C:\Users\You\Desktop" -r --dry-run

- Real run with custom logs:

	python file_organizer.py -p "C:\Users\You\Downloads" --log "C:\logs\organizer.csv" --log-human "C:\logs\organizer.txt"

- Use a custom extension mapping (CSV format: ext,folder):

	# custom_map.csv
	.blend,3D
	.psd,Designs

	python file_organizer.py -p "C:\MyFolder" --map custom_map.csv

How the script handles collisions
- If the destination filename already exists the script writes a new filename like `name (1).ext`, `name (2).ext` etc. — nothing will be overwritten.

Scheduling with Windows Task Scheduler (optional)
You can schedule the script to run regularly using Windows Task Scheduler. Example: schedule the organizer to run every day at 23:00 for a specific folder.

Command-line schtasks example (create a daily task running under the current user):

	schtasks /Create /SC DAILY /TN "FileOrganizer_Downloads" /TR "\"C:\\Python39\\python.exe\" \"C:\\Path\\To\\file_organizer.py\" -p \"C:\\Users\\YourName\\Downloads\" --log \"C:\\Logs\\organizer.csv\"" /ST 23:00

Notes:
- In Task Scheduler GUI you can create a task and set the "Start in (optional)" to the script folder, and the action to call python with the script.
- For reliability, point the task to the full path of your python executable and script, and consider enabling "Run whether user is logged on or not" if you need background runs.

Safety and recommendations
- Always test with --dry-run before running for real.
- Make regular backups if you operate on important folders.

Example: try it locally
1. Create a small folder with example files on your Desktop.
2. Run the script in dry-run mode and inspect the output.
3. Remove --dry-run to apply the changes.

Want improvements?
 - Add file deduplication using content hashes
 - Expand mapping UI or add a small GUI
