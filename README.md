# twrapper: Supertuxkart server websocket wrapper

This is a simple Python websocket server that lets you start SuperTuxKart servers via a websocket connection, using an XML configuration file. The server reads settings from `config.json` and launches processes on request.

## Features
- Start SuperTuxKart servers via WebSocket requests
- Automatic logging of server output (can be disabled)
- Automatically stops servers after a set time

## Requirements
- Python 3.7+
- See `requirements.txt` for required Python packages

## Installation
1. Create a virtual environment: python3 -m venv venv, and activate it afterwards: source venv/bin/activate
2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Make sure you have a valid `config.json` with the correct paths and settings. (Use config.json.example as an example)

## Usage
Start the server with:
```bash
python twrapper.py
```

The server listens on the address and port specified in `config.json`. You can send a JSON request via a websocket client to start a server:

```json
{
  "action": "start_server",
  "params": {
    "xml_path": "/path/to/config.xml",
    "duration": 2,  // in hours
    "log_path": "/path/to/logfile.log",
    "name": "optional_name"
  }
}
```

The server responds with a JSON object containing the status and process ID.

## Notes
- Make sure the paths in `config.json` are correct and you have permission to start processes.
- Logging can be disabled via the `no_logging` option in `config.json`.

## License
This project is licensed under the MIT License see the [LICENSE](LICENSE) file for details.
