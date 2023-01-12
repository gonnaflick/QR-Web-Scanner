# QR-Web-Scanner
A Python application that scans QR information from cards and auto fills the information in a web based access registry.
## Limitations
This application only works with chromium based browsers. This application is not complete, and only fills one value in the form.
## Installing requirements
1. Install the required dependencies:
```
$ pip install -r requirements.txt
```
1. Modify the `qr-scanner.py` values for both the XPATH and URL.
2. Make sure you have a camera connected and run the code:
```
$ python3 qr-scanner.py
```
