# 🔒 SecureBackup

SecureBackup is a desktop application for Windows that allows you to create secure, encrypted backups of your important files and folders. It features a simple user interface for manual backups, restores, and scheduling automated backup jobs.

## Features

-   **AES-256-GCM Encryption:** Strong, authenticated encryption for all backup files.
-   **High-Speed Compression:** Uses the modern Tar + LZ4 combination for very fast archiving of large folders.
-   **Manual Backups:** Easily run a one-off backup at any time.
-   **Restore Functionality:** Decrypt and restore your files to any location.
-   **Scheduled Jobs:** Set up daily or weekly automated backup jobs.
-   **Desktop Notifications:** Get notified when a backup job is complete.

## How to Use the Application

1.  Go to the [Releases page](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME/releases).
2.  Download the `SecureBackup.exe` file from the latest release.
3.  Run the `SecureBackup.exe` file. No installation is needed!

## For Developers: Running from Source

If you want to run the application from the source code, follow these steps:

1.  Clone the repository: `git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git`
2.  Navigate into the project directory: `cd YOUR_REPOSITORY_NAME`
3.  Create a virtual environment: `python -m venv .venv`
4.  Activate it: `.\.venv\Scripts\Activate.ps1`
5.  Install the required packages: `pip install -r requirements.txt`
6.  Run the application: `python main.py`