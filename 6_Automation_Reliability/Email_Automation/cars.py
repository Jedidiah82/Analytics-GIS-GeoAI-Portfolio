#!/usr/bin/env python3
import json
import sys
import reports
import emails

def load_data(filename):
    with open(filename) as f:
        return json.load(f)

def format_car(car):
    return f"{car['car_make']} {car['car_model']} ({car['car_year']})"

def process_data(data):
    max_revenue = 0
    max_sales = 0
    year_sales = {}

    for item in data:
        price = float(item["price"].strip("$"))
        revenue = price * item["total_sales"]

        if revenue > max_revenue:
            max_revenue = revenue
            best_car = item

        if item["total_sales"] > max_sales:
            max_sales = item["total_sales"]
            top_seller = item

        year = item["car"]["car_year"]
        year_sales[year] = year_sales.get(year, 0) + item["total_sales"]

    popular_year = max(year_sales, key=year_sales.get)

    return [
        f"The {format_car(best_car['car'])} generated the most revenue: ${max_revenue:.2f}",
        f"The {format_car(top_seller['car'])} had the most sales: {top_seller['total_sales']}",
        f"The most popular year was {popular_year} with {year_sales[popular_year]} sales."
    ]

def cars_dict_to_table(data):
    table = [["ID", "Car", "Price", "Total Sales"]]
    sorted_data = sorted(data, key=lambda x: x["total_sales"], reverse=True)

    for item in sorted_data:
        table.append([
            item["id"],
            format_car(item["car"]),
            item["price"],
            item["total_sales"]
        ])
    return table

def main():
    data = load_data("car_sales.json")
    summary = process_data(data)

    reports.generate(
        "/tmp/cars.pdf",
        "Sales summary for last month",
        "<br/>".join(summary),
        cars_dict_to_table(data)
    )

    message = emails.generate(
        "automation@example.com",
        "student@example.com",
        "Sales summary for last month",
        "\n".join(summary),
        "/tmp/cars.pdf"
    )

    emails.send(message)

if __name__ == "__main__":
    main()
