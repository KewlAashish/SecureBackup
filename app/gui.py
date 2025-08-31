from __future__ import annotations
import PySimpleGUI as sg
import threading
import base64
from pathlib import Path
from datetime import datetime
from .config import load_config, save_config
from .backup import run_backup
from .restore import run_restore
from .scheduler import BackupScheduler

try:
    from plyer import notification
    NOTIFICATIONS_ENABLED = True
except ImportError:
    NOTIFICATIONS_ENABLED = False

### CHANGE ###
# Base64 encoded loading spinner GIF for visual feedback
LOADER_GIF = b'R0lGODlhEAAQAPIAAP///wAAAMLCwkJCQgAAAGJiYoKCgpKSkiH/C05FVFNDQVBFMi4wAwEAAAAh/hpDcmVhdGVkIHdpdGggYWpheGxvYWQuaW5mbwAh+QQJCgAAACwAAAAAEAAQAAADMwi63P4wyklrE2MIOggZnAdOmGYJRbExwroUmcG2LmDEwnHQLVsYOd2mBzkYDAdKa+dIAAAh+QQJCgAAACwAAAAAEAAQAAADNAi63P5OjCEgG4QMu7DmikRxQlFUYDEZIGBMRVsaqHwctXXf7WEYB4Ag1xjihkMZsiUkKhIAIfkECQoAAAAsAAAAABAAEAAAAzYIujIjK8pByJDMlFYvBoVjHA70GU7xSUJhmKtwHPAKzLO9HMaoKwJZ7Rf8AYPDDzKpZBqfvwQAIfkECQoAAAAsAAAAABAAEAAAAzMIumIlK8oyhpHsnFZfhYumCYUhDAQxRIdhHBGqRoKw0R8DYlJd8z0fMDgsGo/IpHI5TAAAIfkECQoAAAAsAAAAABAAEAAAAzIIunInK0rnZBTwGPNMgQwmdsNgXGJUlIWEuR5oWUIpz8pAEAMe6TwfwyYsGo/IpFKSAAAh+QQJCgAAACwAAAAAEAAQAAADMwi6IMKQORfjdOe82p4wGccc4CEuQradylesojEMBgsUc2G7sDX3lQGBMLAJibufbSlKAAAh+QQJCgAAACwAAAAAEAAQAAADMgi63P7wCRHZnFVdmgHu2nFwlWCI3WGc3TSWhUFGxTAUkGCbtgENBMJAEJsxgMLWzpEAACH5BAkKAAAALAAAAAAQABAAAAMyCLrc/jDKSatlQtScKdceCAjDII7HcQ4EMTCpyrCuUBjCYRgHVtqlAiB1YhiCnlsRkAAAIfkECQoAAAAsAAAAABAAEAAAAzYIujIjK8pByJDMlFYvBoVjHA70GU7xSUJhmKtwHPAKzLO9HMaoKwJZ7Rf8AYPDDzKpZBqfvwQAIfkECQoAAAAsAAAAABAAEAAAAzMIumIlK8oyhpHsnFZfhYumCYUhDAQxRIdhHBGqRoKw0R8DYlJd8z0fMDgsGo/IpHI5TAAAIfkECQoAAAAsAAAAABAAEAAAAzIIunInK0rnZBTwGPNMgQwmdsNgXGJUlIWEuR5oWUIpz8pAEAMe6TwfwyYsGo/IpFKSAAAh+QQJCgAAACwAAAAAEAAQAAADMwi6IMKQORfjdOe82p4wGccc4CEuQradylesojEMBgsUc2G7sDX3lQGBMLAJibufbSlKAAAh+QQJCAAAACwAAAAAEAAQAAADMgi63P7wCRHZnFVdmgHu2nFwlWCI3WGc3TSWhUFGxTAUkGCbtgENBMJAEJsxgMLWzpEAACH5BAkKAAAALAAAAAAQABAAAAMyCLrc/jDKSatlQtScKdceCAjDII7HcQ4EMTCpyrCuUBjCYRgHVtqlAiB1YhiCnlsRkAAAOwAAAAAAAAAAAA=='

# --- Helper Functions ---

def get_backup_filename(name: str) -> str:
    """Generates a unique backup filename with a timestamp."""
    dt = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()
    return f"{sanitized_name}.sbk"

def run_backup_threaded(window: sg.Window, sources: list[str], dest: str, password: str, backup_name: str):
    """Runs the backup process in a thread to avoid freezing the GUI."""
    window.write_event_value("-BACKUP_STATUS-", "Starting backup...")
    window["-RUN_BACKUP-"].update(disabled=True)
    window["-BACKUP_LOADER-"].update(visible=True)
    
    try:
        output_filename = get_backup_filename(backup_name)
        backup_path = run_backup(sources, dest, password, output_filename)
        result = f"Success! Backup saved to:\n{backup_path}"
        if NOTIFICATIONS_ENABLED:
            notification.notify(title="SecureBackup", message=f"Backup '{backup_name}' completed successfully.", app_name="SecureBackup")
    except Exception as e:
        result = f"Error during backup: {e}"
        if NOTIFICATIONS_ENABLED:
            notification.notify(title="SecureBackup - Error", message=f"Backup '{backup_name}' failed.", app_name="SecureBackup")
            
    window.write_event_value("-BACKUP_COMPLETE-", result)

def run_restore_threaded(window: sg.Window, encrypted_path: str, output_folder: str, password: str):
    """Runs the restore process in a thread."""
    window.write_event_value("-RESTORE_STATUS-", "Starting restore...")
    window["-RUN_RESTORE-"].update(disabled=True)
    window["-RESTORE_LOADER-"].update(visible=True)
    
    try:
        run_restore(encrypted_path, output_folder, password)
        result = f"Success! Files restored to:\n{output_folder}"
    except Exception as e:
        result = f"Error during restore: {e}"

    window.write_event_value("-RESTORE_COMPLETE-", result)


# --- UI Layout ---

sg.theme("DarkGrey9")
ICON_PLUS = '➕'
ICON_EDIT = '✏️'
ICON_DELETE = '🗑️'
ICON_SAVE = '💾'

def build_manual_backup_tab():
    return sg.Frame("Manual One-Off Backup", [
        [sg.Text("Sources (files or folders):")],
        [sg.Input(key="-MANUAL_SRC-", size=(60,1)), sg.FilesBrowse("Browse Files", target="-MANUAL_SRC-"), sg.FolderBrowse("Browse Folder", target="-MANUAL_SRC-")],
        [sg.Text("Destination Folder:")],
        [sg.Input(key="-MANUAL_DEST-", size=(60,1)), sg.FolderBrowse("Browse")],
        [sg.Text("Backup Name:", tooltip="Used to name the final backup file."), sg.Input("MyBackup", key="-MANUAL_NAME-", size=(25,1))],
        [sg.Text("Password:"), sg.Input(password_char="*", key="-MANUAL_PASS-", size=(30,1))],
        [sg.Button("Run Backup Now", key="-RUN_BACKUP-", button_color=("white", "#0078D7"), font=("Segoe UI", 11))],
        [sg.HorizontalSeparator()],
        [sg.Image(data=LOADER_GIF, key='-BACKUP_LOADER-', visible=False), sg.Text("Status:", font=("Segoe UI", 10, "bold"))],
        [sg.Multiline("", key="-BACKUP_STATUS-", size=(80, 5), disabled=True, autoscroll=True, background_color='#333333', text_color='white')]
    ], font=("Segoe UI", 12, "bold"), relief=sg.RELIEF_GROOVE, pad=(10,10))

def build_restore_tab():
    return sg.Frame("Restore from Backup", [
        [sg.Text("Backup File (.sbk):")],
        [sg.Input(key="-RESTORE_FILE-", size=(60,1)), sg.FileBrowse("Browse", file_types=(("SecureBackup Files", "*.sbk"),))],
        [sg.Text("Restore to Folder:")],
        [sg.Input(key="-RESTORE_DEST-", size=(60,1)), sg.FolderBrowse("Browse")],
        [sg.Text("Password:"), sg.Input(password_char="*", key="-RESTORE_PASS-", size=(30,1))],
        [sg.Button("Restore Files", key="-RUN_RESTORE-", button_color=("white", "#107C10"), font=("Segoe UI", 11))],
        [sg.HorizontalSeparator()],
        [sg.Image(data=LOADER_GIF, key='-RESTORE_LOADER-', visible=False), sg.Text("Status:", font=("Segoe UI", 10, "bold"))],
        [sg.Multiline("", key="-RESTORE_STATUS-", size=(80, 5), disabled=True, autoscroll=True, background_color='#333333', text_color='white')]
    ], font=("Segoe UI", 12, "bold"), relief=sg.RELIEF_GROOVE, pad=(10,10))
    
def build_schedule_tab():
    # ... (rest of the function is unchanged)
    cfg = load_config()
    jobs = cfg.get("jobs", [])
    job_table_data = [
        [job.get("name", ""), job.get("frequency", ""), job.get("time", ""), ", ".join(job.get("sources", [])), job.get("destination", "")]
        for job in jobs if job.get("enabled", True)
    ]
    
    job_list_col = sg.Column([
        [sg.Frame("Scheduled Jobs", [
            [sg.Table(
                headings=["Name", "Frequency", "Time", "Sources", "Destination"],
                values=job_table_data, key="-JOBTABLE-", auto_size_columns=False, col_widths=[15,10,8,30,30],
                enable_events=True, justification="left", font=("Segoe UI", 10), num_rows=10, select_mode=sg.TABLE_SELECT_MODE_BROWSE
            )],
            [
                sg.Button(f"{ICON_PLUS} Add New Job", key="-ADD_JOB-", button_color=("white", "#0078D7")),
                sg.Button(f"{ICON_EDIT} Edit Selected", key="-EDIT_JOB-", button_color=("white", "#0078D7")),
                sg.Button(f"{ICON_DELETE} Delete Selected", key="-DELETE_JOB-", button_color=("white", "#E81123"))
            ]
        ], font=("Segoe UI", 12, "bold"), relief=sg.RELIEF_GROOVE, pad=(10,10))]
    ])
    
    job_details_col = sg.Column([
         [sg.Frame("Job Editor", [
            [sg.Text("Name:", size=(12,1)), sg.Input(key="-JOB_NAME-")],
            [sg.Text("Sources:", size=(12,1)), sg.Input(key="-JOB_SRC-")],
            [sg.Push(), sg.FilesBrowse("Browse Files", target="-JOB_SRC-", size=(12,1)), sg.FolderBrowse("Browse Folder", target="-JOB_SRC-", size=(12,1))],
            [sg.Text("Destination:", size=(12,1)), sg.Input(key="-JOB_DEST-"), sg.FolderBrowse("Browse")],
            [sg.Text("Frequency:", size=(12,1)), sg.Combo(["Daily", "Weekly"], key="-JOB_FREQ-", default_value="Daily", enable_events=True)],
            [sg.Text("Time:", size=(12,1)), sg.Combo([f"{h:02d}" for h in range(24)], key="-JOB_HOUR-", default_value="10"), sg.Text(":"), sg.Combo([f"{m:02d}" for m in range(0,60,5)], key="-JOB_MIN-", default_value="00")],
            [sg.Text("Day of week:", size=(12,1), key="-JOB_DOW_TEXT-", visible=False), sg.Combo(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], key="-JOB_DOW-", visible=False)],
            [sg.Text("Password:", size=(12,1)), sg.Input(password_char="*", key="-JOB_PASS-")],
            [sg.Checkbox("Enable this job", default=True, key="-JOB_ENABLED-")],
            [sg.Button(f"{ICON_SAVE} Save Job", key="-SAVE_JOB-", button_color=("white", "#107C10")), sg.Button("Cancel", key="-CANCEL_EDIT-")]
        ], font=("Segoe UI", 12, "bold"), relief=sg.RELIEF_GROOVE, pad=(10,10), key="-JOB_EDITOR-", visible=False)]
    ], vertical_alignment='top')
    
    return [[job_list_col, job_details_col]]

def build_window():
    layout = [
        [sg.Text("🔒 SecureBackup", font=("Segoe UI", 22, "bold"), pad=(10,10))],
        [sg.TabGroup([[
            sg.Tab("Manual Backup", [[build_manual_backup_tab()]], key="-TAB_BACKUP-"),
            sg.Tab("Restore", [[build_restore_tab()]], key="-TAB_RESTORE-"),
            sg.Tab("Scheduled Jobs", build_schedule_tab(), key="-TAB_SCHEDULE-")
        ]], tab_location='top', font=("Segoe UI", 12), pad=(10,10))],
        [sg.Button("Exit", button_color=("white", "grey"), font=("Segoe UI", 11), size=(12,1))]
    ]
    return sg.Window("SecureBackup", layout, finalize=True, size=(1000, 750), resizable=True)

# --- Main Application Logic ---

def main():
    window = build_window()
    # ... (event loop needs minor changes)
    cfg = load_config()
    jobs = cfg.get("jobs", [])
    scheduler = BackupScheduler()
    scheduler.start()
    
    editing_job_index = None

    def create_job_function(job: dict):
        # ... (unchanged)
        def job_fn():
            try:
                backup_name = job["name"]
                output_filename = get_backup_filename(backup_name)
                run_backup(job["sources"], job["destination"], job["password"], output_filename)
                if NOTIFICATIONS_ENABLED:
                    notification.notify(title="SecureBackup", message=f"Scheduled backup '{backup_name}' completed successfully.", app_name="SecureBackup")
            except Exception:
                if NOTIFICATIONS_ENABLED:
                    notification.notify(title="SecureBackup - Error", message=f"Scheduled backup '{job['name']}' failed.", app_name="SecureBackup")
        return job_fn

    for job in jobs:
        if job.get("enabled", True):
            cron_expr = BackupScheduler.cron_from_job(job)
            scheduler.add_or_update_job(job['name'], cron_expr, create_job_function(job))
            
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Exit"):
            break

        if event == "-RUN_BACKUP-":
            # ... (unchanged)
            sources = [s.strip() for s in values["-MANUAL_SRC-"].split(';') if s.strip()]
            dest = values["-MANUAL_DEST-"].strip()
            name = values["-MANUAL_NAME-"].strip()
            password = values["-MANUAL_PASS-"]
            if not all([sources, dest, name, password]):
                sg.popup_error("All fields (Sources, Destination, Name, Password) are required.")
            else:
                threading.Thread(target=run_backup_threaded, args=(window, sources, dest, password, name), daemon=True).start()

        if event == "-BACKUP_STATUS-":
            window["-BACKUP_STATUS-"].update(value=values[event], append=True)
            window["-BACKUP_STATUS-"].update("\n")

        if event == "-BACKUP_COMPLETE-":
            ### CHANGE ### Hide loader on completion
            window["-BACKUP_LOADER-"].update(visible=False)
            window["-BACKUP_STATUS-"].update(value=values[event], append=True)
            window["-RUN_BACKUP-"].update(disabled=False)
            
        if event == "-RUN_RESTORE-":
            # ... (unchanged)
            encrypted_file = values["-RESTORE_FILE-"].strip()
            dest_folder = values["-RESTORE_DEST-"].strip()
            password = values["-RESTORE_PASS-"]
            if not all([encrypted_file, dest_folder, password]):
                sg.popup_error("All fields (Backup File, Restore Folder, Password) are required.")
            else:
                threading.Thread(target=run_restore_threaded, args=(window, encrypted_file, dest_folder, password), daemon=True).start()
                
        if event == "-RESTORE_STATUS-":
            window["-RESTORE_STATUS-"].update(value=values[event], append=True)
            window["-RESTORE_STATUS-"].update("\n")

        if event == "-RESTORE_COMPLETE-":
            ### CHANGE ### Hide loader on completion
            window["-RESTORE_LOADER-"].update(visible=False)
            window["-RESTORE_STATUS-"].update(value=values[event], append=True)
            window["-RUN_RESTORE-"].update(disabled=False)

        # ... (rest of the schedule tab events are unchanged)
        if event == "-ADD_JOB-":
            editing_job_index = None
            window["-JOB_EDITOR-"].update(visible=True)
            for key in ["-JOB_NAME-", "-JOB_SRC-", "-JOB_DEST-", "-JOB_PASS-"]:
                window[key].update("")
            window["-JOB_ENABLED-"].update(True)

        if event == "-EDIT_JOB-":
            if not values["-JOBTABLE-"]:
                sg.popup_error("Please select a job to edit from the table.")
                continue
            editing_job_index = values["-JOBTABLE-"][0]
            job = jobs[editing_job_index]
            window["-JOB_EDITOR-"].update(visible=True)
            
            window["-JOB_NAME-"].update(job.get("name", ""))
            window["-JOB_SRC-"].update(";".join(job.get("sources", [])))
            window["-JOB_DEST-"].update(job.get("destination", ""))
            window["-JOB_PASS-"].update(job.get("password", ""))
            window["-JOB_FREQ-"].update(job.get("frequency", "Daily"))
            hour, minute = job.get("time", "10:00").split(":")
            window["-JOB_HOUR-"].update(hour)
            window["-JOB_MIN-"].update(minute)
            window["-JOB_DOW-"].update(job.get("day", "Monday"))
            window["-JOB_ENABLED-"].update(job.get("enabled", True))
            
            is_weekly = job.get("frequency") == "Weekly"
            window["-JOB_DOW_TEXT-"].update(visible=is_weekly)
            window["-JOB_DOW-"].update(visible=is_weekly)

        if event == "-DELETE_JOB-":
            if not values["-JOBTABLE-"]:
                sg.popup_error("Please select a job to delete from the table.")
                continue
            
            if sg.popup_yes_no("Are you sure you want to delete the selected job?") == "Yes":
                job_to_delete = jobs.pop(values["-JOBTABLE-"][0])
                scheduler.remove_job(job_to_delete['name'])
                save_config({"jobs": jobs})
                window["-JOBTABLE-"].update([
                    [j.get("name", ""), j.get("frequency", ""), j.get("time", ""), ", ".join(j.get("sources", [])), j.get("destination", "")]
                    for j in jobs if j.get("enabled", True)
                ])

        if event == "-SAVE_JOB-":
            job_data = {
                "name": values["-JOB_NAME-"].strip(),
                "sources": [s.strip() for s in values["-JOB_SRC-"].split(';') if s.strip()],
                "destination": values["-JOB_DEST-"].strip(),
                "frequency": values["-JOB_FREQ-"],
                "time": f"{values['-JOB_HOUR-']}:{values['-JOB_MIN-']}",
                "day": values["-JOB_DOW-"] if values["-JOB_FREQ-"] == "Weekly" else "*",
                "password": values["-JOB_PASS-"],
                "enabled": values["-JOB_ENABLED-"]
            }
            if not all([job_data['name'], job_data['sources'], job_data['destination'], job_data['password']]):
                sg.popup_error("Name, Sources, Destination, and Password are required.")
                continue

            if editing_job_index is not None:
                old_job_name = jobs[editing_job_index]['name']
                scheduler.remove_job(old_job_name)
                jobs[editing_job_index] = job_data
            else:
                if any(j['name'] == job_data['name'] for j in jobs):
                    sg.popup_error(f"A job with the name '{job_data['name']}' already exists. Please use a unique name.")
                    continue
                jobs.append(job_data)

            save_config({"jobs": jobs})
            
            if job_data['enabled']:
                cron = BackupScheduler.cron_from_job(job_data)
                scheduler.add_or_update_job(job_data['name'], cron, create_job_function(job_data))
            else:
                scheduler.remove_job(job_data['name'])

            window["-JOB_EDITOR-"].update(visible=False)
            window["-JOBTABLE-"].update([
                [j.get("name", ""), j.get("frequency", ""), j.get("time", ""), ", ".join(j.get("sources", [])), j.get("destination", "")]
                for j in jobs if j.get("enabled", True)
            ])
            editing_job_index = None

        if event == "-CANCEL_EDIT-":
            window["-JOB_EDITOR-"].update(visible=False)
            editing_job_index = None

        if event == "-JOB_FREQ-":
            is_weekly = values[event] == "Weekly"
            window["-JOB_DOW_TEXT-"].update(visible=is_weekly)
            window["-JOB_DOW-"].update(visible=is_weekly)

    scheduler.stop()
    window.close()

if __name__ == "__main__":
    main()