import os
import json
from log import logger

import requests
from datetime import date
from fuzzywuzzy import fuzz

SIMPLIFY_LOGO = "https://simplify.jobs/images/logos/logo.svg"

# data schema: {"company", "company_description", "location", "position", "site_link", "simplify_link", "status"}

def create_md_table(listings):
    col_names = ["Company", "Company Bio",
                 "Location", "Title", "Link", "Status"]
    col_keys = ["company", "company_desciption",
                "location", "position"]
    result = "| "
    for name in col_names:
        result += name + " | "
    result += "\n| "
    for name in col_names:
        result += " --- | "
    for listing in listings:
        result += "\n| "
        link = listing["site_link"]
        for key in col_keys:
            result += listing[key] + " | "
        result += f" [![Simplify Link]({SIMPLIFY_LOGO})]({link}) [Link]({link}) |"
        if not listing["is_closed"]:
            result += "✅ |"
        else:
            result += "🚫 |"
    return result


def remove_links(string: str):
    links = {}
    while True:
        bracket_open = string.find("[")
        bracket_closed = string.find("]", bracket_open)
        paren_open = string.find("(", bracket_closed)
        paren_closed = string.find(")", paren_open)
        if (bracket_open == -1 or bracket_closed == -1 or paren_open == -1 or paren_closed == -1):
            break
        text = string[bracket_open+1:bracket_closed]
        link = string[paren_open+1:paren_closed]
        links[text] = link
        string = string[:bracket_open] + text + string[paren_closed+1:]

    return string, links


def convert_file(listings: list, path: str, year: int, is_closed: bool, is_off_season: bool):
    with open(path, "r") as f:
        table_line_num = 0
        for line in f.readlines():
            if line[0] == "|":
                data = {}
                if table_line_num == 0:
                    header = [t.strip(" ") for t in line.split('|')[1:-1]]
                elif table_line_num > 1:
                    stripped_line, links = remove_links(line)
                    values = [t.strip()
                              for t in stripped_line.split('|')[1:-1]]
                    job_is_closed = False
                    for col, value in zip(header, values):
                        data[col.lower()] = value
                        if value.find("Closed") != -1:
                            job_is_closed = True
                            start = value.find("**")
                            data[col] = value[0:start] + \
                                value[value.find("**", start + 1) + 2:]
                    data["is_closed"] = is_closed or job_is_closed
                    data["year"] = year
                    data["is_off_season"] = is_off_season
                    data["company_desciption"] = "Not Implemented"
                    if "date_posted" not in data:
                        data["date_posted"] = date.today().strftime("%b %d, %Y")
                    for text, link in links.items():
                        if len(links) == 1 or text != values[0]:
                            listing = dict(data)
                            listing["site_link"] = link
                            listing["title"] = text if len(
                                links) > 1 else listing["notes"]
                            listings.append(listing)

                table_line_num += 1

def parse_file(listings: list, path: str, year: int, is_closed: bool, is_off_season: bool):
    with open(path, "r") as f:
        table_line_num = 0
        for line in f.readlines():
            if line[0] == "|":
                data = {}
                if table_line_num == 0:
                    header = [t.strip(" ") for t in line.split('|')[1:-1]]
                elif table_line_num > 1:
                    stripped_line, links = remove_links(line)
                    values = [t.strip()
                              for t in stripped_line.split('|')[1:-1]]
                    job_is_closed = False
                    for col, value in zip(header, values):
                        data[col.lower()] = value
                        if value.find("Closed") != -1:
                            job_is_closed = True
                            start = value.find("**")
                            data[col] = value[0:start] + \
                                value[value.find("**", start + 1) + 2:]
                    data["is_closed"] = is_closed or job_is_closed
                    data["year"] = year
                    data["is_off_season"] = is_off_season
                    data["company_desciption"] = "Not Implemented"
                    if "date_posted" not in data:
                        data["date_posted"] = date.today().strftime("%b %d, %Y")
                    for text, link in links.items():
                        if len(links) == 1 or text != values[0]:
                            listing = dict(data)
                            listing["site_link"] = link
                            listing["title"] = text if len(
                                links) > 1 else listing["notes"]
                            listings.append(listing)

                table_line_num += 1

def findListing(listings, listing, threshold=90):
    for l in listings:
        title_similarity = fuzz.token_set_ratio(l["title"], listing["title"])
        if listing["name"].lower() == l["name"].lower() and title_similarity >= threshold:
            return l
    return None


def updateListings(listingsJSON, listingsMD, listingsSimplify):
    addedListings = []
    for listing in listingsMD + listingsSimplify:
        listingJSON = findListing(listingsJSON, listing)
        if not listingJSON:
            addedListings.append(listing)
            continue
        # print(listing["title"], listingJSON["title"])
        for key, value in listing.items():
            listingJSON[key] = value
    print(addedListings)


def getListingsFromSimplify():
    return []


def getListingsFromMarkDown():
    result = []
    parse_file(result, "README.md", 2024, False, False)
    parse_file(result, "README-Off-Season.md", 2024, False, True)
    parse_file(result, "README-2023.md", 2023, True, False)
    return result


def getListingsFromJSON():
    with open("simplify/listings.json") as f:
        listings = json.load(f)
        return listings


def exportJSON(listings):
    text_file = open("simplify/listings.json", "w")
    n = text_file.write(json.dumps(listings, indent=4))
    text_file.close()


def exportTable(result):
    text_file = open("TABLE.md", "w")
    summer_listings = list(filter(
        lambda x: not x["is_closed"] and not x["is_off_season"] and x["year"] == 2024, result))
    n = text_file.write(create_md_table(summer_listings))
    text_file.close()


def main():
    # logger.info(f"Running main() in main.py")
    listingsJSON = getListingsFromJSON()
    listingsMD = getListingsFromMarkDown()
    listingsSimplify = getListingsFromSimplify()

    updateListings(listingsJSON, listingsMD, listingsSimplify)

    exportJSON(listingsJSON)
    exportTable(listingsJSON)


if __name__ == "__main__":
    main()
