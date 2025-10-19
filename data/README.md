
# Data folder

This folder contains the provided assignment datasets (CSV) used to seed the databases.

| Original file name          | Normalized name | Used by service       |
|----------------------------|-----------------|-----------------------|
| customers food.csv         | customers.csv   | customer-service      |
| addresses.csv              | addresses.csv   | customer-service      |
| restaurants.csv            | restaurants.csv | restaurant-service    |
| menu_items.csv             | menu_items.csv  | restaurant-service    |
| orders.csv                 | orders.csv      | order-service         |
| order_items.csv            | order_items.csv | order-service         |
| payments.csv               | payments.csv    | payment-service       |
| drivers.csv                | drivers.csv     | delivery-service      |
| deliveries.csv             | deliveries.csv  | delivery-service      |

**Notes**

- Date/time columns are parsed from typical forms like `DD/MM/YY HH:MM` or `DD/MM/YYYY HH:MM`.
- Booleans in `is_open` and `is_available` are respected as-is.
