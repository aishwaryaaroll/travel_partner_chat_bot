# personal-info/ (local only)

This folder holds private configuration for your machine. Everything here except this README and `.gitkeep` is gitignored.

- `.env` holds `ANTHROPIC_API_KEY` and the other backend settings. The backend reads it at startup.
- See `backend/.env.example` for the list of variables. That file contains placeholders only.

If a key from this folder is ever committed or shared, **revoke it at https://console.anthropic.com/ and create a new one**. Deleting the file or the commit does not make the key safe again.
