# Email Attachment Extractor
---
A powerful cross-platform Python tool for extracting attachments from email accounts via IMAP. Supports Windows, Linux, and macOS with advanced filtering options including wildcard patterns.
---
## Features
- 🌐 **Cross-platform** compatibility (Windows, Linux, macOS)
- 📧 **Multiple** email provider support (Gmail, Outlook, iCloud, Yahoo, GMX, Web.de, custom IMAP)
- 📁 **Smart organization of attachments** by sender and/or date
- 🔍 **Advanced filtering** with wildcard pattern support
- 📊 **Comprehensive metadata** export (JSON format)
- 🎨 **Colored terminal output** for better readability
- 🔄 **Recursive mailbox processing** (process INBOX and all subfolders)
- ⚙️ **Configuration** file support for automation
- 🛡️ **Safe filename handling** across all platforms
## Installation
### Prerequisites
- Python 3.6 or higher
- pip (Python package installer)
#### Required Python Libraries
```bash
pip install imaplib email pathlib
```
**Note: Most required libraries are part of Python's standard library.**
---
## Quick Start 
### Interactive Mode
Simply run the script without arguments for interactive setup:
```bash
python email_attachment_extractor.py

```
### Command Line Mode
```bash
python email_attachment_extractor.py \
    --server imap.gmail.com \
    --username your.email@gmail.com \
    --save-path ./attachments \
    --organize-by-date \
    --file-types pdf docx xlsx
```
### Configuration File Mode
```bash
python email_attachment_extractor.py --config config.json
```
## Configuration File
Create a config.json file for automated extraction:
```json
{
  "server": "imap.gmail.com",
  "port": 993,
  "username": "your.email@gmail.com",
  "password": "your_app_password",
  "use_ssl": true,
  "mailbox": "INBOX",
  "search_criteria": "ALL",
  "organize_by_sender": false,
  "organize_by_date": true,
  "save_path": "/path/to/save/attachments",
  "limit": 100,
  "save_metadata": true,
  "allowed_extensions": ["pdf", "*.doc*", "*.xls*"],
  "excluded_extensions": ["exe", "bat", "*.tmp"]
}
```
## Wildcard Pattern Support
The tool supports Unix-style wildcard patterns for flexible file filtering:
Pattern Syntax
```bash
* - matches any number of characters
? - matches exactly one character
[seq] - matches any character in seq
[!seq] - matches any character not in seq
```
## Examples
### Allow All Files Except Dangerous
```json
{
  "allowed_extensions": ["*"],
  "excluded_extensions": ["exe", "bat", "sh", "dll", "scr"]
}
```
### Only Office Documents
```json
{
  "allowed_extensions": ["*.doc*", "*.xls*", "*.ppt*", "pdf"],
  "excluded_extensions": null
}
```
### Complex Pattern Matching
```json
{
  "allowed_extensions": [
    "report_*.pdf",      // PDFs starting with "report_"
    "invoice_*.pdf",     // PDFs starting with "invoice_"
    "IMG_*.jpg",         // JPEGs starting with "IMG_"
    "backup_20??.*",     // Backups from 2000-2099
    "data_*.csv"         // CSV files starting with "data_"
  ],
  "excluded_extensions": [
    "*_draft.*",         // All draft files
    "*_temp.*",          // All temporary files
    "~*",                // All backup files (starting with ~)
    "*.bak",             // All .bak files
    "test_*"             // All files starting with "test_"
  ]
}
```
## Command Line Options

| Option| Description| Example|
|-------|------------|--------|
| `--config, -c`| Path to JSON configuration file| `--config config.json`|
| `--server`             | IMAP server address                 | `--server imap.gmail.com`                  |
| `--port`               | IMAP port (default: 993)            | `--port 993`                               |
| `--username`           | Email address/username              | `--username user@example.com`              |
| `--password`           | Password (prompt if not provided)   | `--password mypassword`                    |
| `--save-path`          | Directory to save attachments       | `--save-path ./attachments`                |
| `--mailbox`            | Mailbox/folder to process           | `--mailbox INBOX`                          |
| `--search`             | IMAP search criteria                | `--search "SINCE 01-Jan-2024"`             |
| `--organize-by-sender` | Create folders by sender            | `--organize-by-sender`                     |
| `--organize-by-date`   | Create folders by date              | `--organize-by-date`                       |
| `--limit`              | Max emails to process               | `--limit 50`                               |
| `--recursive`          | Process all INBOX subfolders        | `--recursive`                              |
| `--limit-per-folder`.  | Max emails per folder (recursive)   | `--limit-per-folder 100`                   |
| `--total-limit`        | Total limit across all folders      | `--total-limit 500`                        |
| `--file-types`         | Allowed file extensions/patterns    | `--file-types pdf "*.doc*" "*.xls*"`       |
| `--exclude-types`      | Excluded file extensions/patterns   | `--exclude-types exe bat "*.tmp"`          |
| `--no-metadata`        | Don't save metadata JSON            | `--no-metadata`                            |

## IMAP Search Criteria
### Common IMAP search criteria for the search_criteria field:
- ALL - All messages (default)
- UNSEEN - Unread messages only
- SEEN - Read messages only
- SINCE 01-Jan-2024 - Messages since date
- BEFORE 31-Dec-2024 - Messages before date
- FROM "sender@example.com" - Messages from specific sender
- SUBJECT "Invoice" - Messages with subject containing text
- LARGER 1000000 - Messages larger than size (in bytes)
- OR UNSEEN FLAGGED - Unread OR flagged messages
- NOT DELETED - Non-deleted messages
### Output Structure
The tool creates an organized folder structure:

```
save_path/
├── INBOX/
│   ├── sender1@example.com/
│   │   ├── 2024-01-15/
│   │   │   ├── 2024-01-15_MSG001_Subject/
│   │   │   │   ├── 01_document.pdf
│   │   │   │   └── 02_image.jpg
│   │   │   └── 2024-01-15_MSG002_Another_Subject/
│   │   │       └── 01_report.xlsx
│   │   └── 2024-01-16/
│   │       └── ...
│   └── attachments_metadata_INBOX.json
├── INBOX_Subfolder/
│   └── ...
└── attachments_metadata_total.json
```

### Metadata Format
The tool saves detailed metadata in JSON format:
```json
{
  "extraction_date": "2024-01-15T10:30:00",
  "mailbox": "INBOX",
  "attachments": [
    {
      "filename": "01_document.pdf",
      "original_filename": "document.pdf",
      "filepath": "/path/to/file",
      "size_bytes": 1024000,
      "size_mb": 1.0,
      "sender": "sender@example.com",
      "subject": "Email Subject",
      "date": "2024-01-15T09:00:00",
      "email_id": "123",
      "message_id": "MSG001",
      "email_folder": "2024-01-15_MSG001_Subject",
      "attachment_number": 1
    }
  ]
}
```

## Provider-Specific Settings
### Gmail
- Enable 2-factor authentication
- Generate an app-specific password
- Use the app password instead of your regular password
### Outlook/Office 365
- Enable 2-factor authentication if required
- Use app password if 2FA is enabled
### iCloud
- Generate an app-specific password from Apple ID settings
- The tool handles iCloud's specific IMAP requirements automatically
## Security Notes
- Never commit passwords to version control
- Use app-specific passwords when available
- Store configuration files with passwords securely
- Consider using environment variables for sensitive data
- The tool uses SSL/TLS by default for secure connections
## Troubleshooting
### Common Issues
#### Authentication Failed
- Check username/password
- Use app-specific password for Gmail/iCloud
- Verify 2FA settings
#### No Attachments Found
- Check search criteria
- Verify mailbox selection
- Review allowed/excluded extensions
#### Connection Timeout
- Check server address and port
- Verify internet connection
- Check firewall settings
### Wildcard Patterns Not Working
- Ensure patterns are in quotes in command line
- Check JSON syntax in config file
- **Remember: exclusions always have priority**
### Debug Mode
Enable debug output by uncommenting line 14:

```python
imaplib.Debug = 4
```

## Examples
### Extract Only PDFs from Last 30 Days
```bash
python email_attachment_extractor.py \
    --config config.json \
    --search "SINCE 15-Dec-2024" \
    --file-types pdf
```
### Extract All Except Executables, Organize by Date
```bash
python email_attachment_extractor.py \
    --config config.json \
    --organize-by-date \
    --file-types "*" \
    --exclude-types exe bat sh dll
```
### Process All INBOX Folders Recursively
```bash
python email_attachment_extractor.py \
    --config config.json \
    --recursive \
    --limit-per-folder 100 \
    --total-limit 1000
```
### Extract Word and Excel Files with Specific Patterns
```json
{
  "allowed_extensions": [
    "report_*.doc*",
    "invoice_*.xls*",
    "data_20??_*.csv"
  ],
  "excluded_extensions": [
    "*_draft.*",
    "*_temp.*"
  ]
}
```
## License
This project is provided as-is for educational and personal use.
## Contributing
Contributions are welcome! Please feel free to submit issues or pull requests.
## Version
Version 1.0.1
<div align="center">
Made with ❤️ for efficient email attachment management
Star ⭐ this repository if you find it helpful!
</div>
