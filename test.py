import requests

API_KEY = "45b71991-ad6b-421d-a85b-b5783145d382"

resp = requests.get(
    "https://www.biodiversitylibrary.org/api2/httpquery.ashx",
    params={
        "op": "GetTitleSearchSimple",
        "title": "Haeckel",
        "apikey": API_KEY,
        "format": "json",
    },
)

print("Status:", resp.status_code)
print("Body:", resp.text[:500])
