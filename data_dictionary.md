# Data Dictionary: Synthetic Warehouse Orders

> **IMPORTANT: This is SYNTHETIC (hypothetical) data.** It was created by `generate_dataset.py` for an academic project at IILM University. It is not from any real company. Every pattern in it comes from the assumptions listed below.

## Files

| File | Rows | Purpose |
|---|---|---|
| `warehouse_orders_raw.csv` | 2,025 | Messy "system export" with deliberate errors (used for the cleaning demonstration) |
| `warehouse_orders.csv` | 2,000 | **Clean master dataset. Used by Python, Power BI, the AI assistant and n8n** |
| `warehouse_orders_sample.csv` | 20 | Small hand-picked sample showing every situation (on time, each delay stage, cancelled, in transit) |
| `generate_dataset.py` | n/a | The script that creates all of the above (seed 42, so results are repeatable) |

## Scenario (hypothetical)

An e-commerce warehouse near Delhi NCR ships to customers across India. Data covers **1 Sep to 31 Oct 2026**, with a hypothetical **festive sale week (15-21 Oct)** when order volume rises sharply. The data was "exported" on 3 Nov 2026.

## Order journey

Receiving → Inventory Verification → Picking → Packing → Dispatch → Delivery

## Columns (24)

| # | Column | Meaning | Values / unit |
|---|---|---|---|
| 1 | Order_ID | Unique order number | ORD-100001 to ORD-102000 |
| 2 | Order_Date | Date the order was placed | YYYY-MM-DD |
| 3 | Order_Hour | Hour of day the order arrived | 0-23 |
| 4 | Shift | Warehouse shift at that hour | Morning (6-14), Evening (14-22), Night (22-6) |
| 5 | Customer_Location | Delivery city | 20 Indian cities |
| 6 | Delivery_Zone | Type of destination | Metro, Tier-2, Remote |
| 7 | Product_Category | Type of product | 8 categories |
| 8 | Order_Priority | Delivery promise level | Express, Standard, Economy |
| 9 | Order_Quantity | Units in the order | 1-6 |
| 10 | Inventory_Status | Stock position when order was checked | Available, Low Stock, Out of Stock |
| 11 | Receiving_Time_Minutes | Time to receive and verify the order | minutes |
| 12 | Inventory_Check_Time_Minutes | Stock check time, **including waiting for replenishment** if out of stock | minutes |
| 13 | Picking_Time_Minutes | Time to collect items from shelves | minutes |
| 14 | Packing_Time_Minutes | Packing work **plus waiting in the packing queue** | minutes |
| 15 | Dispatch_Time_Minutes | Time from packed to handed to courier | minutes |
| 16 | Delivery_Time_Minutes | Time from courier pickup to customer | minutes |
| 17 | Total_Time_Minutes | Sum of columns 11-16 | minutes |
| 18 | SLA_Minutes | Promised total time for that priority and zone | minutes |
| 19 | Order_Status | Where the order stands | Delivered, Cancelled, In Transit |
| 20 | Delay_Status | Was the promise broken? | On Time, Delayed, Not Applicable |
| 21 | Delay_Stage | Stage that went furthest over its normal time | Receiving, Inventory, Picking, Packing, Dispatch, Delivery; "No Delay"; "Not Applicable" |
| 22 | Delay_Reason | Business reason linked to that stage | 13 reasons; "No Delay"; "Not Applicable" |
| 23 | Warehouse_Employee_ID | Picker responsible for the order | EMP001-EMP020, or "Unassigned" |
| 24 | Operational_Cost | Cost to fulfil the order | Indian Rupees (Rs) |

Columns 4, 6, 11, 12, 17, 18, 21 were added to the brief's list so that stage-level analysis is possible.

## Intentional blanks (these are NOT errors)

- **Cancelled orders (52):** Picking, Packing, Dispatch, Delivery and Total are blank because those stages never happened.
- **In Transit orders (7):** Delivery and Total are blank because the parcel had not arrived at export time.
- Blank means "did not happen". It is not zero. This matters when calculating averages.

## How the data was generated

1. **Dates and hours:** 2,000 orders spread over 61 days. Weekends are 25% busier, month-end 10% busier, festive week 2.3 times busier. More orders arrive at lunch and evening hours.
2. **Customer, product, priority, quantity:** drawn at random using stated percentages (e.g. 15% Express, 65% Standard, 20% Economy; 52% of orders are 1 unit).
3. **Inventory:** each category has its own stock-out chance (e.g. Electronics highest, Books lowest). Chances are 1.7 times higher in festive week. Out-of-stock orders wait for replenishment (median 150 minutes), and 18% of them are cancelled.
4. **Stage times:** each stage has a typical time with natural variation (a few orders are much slower than normal, as in real life). Bulky or multi-unit orders take longer.
5. **Built-in business causes (assumptions):**
   - Packing queues grow when a day is much busier than normal, and more at peak hours.
   - Evening picking is 10% slower (short of pickers).
   - 3 trainee pickers (EMP005, EMP012, EMP018) are about 30% slower.
   - Small chances of packing-material shortage (2.5%), courier pickup delay (4%) and courier transit delay (3.5%; 7% for remote).
6. **Delay rule:** an order is Delayed if Total_Time_Minutes is greater than SLA_Minutes. SLA = 1.06 x typical delivery time for that priority and zone + 150 minutes.
7. **Delay_Stage:** the stage with the biggest excess over its normal time.
8. **Cost (Rs):** staff time at Rs 2.5 per minute + packaging by category + courier cost by zone (Express x1.5) + Rs 40 back-order handling if out of stock + compensation voucher if delayed (Rs 40; Express Rs 80). Waiting time is not charged as labour.

> **Honest limitation:** because we built the packing queue and festive-week effects into the generator, finding them in the analysis demonstrates our **method**. It does not prove anything about real warehouses. Say this clearly in the report and viva.

## Cleaning rules (raw to clean)

| Problem injected in raw file | Count | Rule applied |
|---|---|---|
| Exact duplicate rows | 25 | Remove duplicates |
| Inconsistent text (extra spaces, lower/upper case) in Priority, Category, Location | 75 | Strip spaces and map to standard names |
| Impossible Order_Quantity (0, -1, 99) | 8 | Replace with 1 (most common value) |
| Missing Delivery_Zone | 15 | Rebuild from Customer_Location |
| Missing Warehouse_Employee_ID | 8 | Fill with "Unassigned" (cannot be recovered) |

Result: 2,025 raw rows become 2,000 clean rows. The Python notebook (Phase 3) repeats these steps so the team can explain them.

## Known quirks (be ready to explain)

- One delivered order may be marked Delayed or On Time by a minute different from a strict comparison, because stored times are rounded to whole minutes.
- "Unassigned" appears as a 21st employee value in the clean file. Exclude it when analysing employee workload.
