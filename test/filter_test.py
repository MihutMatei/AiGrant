from filter.filter import filter


funds = [
    {
        "metadata": {"name": "Fondul pentru saraci", "url": "https://fonduri.ro"},
        "requirements": {
            "caen": [6025, 6022, 5031],
            "employees": {"min": 3, "max": 7},
            "city": "Bucharest",
        },
    },
    {
        "metadata": {"name": "Fonduri Europene", "url": "https://dwdw.com"},
        "requirements": {"caen": [6022, 4321], "employees": 5, "city": "Ploiesti"},
    },
    {
        "metadata": {"name": "Fonduri Europene", "url": "https://dwjidw.com"},
        "requirements": {
            "caen": 4092,
            "employees": {"min": 7, "max": 8},
            "city": "Bucharest",
        },
    },
]

company = {"caen": [6025, 4092, 4321], "employees": 5, "city": "Bucharest"}

eligibility = filter(company, funds)
print(eligibility)
