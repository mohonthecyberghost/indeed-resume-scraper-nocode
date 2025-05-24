# Indeed Resume Scraper

A no-code-friendly scraper for Indeed Resume that collects candidate information and resumes based on customizable search filters.

## Features

- 🔍 Dynamic search filters (keywords, location, experience, education)
- 📝 Extracts candidate information (name, email, phone)
- 📄 Downloads and processes resumes (PDF/HTML)
- 📊 Exports data to CSV/Google Sheets
- ☁️ Uploads resumes to Google Drive
- 🤖 Runs headlessly via Make.com or n8n

## Quick Start

1. **Setup Environment**
   ```bash
   # Clone the repository
   git clone https://github.com/yourusername/indeed-resume-scraper-nocode.git
   cd indeed-resume-scraper-nocode

   # Install dependencies
   pip install -r requirements.txt

   # Set up environment variables
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Configure Credentials**
   - Add your Indeed credentials to `.env`
   - Set up Google API credentials for Drive/Sheets integration

3. **Run the Scraper**
   ```bash
   # Start the webhook server
   python src/webhook_server.py
   ```

4. **Make.com Integration**
   - Create a new scenario
   - Add HTTP request module
   - Configure with your webhook URL
   - Set up the request body with search parameters

## Search Parameters

```json
{
    "keywords": "Python developer",
    "location": "New York, NY",
    "experience_years": 5,
    "education": "Bachelor's Degree",
    "output_format": "csv",  // or "google_sheets"
    "storage": "google_drive"  // or "s3"
}
```

## Output Format

The scraper generates:
1. CSV/Google Sheet with candidate information
2. Downloaded resumes in PDF format
3. Uploaded files to Google Drive/S3

## Security Notes

- Never commit your `.env` file
- Use environment variables for sensitive data
- Implement rate limiting in production

## Support

For issues and feature requests, please open a GitHub issue.

## License

MIT License - See LICENSE file for details
