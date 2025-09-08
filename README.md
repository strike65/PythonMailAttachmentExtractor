# Email Attachment Extractor v1.0

A cross-platform Python tool for extracting email attachments from IMAP mailboxes. Supports recursive folder processing, intelligent organization, and works on Windows, Linux, and macOS.

## Features

- 📧 **IMAP Support**: Connect to any IMAP email server (Gmail, Outlook, iCloud, Yahoo, etc.)
- 🔄 **Recursive Processing**: Process INBOX and all subfolders automatically
- 📁 **Smart Organization**: Organize attachments by date, sender, or both
- 🎨 **Colored Terminal Output**: Clear visual feedback with color-coded messages
- 💾 **Metadata Tracking**: Save detailed JSON metadata about extracted attachments
- 🔐 **Secure**: Supports SSL/TLS connections
- 🖥️ **Cross-Platform**: Works on Windows, Linux, and macOS

## Requirements

- Python 3.7 or higher
- No external dependencies (uses only Python standard library)

## Installation

1. Clone or download the script:
```bash
git clone https://github.com/yourusername/email-attachment-extractor.git
cd email-attachment-extractor
```

2. Make the script executable (Linux/macOS):
```bash
chmod +x email_extractor.py
```

## Quick Start

### Interactive Mode
Simply run the script without arguments for guided setup:
```bash
python3 email_extractor.py
```

### With Configuration File
Create a configuration file and run:
```bash
python3 email_extractor.py --config config.json
```

### Command Line Arguments
```bash
python3 email_extractor.py --server imap.gmail.com --username your@email.com --recursive
```

## Configuration File Format

Create a `config.json` file with your email settings:

```json
{
    "server": "imap.gmail.com",
    "port": 993,
    "username": "your.email@gmail.com",
    "password": "your-app-password",
    "use_ssl": true,
    "mailbox": "INBOX",
    "search_criteria": "ALL",
    "organize_by_sender": false,
    "organize_by_date": true,
    "save_path": "/path/to/save/attachments",
    "recursive": true,
    "limit_per_folder": 100,
    "total_limit": 1000,
    "save_metadata": true
}
```

**Note**: For security, consider omitting the password from the config file. The script will prompt for it.

## Command Line Options

| Option | Description |
|--------|-------------|
| `--config FILE` | Load configuration from JSON file |
| `--server SERVER` | IMAP server address |
| `--port PORT` | IMAP port (default: 993) |
| `--username EMAIL` | Email address/username |
| `--password PASS` | Password (not recommended in CLI) |
| `--save-path PATH` | Directory to save attachments |
| `--mailbox FOLDER` | Specific mailbox to process (default: INBOX) |
| `--search CRITERIA` | IMAP search criteria (default: ALL) |
| `--organize-by-sender` | Create folders organized by sender |
| `--organize-by-date` | Create folders organized by date |
| `--recursive` | Process all INBOX subfolders |
| `--limit N` | Maximum emails to process |
| `--limit-per-folder N` | Maximum emails per folder (recursive mode) |
| `--total-limit N` | Total limit across all folders |
| `--no-metadata` | Don't save metadata JSON files |

## IMAP Search Criteria Examples

- `ALL` - All emails
- `UNSEEN` - Unread emails only
- `FROM "sender@email.com"` - Emails from specific sender
- `SINCE 1-Jan-2024` - Emails since specific date
- `SUBJECT "Invoice"` - Emails with specific subject
- `LARGER 1000000` - Emails with attachments larger than 1MB

## Provider-Specific Setup

### Gmail
1. Enable 2-factor authentication
2. Generate an app-specific password: https://myaccount.google.com/apppasswords
3. Use the app password instead of your regular password

### Outlook/Office 365
1. If using 2FA, generate an app password
2. Server: `outlook.office365.com`

### iCloud
1. Generate an app-specific password: https://appleid.apple.com/account/manage
2. Server: `imap.mail.me.com`

## Output Structure

The script creates the following folder structure:

```
save_path/
├── INBOX/
│   └── 2024-12-15/
│       └── 2024-12-15_MessageID_Subject/
│           ├── 01_attachment1.pdf
│           └── 02_attachment2.docx
├── INBOX_subfolder/
│   └── 2024-12-14/
│       └── 2024-12-14_MessageID_Subject/
│           └── 01_document.xlsx
└── attachments_metadata_total.json
```

### File Naming Convention
- Each email gets its own folder: `YYYY-MM-DD_MessageID_Subject/`
- Attachments are numbered: `01_filename.ext`, `02_filename.ext`
- Metadata JSON files track all extracted attachments

## Examples

### Extract all attachments from Gmail
```bash
python3 email_extractor.py \
    --server imap.gmail.com \
    --username your@gmail.com \
    --recursive \
    --organize-by-date
```

### Process only unread emails with attachments
```bash
python3 email_extractor.py \
    --config config.json \
    --search "UNSEEN" \
    --save-path /Volumes/Backup/EmailAttachments
```

### Extract from specific sender with limit
```bash
python3 email_extractor.py \
    --config config.json \
    --search 'FROM "client@company.com"' \
    --limit 50
```

### Process specific mailbox folder
```bash
python3 email_extractor.py \
    --config config.json \
    --mailbox "INBOX/Projects" \
    --organize-by-sender
```

## Color Output Guide

The script uses colored terminal output for better readability:
- **Cyan**: Information and progress messages
- **Green**: Success messages
- **Yellow**: Warnings
- **Red**: Errors

## Security Considerations

1. **Never commit passwords**: Don't include passwords in config files that will be version controlled
2. **Use app-specific passwords**: Most providers support app passwords for better security
3. **File permissions**: Ensure config files with passwords have restricted permissions:
   ```bash
   chmod 600 config.json
   ```
4. **Use environment variables**: Consider storing passwords in environment variables:
   ```bash
   export EMAIL_PASSWORD="your-password"
   ```

## Troubleshooting

### Connection Issues
- Verify server address and port
- Check if your email provider requires app-specific passwords
- Ensure IMAP is enabled in your email settings
- Check firewall/antivirus settings

### No Attachments Found
- Verify the search criteria matches your emails
- Check if emails actually have attachments (not inline images)
- Try with `--search "ALL"` first to test

### Permission Errors
- Ensure you have write permissions to the save path
- On Windows, run as administrator if saving to system directories
- Check disk space availability

### Memory Issues with Large Mailboxes
- Use `--limit` to process emails in batches
- Use `--limit-per-folder` in recursive mode
- Process specific date ranges with `--search "SINCE date BEFORE date"`

## Metadata Format

The script saves metadata in JSON format with the following structure:

```json
{
    "extraction_date": "2024-12-15T10:30:00",
    "processed_folders": ["INBOX", "INBOX/Subfolder"],
    "statistics": {
        "emails_processed": 150,
        "attachments_saved": 423,
        "total_size_mb": 1250.5,
        "errors": []
    },
    "attachments": [
        {
            "filename": "01_document.pdf",
            "original_filename": "document.pdf",
            "filepath": "/path/to/file",
            "size_mb": 2.5,
            "sender": "sender@email.com",
            "subject": "Email Subject",
            "date": "2024-12-15T09:00:00",
            "message_id": "ABC123"
        }
    ]
}
```

## License

MIT License - feel free to modify and distribute as needed.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## Version History

- **v1.0** (2024-12-15): Initial release
  - Cross-platform support (Windows, Linux, macOS)
  - Recursive folder processing
  - Colored terminal output
  - Comprehensive metadata tracking
  - Multiple organization options

## Support

For issues, questions, or suggestions, please open an issue on GitHub or contact the maintainer.
