# Storage Directory

This directory contains runtime data for the AI4SupplyChain application.

## 📁 Directory Structure

```
storage/
├── database/           # Database files
│   └── inventory.db    # Main SQLite database (created at runtime)
├── uploads/           # User uploaded files
│   ├── documents/     # OCR documents (PDFs, images)
│   └── imports/       # CSV/Excel files for bulk import
├── exports/           # Generated reports and exports
│   ├── reports/       # Inventory reports, analytics
│   ├── forecasts/     # Forecast results
│   └── backups/       # Database backups
├── sample_data/       # Sample/test data files
│   ├── products.csv   # Sample product data
│   ├── suppliers.csv  # Sample supplier data
│   ├── transactions.csv # Sample transaction data
│   └── locations.csv  # Sample location data
└── logs/             # Application logs
    ├── app.log        # Main application log
    ├── ai_agent.log   # AI agent interactions
    └── api.log        # API request logs
```

## 🔐 Security & Privacy

- **Database files**: Contain sensitive business data
- **Upload files**: May contain confidential documents
- **Logs**: May contain user queries and system information

## 📋 Maintenance

- **Backups**: Regularly backup the `database/` folder
- **Cleanup**: Periodically clean old files from `uploads/` and `exports/`
- **Monitoring**: Check `logs/` for errors and performance issues

## 🚫 Git Ignore

Most files in this directory should NOT be committed to version control:
- Database files (contain sensitive data)
- User uploads (privacy and size concerns)
- Generated exports (temporary files)
- Log files (contain runtime information)

Only structural files like this README and sample data should be versioned.
