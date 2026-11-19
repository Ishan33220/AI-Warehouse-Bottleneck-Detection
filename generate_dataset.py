"""
generate_dataset.py
===================
Creates a SYNTHETIC (hypothetical) e-commerce warehouse order dataset.
NONE of this is real company data. Every number comes from the assumptions
written in this file, so a professor can read and challenge each one.

What this script does (in plain English)
1. Builds 2,000 hypothetical orders between 1 Sep 2026 and 31 Oct 2026.
2. Gives each order realistic stage times (receiving, inventory, picking,
   packing, dispatch, delivery) using stated business rules.
3. Saves the "raw" file (like a messy export from a warehouse system).
4. Cleans the raw file with simple rules and saves the clean file.

Run it:   python generate_dataset.py
Needs:    pandas, numpy
"""

import os
import numpy as np
import pandas as pd

# ------------------------------------------------------------------
# STEP 0: Settings you can change (the "assumptions")
# ------------------------------------------------------------------
SEED = 42                     # same seed = same dataset every time
N_ORDERS = 2000               # number of orders to create
START_DATE = "2026-09-01"
END_DATE = "2026-10-31"
FESTIVE_START = pd.Timestamp("2026-10-15")   # hypothetical festive sale week
FESTIVE_END = pd.Timestamp("2026-10-21")
SNAPSHOT = pd.Timestamp("2026-11-03")        # date the data was "exported"

rng = np.random.default_rng(SEED)            # the random number generator


def noisy(median, sigma=0.25):
    """Return a value around 'median' with natural variation (always > 0).
    Real processing times are not all equal: most are near the median and
    a few are much slower. A log-normal shape gives exactly this pattern."""
    return median * np.exp(rng.normal(0, sigma))


# ------------------------------------------------------------------
# STEP 1: Business lookup tables (assumptions)
# ------------------------------------------------------------------
# name: (share of orders, picking multiplier, packing multiplier,
#        chance Out of Stock, chance Low Stock, packaging cost in Rs)
CATEGORIES = {
    "Electronics":           (0.20, 0.90, 1.15, 0.060, 0.06, 30),
    "Fashion & Apparel":     (0.22, 1.00, 0.85, 0.035, 0.05, 12),
    "Home & Kitchen":        (0.16, 1.15, 1.35, 0.035, 0.05, 35),
    "Beauty & Personal Care": (0.12, 0.85, 0.95, 0.030, 0.04, 14),
    "Books & Stationery":    (0.08, 0.90, 0.80, 0.020, 0.03, 10),
    "Grocery & Gourmet":     (0.10, 1.05, 1.00, 0.025, 0.04, 14),
    "Toys & Games":          (0.07, 1.00, 1.10, 0.055, 0.06, 18),
    "Sports & Fitness":      (0.05, 1.10, 1.20, 0.030, 0.04, 24),
}

# zone: (share of orders, {city: share})
ZONES = {
    "Metro":  (0.55, {"Delhi NCR": .25, "Mumbai": .16, "Bengaluru": .15, "Hyderabad": .11,
                      "Chennai": .09, "Kolkata": .08, "Pune": .09, "Ahmedabad": .07}),
    "Tier-2": (0.33, {"Lucknow": .20, "Jaipur": .18, "Varanasi": .12, "Patna": .13,
                      "Indore": .13, "Bhopal": .12, "Kanpur": .12}),
    "Remote": (0.12, {"Guwahati": .30, "Ranchi": .25, "Dehradun": .20, "Shimla": .15,
                      "Imphal": .10}),
}
CITY_TO_ZONE = {city: z for z, (_, cities) in ZONES.items() for city in cities}

PRIORITIES = ["Express", "Standard", "Economy"]
PRIORITY_SHARE = [0.15, 0.65, 0.20]

# Typical (median) delivery time in minutes by priority and zone
DELIVERY_MEDIAN = {
    ("Express", "Metro"): 700,   ("Express", "Tier-2"): 950,   ("Express", "Remote"): 1250,
    ("Standard", "Metro"): 1700, ("Standard", "Tier-2"): 2300, ("Standard", "Remote"): 3100,
    ("Economy", "Metro"): 2600,  ("Economy", "Tier-2"): 3500,  ("Economy", "Remote"): 4600,
}
# Courier cost per order (Rs) by zone
COURIER_COST = {"Metro": 45, "Tier-2": 70, "Remote": 120}

# 20 employees (pickers). Morning 7, Evening 7, Night 6.
ROSTER = {
    "Morning": [f"EMP{n:03d}" for n in range(1, 8)],
    "Evening": [f"EMP{n:03d}" for n in range(8, 15)],
    "Night":   [f"EMP{n:03d}" for n in range(15, 21)],
}
TRAINEES = {"EMP005", "EMP012", "EMP018"}   # new joiners, ~30% slower


# ------------------------------------------------------------------
# STEP 2: Decide how many orders arrive on each day and hour
# ------------------------------------------------------------------
days = pd.date_range(START_DATE, END_DATE)
day_weights = []
for d in days:
    w = 1.0
    if d.dayofweek >= 5:                    # weekends a bit busier
        w *= 1.25
    if d.day >= 28:                         # month-end bump
        w *= 1.10
    if FESTIVE_START <= d <= FESTIVE_END:   # festive sale surge
        w *= 2.3
    day_weights.append(w)
day_weights = np.array(day_weights) / sum(day_weights)

day_index = rng.choice(len(days), size=N_ORDERS, p=day_weights)

hour_weights = np.array([.5] * 6 + [1, 2, 3, 4, 5, 6, 6, 5, 5, 4, 4, 4, 5, 6, 7, 7, 5, 2], dtype=float)
hour_weights = hour_weights / hour_weights.sum()
hours = rng.choice(24, size=N_ORDERS, p=hour_weights)
minutes = rng.integers(0, 60, size=N_ORDERS)

# sort orders by date, then hour, then minute (oldest first)
order = np.lexsort((minutes, hours, day_index))
day_index, hours, minutes = day_index[order], hours[order], minutes[order]
order_dates = days[day_index]

# "load" = how busy a day is compared with a normal day
daily_counts = pd.Series(order_dates).value_counts()
typical_daily = daily_counts.median()

# ------------------------------------------------------------------
# STEP 3: Build each order one by one
# ------------------------------------------------------------------
cat_names = list(CATEGORIES.keys())
cat_probs = np.array([CATEGORIES[c][0] for c in cat_names])
zone_names = list(ZONES.keys())
zone_probs = np.array([ZONES[z][0] for z in zone_names])

# Each employee gets a random workload weight (some are busier than others)
emp_weight = {e: rng.uniform(0.6, 1.4) for shift in ROSTER.values() for e in shift}

rows = []
for i in range(N_ORDERS):
    date = order_dates[i]
    hour = int(hours[i])
    load = daily_counts[date] / typical_daily
    festive = FESTIVE_START <= date <= FESTIVE_END
    peak_hour = hour in (11, 12, 13, 14, 19, 20, 21, 22)

    # shift is decided by the hour the order arrives
    if 6 <= hour < 14:
        shift = "Morning"
    elif 14 <= hour < 22:
        shift = "Evening"
    else:
        shift = "Night"

    # who / what / where
    zone = rng.choice(zone_names, p=zone_probs)
    cities = list(ZONES[zone][1].keys())
    city = rng.choice(cities, p=list(ZONES[zone][1].values()))
    category = rng.choice(cat_names, p=cat_probs)
    _, pick_mult, pack_mult, oos_p, low_p, pack_cost = CATEGORIES[category]
    priority = rng.choice(PRIORITIES, p=PRIORITY_SHARE)
    qty = int(rng.choice([1, 2, 3, 4, 5, 6], p=[.52, .25, .11, .06, .04, .02]))

    staff = ROSTER[shift]
    w = np.array([emp_weight[e] for e in staff])
    employee = rng.choice(staff, p=w / w.sum())
    speed = 1.30 if employee in TRAINEES else float(np.clip(rng.normal(1.0, 0.06), 0.85, 1.15))

    # --- Stage 1: Order receiving (system + payment check) -------------
    receiving = noisy(6, 0.35)
    payment_issue = rng.random() < 0.02
    if payment_issue:
        receiving += rng.uniform(30, 90)

    # --- Stage 2: Inventory verification -------------------------------
    oos_p = oos_p * 1.6 * (1.7 if festive else 1.0)    # more stock-outs in festive week
    u = rng.random()
    if u < oos_p:
        inv_status = "Out of Stock"
    elif u < oos_p + low_p:
        inv_status = "Low Stock"
    else:
        inv_status = "Available"
    inv_base = {"Available": 5, "Low Stock": 9, "Out of Stock": 8}[inv_status]
    inventory = noisy(inv_base, 0.3)
    restock_wait = 0.0
    if inv_status == "Out of Stock":              # waiting for replenishment
        restock_wait = float(np.clip(noisy(150, 0.7), 45, 900))
        inventory += restock_wait

    # --- Cancellation (before picking starts) --------------------------
    cancelled = False
    if inv_status == "Out of Stock" and rng.random() < 0.18:
        cancelled = True
    elif rng.random() < 0.012:                    # customer changes mind
        cancelled = True

    picking = packing = dispatch = delivery = np.nan
    flag_long_route = flag_material = flag_courier_pickup = flag_courier_transit = False
    queue = 0.0

    if not cancelled:
        # --- Stage 3: Picking -------------------------------------------
        picking = 28 * pick_mult * (1 + 0.12 * (qty - 1)) * speed * noisy(1, 0.28)
        if shift == "Evening":
            picking *= 1.10                       # evening is short of pickers
        picking *= 1 + 0.10 * max(0, load - 1)    # busy day = slower
        flag_long_route = rng.random() < 0.05     # occasionally a long route
        if flag_long_route:
            picking *= 1.8

        # --- Stage 4: Packing (includes waiting in the queue) -----------
        work = 12 * pack_mult * (1 + 0.10 * (qty - 1)) * noisy(1, 0.25)
        congestion = max(0, load - 1.1)           # only on very busy days
        queue_mean = 4 + 70 * congestion
        if peak_hour:
            queue_mean *= 1.3
        if shift == "Night":
            queue_mean *= 0.7
        queue = rng.exponential(queue_mean)
        flag_material = rng.random() < 0.025      # packing material runs out
        packing = work + queue
        if flag_material:
            packing += rng.uniform(40, 120)

        # --- Stage 5: Dispatch (waiting for courier pickup) -------------
        dispatch = noisy(20 if priority == "Express" else 35, 0.4)
        flag_courier_pickup = rng.random() < 0.04
        if flag_courier_pickup:
            dispatch += rng.uniform(60, 240)

        # --- Stage 6: Delivery -----------------------------------------
        median_delivery = DELIVERY_MEDIAN[(priority, zone)]
        delivery = noisy(median_delivery, 0.04)
        flag_courier_transit = rng.random() < (0.07 if zone == "Remote" else 0.035)
        if flag_courier_transit:
            delivery += rng.uniform(300, 1200)

    # --- Promised time (SLA) for this priority and zone -----------------
    sla = round(DELIVERY_MEDIAN[(priority, zone)] * 1.06 + 150)

    # --- Status and delay decision ---------------------------------------
    order_time = date + pd.Timedelta(hours=hour, minutes=int(minutes[i]))
    status = delay_status = delay_stage = delay_reason = "Not Applicable"
    total = np.nan

    if cancelled:
        status = "Cancelled"
    else:
        total = receiving + inventory + picking + packing + dispatch + delivery
        if order_time + pd.Timedelta(minutes=float(total)) > SNAPSHOT:
            status = "In Transit"
            delivery = np.nan                      # not delivered yet when exported
            total = np.nan
        else:
            status = "Delivered"
            if total > sla:
                delay_status = "Delayed"
                # the stage that went furthest over its normal time is blamed
                normal = {"Receiving": 7, "Inventory": 7, "Picking": 30, "Packing": 15,
                          "Dispatch": 35, "Delivery": DELIVERY_MEDIAN[(priority, zone)] * 1.08}
                actual = {"Receiving": receiving, "Inventory": inventory, "Picking": picking,
                          "Packing": packing, "Dispatch": dispatch, "Delivery": delivery}
                delay_stage = max(normal, key=lambda s: actual[s] - normal[s])

                # a reason that matches the stage and what really happened
                if delay_stage == "Receiving":
                    delay_reason = "Payment/order verification delay"
                elif delay_stage == "Inventory":
                    delay_reason = ("Stock-out - awaiting replenishment" if inv_status == "Out of Stock"
                                    else "Low stock / inventory record mismatch")
                elif delay_stage == "Picking":
                    if flag_long_route:
                        delay_reason = "Long picking route / poor bin location"
                    elif employee in TRAINEES:
                        delay_reason = "Inexperienced picker (new joiner)"
                    else:
                        delay_reason = "Picker shortage during peak shift"
                elif delay_stage == "Packing":
                    if flag_material:
                        delay_reason = "Packing material shortage"
                    elif queue > 25:
                        delay_reason = "Packing station congestion (peak load)"
                    else:
                        delay_reason = "Understaffed packing shift"
                elif delay_stage == "Dispatch":
                    delay_reason = "Courier pickup delay" if flag_courier_pickup else "Dispatch batching wait"
                else:
                    if flag_courier_transit:
                        delay_reason = "Courier delay in transit"
                    elif zone == "Remote":
                        delay_reason = "Remote location / address issue"
                    else:
                        delay_reason = "Courier route congestion"
            else:
                delay_status = "On Time"
                delay_stage = delay_reason = "No Delay"

    # --- Operational cost in Rs (simple, stated formula) -----------------
    labour_rate = 2.5                              # Rs per minute of staff time
    if cancelled:
        cost = labour_rate * (receiving + 8) + 20
    else:
        work_minutes = receiving + 8 + picking + (packing - queue) + dispatch
        courier = COURIER_COST[zone] * (1.5 if priority == "Express" else 1.0) + 8 * (qty - 1)
        cost = labour_rate * work_minutes + pack_cost * (1 + 0.3 * (qty - 1)) + courier
        if inv_status == "Out of Stock":
            cost += 40                             # extra handling for back-order
        if delay_status == "Delayed":
            cost += 80 if priority == "Express" else 40   # compensation voucher

    rows.append({
        "Order_ID": f"ORD-{100001 + i}",
        "Order_Date": date.strftime("%Y-%m-%d"),
        "Order_Hour": hour,
        "Shift": shift,
        "Customer_Location": city,
        "Delivery_Zone": zone,
        "Product_Category": category,
        "Order_Priority": priority,
        "Order_Quantity": qty,
        "Inventory_Status": inv_status,
        "Receiving_Time_Minutes": receiving,
        "Inventory_Check_Time_Minutes": inventory,
        "Picking_Time_Minutes": picking,
        "Packing_Time_Minutes": packing,
        "Dispatch_Time_Minutes": dispatch,
        "Delivery_Time_Minutes": delivery,
        "Total_Time_Minutes": total,
        "SLA_Minutes": sla,
        "Order_Status": status,
        "Delay_Status": delay_status,
        "Delay_Stage": delay_stage,
        "Delay_Reason": delay_reason,
        "Warehouse_Employee_ID": employee,
        "Operational_Cost": round(cost, 2),
    })

df = pd.DataFrame(rows)

# Time columns as whole minutes; blank (not zero) when a stage never happened
time_cols = [c for c in df.columns if c.endswith("_Minutes")]
for c in time_cols:
    df[c] = df[c].round(0).astype("Int64")

# ------------------------------------------------------------------
# STEP 4: Make a deliberately MESSY "raw" version (for the cleaning demo)
# ------------------------------------------------------------------
raw = df.copy()
raw["Order_Quantity"] = raw["Order_Quantity"].astype("Int64")
rows_pool = rng.permutation(len(raw))

bad_qty = rows_pool[0:8]            # impossible quantities (0, -1, 99)
raw.loc[bad_qty, "Order_Quantity"] = rng.choice([0, -1, 99], size=8)

miss_zone = rows_pool[8:23]         # missing zone (can be rebuilt from city)
raw.loc[miss_zone, "Delivery_Zone"] = np.nan

miss_emp = rows_pool[23:31]         # missing employee ID (cannot be rebuilt)
raw.loc[miss_emp, "Warehouse_Employee_ID"] = np.nan

messy_pri = rows_pool[31:66]        # inconsistent text: spaces / capitals
raw.loc[messy_pri, "Order_Priority"] = [
    rng.choice([p.lower(), p.upper(), " " + p + " "]) for p in raw.loc[messy_pri, "Order_Priority"]]

messy_cat = rows_pool[66:91]
raw.loc[messy_cat, "Product_Category"] = [
    rng.choice([p.lower(), " " + p, p + " "]) for p in raw.loc[messy_cat, "Product_Category"]]

messy_loc = rows_pool[91:106]
raw.loc[messy_loc, "Customer_Location"] = [
    rng.choice([p.lower(), " " + p + " "]) for p in raw.loc[messy_loc, "Customer_Location"]]

dups = raw.sample(25, random_state=SEED)     # 25 duplicate rows
raw = pd.concat([raw, dups]).sort_values("Order_ID", kind="stable").reset_index(drop=True)


# ------------------------------------------------------------------
# STEP 5: Cleaning rules (the same rules are repeated in the notebook)
# ------------------------------------------------------------------
def clean(raw_df):
    d = raw_df.drop_duplicates().copy()                       # 1. remove duplicates

    pri = {p.lower(): p for p in PRIORITIES}                   # 2. fix text
    cat = {c.lower(): c for c in CATEGORIES}
    loc = {c.lower(): c for c in CITY_TO_ZONE}
    d["Order_Priority"] = d["Order_Priority"].str.strip().str.lower().map(pri)
    d["Product_Category"] = d["Product_Category"].str.strip().str.lower().map(cat)
    d["Customer_Location"] = d["Customer_Location"].str.strip().str.lower().map(loc)

    bad = (d["Order_Quantity"] < 1) | (d["Order_Quantity"] > 10)   # 3. impossible quantity
    d.loc[bad, "Order_Quantity"] = 1                               #    -> most common value

    d["Delivery_Zone"] = d["Customer_Location"].map(CITY_TO_ZONE)  # 4. rebuild zone from city
    d["Warehouse_Employee_ID"] = d["Warehouse_Employee_ID"].fillna("Unassigned")  # 5.
    return d.reset_index(drop=True)


clean_df = clean(raw)

# ------------------------------------------------------------------
# STEP 6: Save files + a small sample
# ------------------------------------------------------------------
folder = os.path.dirname(os.path.abspath(__file__))
raw.to_csv(os.path.join(folder, "warehouse_orders_raw.csv"), index=False)
clean_df.to_csv(os.path.join(folder, "warehouse_orders.csv"), index=False)

# sample: 20 rows showing different situations (for understanding the structure)
sample_parts = [
    clean_df[clean_df.Delay_Status == "On Time"].head(5),
    clean_df[(clean_df.Delay_Stage == "Packing")].head(3),
    clean_df[(clean_df.Delay_Stage == "Inventory")].head(2),
    clean_df[(clean_df.Delay_Stage == "Picking")].head(2),
    clean_df[(clean_df.Delay_Stage == "Dispatch")].head(1),
    clean_df[(clean_df.Delay_Stage == "Delivery")].head(2),
    clean_df[clean_df.Order_Status == "Cancelled"].head(3),
    clean_df[clean_df.Order_Status == "In Transit"].head(2),
]
pd.concat(sample_parts).sort_values("Order_ID").to_csv(
    os.path.join(folder, "warehouse_orders_sample.csv"), index=False)

print("Raw rows  :", len(raw))
print("Clean rows:", len(clean_df))
print("Files saved in:", folder)
