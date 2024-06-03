import requests
from bs4 import BeautifulSoup
import csv
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Get the base directory of the script
BASE_DIR = Path(__file__).resolve().parent

class AIROMedical:
    def get_headers(self):
        """
        Return headers for API requests.
        """
        return {
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'referer': 'https://airomedical.com/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        }

    def get_hospitals(self):
        """
        Generator function to fetch hospital data.
        """
        page = 1
        while True:
            params = {
                'page': str(page),
                'perPage': '100',
                'languageId': '1',
            }
            response = requests.get('https://api.airomedical.com/api/client/v1/hospitals', params=params, headers=self.get_headers())
            if response.status_code != 200:
                return
            for hospital in response.json()["data"]:
                country = hospital["country"]["name"]
                city = hospital["city"]["name"]
                streetNumber = hospital["addressStreetNumber"] or ""
                postalCode = hospital["addressPostalCode"] or ""
                addressRoute = hospital["addressRoute"] or ""
                address = f"{addressRoute}, {streetNumber}, {postalCode} {city}, {country}"
                while address.startswith(" ") or address.startswith(","):
                    address = address.lstrip().lstrip(",")
                yield {
                    "name": hospital["title"],
                    "address": address
                }
            page += 1

    def get_doctors(self):
        """
        Generator function to fetch doctor data.
        """
        page = 1
        while True:
            params = {
                'page': str(page),
                'perPage': '100',
                'languageId': '1',
            }
            response = requests.get('https://api.airomedical.com/api/client/v1/doctors', params=params, headers=self.get_headers())
            if response.status_code != 200:
                return
            yield [{
                "name": doctor["name"],
                "specialization": doctor["specialization"] or "",
                "startedWorkingIn": doctor["startedWorkingIn"] or "",
                "hospital": doctor["hospital"]["name"] if doctor.get("hospital") else "",
                "URL": f"https://airomedical.com/doctors/{doctor['urlSlug']}"
            } for doctor in response.json()["data"]]
            page += 1

    def doctor_detail(self, doctor):
        """
        Fetch additional details for a doctor.
        """
        URL = doctor["URL"]
        response = requests.get(URL, headers={
            "user-agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        })
        soup = BeautifulSoup(response.content, "html.parser")
        about = soup.select_one("div.AboutBlock_message__oiMr8")
        if about:
            about = about.text
        else:
            about = ""
        doctor["about"] = about
        doctor.pop('URL')
        return doctor

    def save_hospitals_to_csv(self):
        """
        Save hospitals data to a CSV file.
        """
        total = 0
        columns = (
            "name",
            "address"
        )
        with open(BASE_DIR / "hospitals.csv", "w", encoding="utf8") as f:
            writer = csv.DictWriter(f, columns, quotechar='"')
            writer.writeheader()
            for hospital in self.get_hospitals():
                writer.writerow(hospital)
                total += 1
                print("Total Hospitals Scraped:", total)

    def save_doctors_to_csv(self):
        """
        Save doctors data to a CSV file.
        """
        total = 0
        columns = (
            "name",
            "specialization",
            "startedWorkingIn",
            "hospital",
            "about",
        )
        with open(BASE_DIR / "doctors.csv", "w", encoding="utf8") as f:
            writer = csv.DictWriter(f, columns, quotechar='"')
            writer.writeheader()
            with ThreadPoolExecutor(max_workers=10) as executor:
                for doctors in self.get_doctors():
                    for doctor in executor.map(self.doctor_detail, doctors):
                        writer.writerow(doctor)
                        total += 1
                        print("Total Doctors Scraped:", total)

