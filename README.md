# Email Attachment Extractor

**A powerful, modular Python application** for extracting attachments from email accounts via IMAP. Features advanced wildcard filtering, cross-platform support, and a clean modular architecture.

## ✨ Features

- 🌐 **Cross-platform compatibility** (Windows, Linux, macOS)
- 📧 **15+ Email providers supported** (Gmail, Outlook, iCloud, Yahoo, etc.)
- 🎯 **Advanced wildcard filtering** for file types
- 📁 **Smart organization** by sender and/or date
- 🔄 **Recursive folder processing** for complete mailbox extraction
- 🎨 **Colored terminal output** for better readability
- 📊 **Comprehensive metadata** export in JSON format
- 🏗️ **Clean modular architecture** for easy maintenance and extension

## 📦 Installation

### **Prerequisites**
- Python 3.6 or higher
- No external dependencies required (uses Python standard library)

### **Quick Setup**

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/email-attachment-extractor.git
cd email-attachment-extractor
```

2. **Optional: Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. **Install optional dependencies:**
```bash
pip install -r requirements.txt
```

## 🚀 Quick Start

### **Interactive Mode**
Run without arguments for guided setup:
```bash
python main.py
```

### **Configuration File Mode** *(Recommended)*
```bash
python main.py --config config.json
```

### **Command Line Mode**
```bash
python main.py \
    --server imap.gmail.com \
    --username your.email@gmail.com \
    --save-path ./attachments \
    --organize-by-date \
    --file-types pdf docx xlsx
```

## ⚙️ Configuration

### **Sample config.json**
```json
{
  "server": "imap.gmail.com",
  "port": 993,
  "username": "your.email@gmail.com",
  "password": null,
  "use_ssl": true,
  "mailbox": "INBOX",
  "search_criteria": "ALL",
  "organize_by_sender": false,
  "organize_by_date": true,
  "save_path": "./attachments",
  "limit": 100,
  "save_metadata": true,
  "allowed_extensions": ["pdf", "*.doc*", "*.xls*"],
  "excluded_extensions": ["exe", "bat", "*.tmp"],
  "recursive": false
}
```

> ⚠️ **Important:** Field names are case-sensitive. Use `excluded_extensions` (plural), not `excluded_extension`!

## 🎯 Wildcard Pattern Support

### **Pattern Syntax**

| Pattern | Description | Example |
|---------|-------------|---------|
| `*` | Matches any characters | `*.pdf` matches all PDFs |
| `?` | Matches single character | `doc?.pdf` matches `doc1.pdf` |
| `[seq]` | Matches any char in seq | `file[123].txt` matches `file1.txt` |
| `[!seq]` | Matches any char NOT in seq | `file[!0-9].txt` matches `fileA.txt` |

### **Common Use Cases**

```json
{
  "allowed_extensions": ["*"],
  "excluded_extensions": ["exe", "bat", "dll", "scr"]
}
```
*Allow all files except potentially dangerous ones*

```json
{
  "allowed_extensions": ["*.doc*", "*.xls*", "*.ppt*", "pdf"]
}
```
*Only office documents*

```json
{
  "allowed_extensions": ["report_*.pdf", "invoice_*.pdf", "IMG_*.jpg"]
}
```
*Specific naming patterns*

> 💡 **Tip:** Exclusions ALWAYS have priority over allowed patterns!

## 📋 Command Line Options

| Option | Description |
|--------|-------------|
| `--config FILE` | Path to JSON configuration file |
| `--server HOST` | IMAP server address |
| `--port PORT` | IMAP port (default: 993) |
| `--username USER` | Email address/username |
| `--password PASS` | Password (prompts if not provided) |
| `--save-path PATH` | Directory to save attachments |
| `--mailbox FOLDER` | Mailbox to process (default: INBOX) |
| `--search CRITERIA` | IMAP search criteria |
| `--organize-by-sender` | Create folders by sender |
| `--organize-by-date` | Create folders by date |
| `--recursive` | Process all INBOX subfolders |
| `--limit N` | Max emails to process |
| `--file-types PATTERN...` | Allowed file patterns |
| `--exclude-types PATTERN...` | Excluded file patterns |
| `--no-metadata` | Don't save metadata JSON |
| `--debug` | Enable debug output |
| `--version` | Show version |

## 📁 Project Structure

```
email_attachment_extractor/
├── main.py                     # Main entry point
├── config.json.example         # Example configuration
├── requirements.txt            # Optional dependencies
├── README.md                   # This file
├── src/
│   ├── core/                  # Core functionality
│   │   ├── extractor.py       # Main extractor class
│   │   ├── email_processor.py # Email parsing & attachments
│   │   └── pattern_matcher.py # Wildcard pattern matching
│   ├── utils/                 # Utility modules
│   │   ├── colors.py          # Terminal colors
│   │   ├── filesystem.py      # File operations
│   │   └── config_loader.py   # Configuration handling
│   ├── providers/             # Email providers
│   │   └── email_providers.py # Provider configurations
│   └── cli/                   # Command-line interface
│       ├── argparser.py       # Argument parsing
│       └── interactive.py     # Interactive setup
└── tests/                     # Unit tests
```

## 📧 Supported Email Providers

The application includes pre-configured settings for:

- **Gmail** - Requires app-specific password
- **Outlook/Office 365** - Standard IMAP support
- **iCloud** - Special handling included
- **Yahoo Mail** - May need app password
- **ProtonMail** - Via ProtonMail Bridge
- **FastMail, Zoho, GMX, Web.de** - And many more!

### **Provider-Specific Notes**

**Gmail:**
1. Enable 2-factor authentication
2. Generate app-specific password
3. Use app password instead of regular password

**iCloud:**
1. Generate app-specific password from Apple ID settings
2. Automatic special handling for iCloud quirks

## 📁 Output Structure

```
attachments/
├── INBOX/
│   ├── sender@example.com/
│   │   ├── 2024-01-15/
│   │   │   ├── 2024-01-15_MSG001_Subject/
│   │   │   │   ├── 01_document.pdf
│   │   │   │   └── 02_image.jpg
│   │   │   └── attachments_metadata.json
│   │   └── 2024-01-16/
│   └── another@example.com/
└── attachments_metadata_total.json
```

## 🔍 IMAP Search Criteria

| Criteria | Description |
|----------|-------------|
| `ALL` | All messages (default) |
| `UNSEEN` | Unread messages only |
| `SINCE 01-Jan-2024` | Messages since date |
| `FROM sender@example.com` | From specific sender |
| `SUBJECT "Invoice"` | Subject contains text |
| `LARGER 1000000` | Larger than size (bytes) |

## 💡 Examples

### **Extract PDFs from last 30 days:**
```bash
python main.py --config config.json \
    --search "SINCE 01-Dec-2024" \
    --file-types pdf
```

### **Process all folders recursively:**
```bash
python main.py --config config.json \
    --recursive \
    --limit-per-folder 100
```

### **Extract everything except executables:**
```bash
python main.py --config config.json \
    --file-types "*" \
    --exclude-types exe bat sh dll
```

## 🛠️ Development

### **Running Tests:**
```bash
pytest tests/
```

### **Code Style:**
```bash
black src/
pylint src/
```

### **Type Checking:**
```bash
mypy src/
```

## 🔒 Security Notes

- **Never commit passwords** to version control
- Use **app-specific passwords** when available
- Store config files **securely**
- Consider **environment variables** for credentials
- SSL/TLS enabled by default

## 🐛 Troubleshooting

### **Authentication Failed**
- Verify username/password
- Use app-specific password for Gmail/iCloud
- Check 2FA settings

### **No Attachments Found**
- Check search criteria
- Verify allowed/excluded patterns
- Ensure mailbox exists

### **Import Errors**
- Ensure you're running from project root
- Check Python version (3.6+)
- Verify all module files exist

### **Debug Mode**
Enable detailed output:
```bash
python main.py --config config.json --debug
```

## 📜 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📌 Version

**Version 2.0.0** - Modular Architecture with Wildcard Support

## 👤 Author

strike

---

<div align="center">

*Star ⭐ this repository if you find it helpful!*

</div>