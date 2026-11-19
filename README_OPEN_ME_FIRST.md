# WarehouseDashboard: Power BI Project (PBIP)

A ready-to-open Power BI project for **AI-Powered Warehouse Bottleneck Detection and Operational Decision Support System**.
It contains the data model, 24 DAX measures and three fully designed report pages (50 visual objects including slicers and text boxes).

## 1. Honest status (please read)

| Check | Result |
|---|---|
| All 57 JSON files validated against Microsoft's official Power BI report schemas | Passed (and a deliberately broken file was correctly rejected, so the test is real) |
| Every field used in every visual exists in the model and in the CSV header | Passed (29 distinct fields) |
| Visual layout: nothing outside the 1280x720 canvas, nothing overlapping | Passed |
| Measure logic reproduced in Python on the same CSV and compared with `kpi_summary.json` | Passed (all 9 required KPIs match, bottleneck = Packing) |
| **Opened inside Power BI Desktop** | **Not done. I cannot run Power BI here.** You are the first to open it |
| DAX syntax accepted by Power BI's engine | Not yet confirmed (logic checked, syntax not machine-checked) |

If something does not open or render, send me the **exact error text** or a screenshot and I will fix the project. Do not describe the dashboard as "tested in Power BI" in the report until you have opened it and matched the numbers below.

## 2. Folder structure

```
PBIP/
  WarehouseDashboard.pbip                 <- double-click this to open
  WarehouseDashboard.SemanticModel/       <- the data model
    definition/tables/Orders.tmdl         <- 24 columns + 24 DAX measures + CSV loading query
    definition/expressions.tmdl           <- the DataFilePath setting (you edit this once)
    definition/model.tmdl, database.tmdl, ../definition.pbism
  WarehouseDashboard.Report/              <- the dashboard
    definition/pages/<3 pages>/visuals/   <- one folder per visual
    StaticResources/                      <- colour theme (navy / teal / red)
    definition.pbir, definition/report.json, version.json, pages.json
  .gitignore
```
The dataset stays in `Dataset/warehouse_orders.csv` (unchanged, 2,000 rows).

## 3. How to open it (step by step)

1. **Copy** the whole `AI-Warehouse-Bottleneck-Detector` folder to your Windows laptop (for example `C:\Users\<you>\Documents\`). Unzip first if you downloaded a zip.
2. Open **Power BI Desktop**. Go to **File > Options and settings > Options > Preview features**. If you see **"Power BI Project (.pbip) save option"** and **"Store reports using enhanced metadata format (PBIR)"**, tick both and restart Power BI. (In recent versions these may already be on or may not be listed. That is fine.)
3. **File > Open report > Browse this device** and choose `PowerBI\PBIP\WarehouseDashboard.pbip`. (Double-clicking it also works.)
4. The pages will appear but the charts will be empty or show an error. This is expected, because the project does not yet know where the CSV is on **your** laptop.
5. On the **Home** ribbon click the small arrow under **Transform data** and choose **Edit parameters**.
6. In the box **DataFilePath** paste the full path to the CSV, for example
   `C:\Users\Ishan\Documents\AI-Warehouse-Bottleneck-Detector\Dataset\warehouse_orders.csv`
   (Tip: in File Explorer, hold Shift, right-click the CSV, choose **Copy as path**, then delete the quotation marks.)
7. Click **OK**, then **Apply changes** (yellow bar) or **Home > Refresh**. If Power BI asks about privacy levels, choose **Ignore privacy levels** or **Organizational**.
8. Check the numbers against section 4. If they match, your dashboard works.
9. **File > Save**. To make one single file for submission: **File > Save as > Power BI files (*.pbix)**.

## 4. What you should see (expected values from the real data)

**Page 1: Warehouse Overview**
- Cards: Total Orders **2,000** | Completed Orders **1,941** | Delayed Orders **328** (red) | On-Time Delivery **83.1%** | Total Operational Cost **₹762,668**
- Orders by Status donut: Delivered 1,941; Cancelled 52; In Transit 7
- Orders by Shift: Morning 773, Evening 981, Night 246
- Daily Order Trend: sharp rise in the festive week (15 to 21 Oct); busiest day is 2026-10-18 with 82 orders and 39 delayed

**Page 2: Bottleneck Analysis**
- Cards: Delayed **328** | Avg Picking **37.4** | Avg Packing **43.7** | Avg Dispatch **42.1** | Biggest Warehouse Bottleneck **Packing**
- Delays by stage (bars): Packing **123** (red), Delivery 82 (grey, courier), Inventory 64, Dispatch 50, Picking 6, Receiving 3
- Top 8 delay reasons donut: Packing station congestion 109; Stock-out 64; Courier delay in transit 62; Courier pickup delay 36; Dispatch batching wait 14; Courier route congestion 14; Packing material shortage 11; Remote location/address issue 6
- Delay rate by shift: Morning 18.5%, Evening 15.8%, Night 16.1%
- Delay rate by zone: Metro 17.9%, Tier-2 14.4%, Remote 19.5%
- Side cards: Bottleneck delays **123** | share of all delays **37.5%** | delays inside warehouse **75.0%**

**Page 3: Inventory and Workforce Efficiency**
- Cards: Inventory Shortage **8.2%** | Out of Stock **163** | Low Stock **89** | Orders per Employee **99.6** | On-Time **83.1%**
- Inventory Status donut: Available 1,748; Low Stock 89; Out of Stock 163
- Shortage by category: Electronics 12.1%, Toys & Games 10.5%, Fashion & Apparel 8.2%, Beauty & Personal Care 8.0%, Home & Kitchen 6.5%, Grocery & Gourmet 4.9%, Sports & Fitness 4.9%, Books & Stationery 4.8%
- Average picking (min) by shift: Morning 35.8, Evening 38.3, Night 38.8
- Average packing (min) by shift: Morning 43.4, Evening 45.5, Night 37.2
- Delivery Zone Performance table: Metro 1066 orders / 82.1% on time / 29.6 hrs; Tier-2 690 / 85.6% / 39.5 hrs; Remote 244 / 80.5% / 54.4 hrs

These come from the same CSV and match `kpi_summary.json` where the two overlap. The shift values here include all 2,000 orders. The Phase 3 notebook left out 8 "Unassigned" orders for its employee table, so a few shift figures differ by about 0.1.

## 5. Slicers and cross-filtering

Every page has four slicers: Order Date (range slider), Order Priority, Shift, Delivery Zone. They are **synced**, so choosing "Express" on page 1 stays selected on pages 2 and 3. Clicking any bar or slice filters the other visuals on the same page. To clear, click the slicer or the selected bar again. Try selecting 15 to 21 Oct in the date slicer and watch Packing grow on page 2.

## 6. If something goes wrong

| Symptom | What to do |
|---|---|
| Power BI refuses to open the .pbip | Make sure the folder is intact (the `.Report` and `.SemanticModel` folders sit next to the `.pbip`). Turn on the preview features in step 2. Copy the exact error message and send it to me |
| "We couldn't find the file" / empty charts | The DataFilePath parameter is wrong (step 6). Edit it again |
| A single visual says "Can't display this visual" | Click the small warning icon for the message and send it to me. The other visuals are unaffected |
| All bars on page 2 are one colour | The colour-by-rule is a nicety. Fix manually: select the bar chart > Format > Bars > Colors > fx > Format style **Field value** > Based on field **Stage Bar Color** |
| Date slicer shows a list instead of a slider | Select the slicer > Format > Slicer settings > Style > **Between** |
| The measures show errors | Open Model view and confirm the table is named `Orders` and rows = 2,000 |
| Nothing works at all | Fallback: use your existing .pbix and the formulas in `dax_measures.md` (still valid) |

## 7. Visual inventory (generated from the actual project files)

### 1 Warehouse Overview

| # | Visual | Type | Fields used |
|---|---|---|---|
| 1 | Order Date | slicer | Values: Order_Date |
| 2 | Order Priority | slicer | Values: Order_Priority |
| 3 | Shift | slicer | Values: Shift |
| 4 | Delivery Zone | slicer | Values: Delivery_Zone |
| 5 | Total Orders | card | Values: Total Orders |
| 6 | Completed Orders | card | Values: Completed Orders |
| 7 | Delayed Orders | card | Values: Delayed Orders |
| 8 | On-Time Delivery % | card | Values: On-Time Delivery % |
| 9 | Total Operational Cost | card | Values: Total Operational Cost |
| 10 | Daily Order Trend (orders vs delayed orders) | lineChart | Category: Order_Date, Y: Total Orders, Y: Delayed Orders |
| 11 | Orders by Status | donutChart | Category: Order_Status, Y: Total Orders |
| 12 | Orders by Shift | clusteredColumnChart | Category: Shift, Y: Total Orders |

### 2 Bottleneck Analysis

| # | Visual | Type | Fields used |
|---|---|---|---|
| 1 | Order Date | slicer | Values: Order_Date |
| 2 | Order Priority | slicer | Values: Order_Priority |
| 3 | Shift | slicer | Values: Shift |
| 4 | Delivery Zone | slicer | Values: Delivery_Zone |
| 5 | Total Delayed Orders | card | Values: Delayed Orders |
| 6 | Average Picking Time (min) | card | Values: Average Picking Time |
| 7 | Average Packing Time (min) | card | Values: Average Packing Time |
| 8 | Average Dispatch Time (min) | card | Values: Average Dispatch Time |
| 9 | Biggest Warehouse Bottleneck | card | Values: Biggest Warehouse Bottleneck |
| 10 | Delays by Operational Stage (red = biggest warehouse bottleneck) | clusteredBarChart | Category: Delay_Stage, Y: Delayed Orders, Bar colour rule: Stage Bar Color |
| 11 | Top 8 Delay Reasons | donutChart | Category: Delay_Reason, Y: Delayed Orders (Top 8 Reasons) |
| 12 | Delay Rate % by Shift | clusteredColumnChart | Category: Shift, Y: Delay Rate % |
| 13 | Delay Rate % by Delivery Zone | clusteredColumnChart | Category: Delivery_Zone, Y: Delay Rate % |
| 14 | Delays at the Bottleneck Stage | card | Values: Bottleneck Delays |
| 15 | Bottleneck Share of All Delays | card | Values: Bottleneck Share of Delays % |
| 16 | Delays Inside the Warehouse (share) | card | Values: Warehouse Delay Share % |

### 3 Inventory and Workforce Efficiency

| # | Visual | Type | Fields used |
|---|---|---|---|
| 1 | Order Date | slicer | Values: Order_Date |
| 2 | Order Priority | slicer | Values: Order_Priority |
| 3 | Shift | slicer | Values: Shift |
| 4 | Delivery Zone | slicer | Values: Delivery_Zone |
| 5 | Inventory Shortage % | card | Values: Inventory Shortage % |
| 6 | Out of Stock Orders | card | Values: Out of Stock Orders |
| 7 | Low Stock Orders | card | Values: Low Stock Orders |
| 8 | Orders per Employee | card | Values: Orders per Employee |
| 9 | On-Time Delivery % | card | Values: On-Time Delivery % |
| 10 | Inventory Status | donutChart | Category: Inventory_Status, Y: Total Orders |
| 11 | Inventory Shortage % by Product Category | clusteredBarChart | Category: Product_Category, Y: Inventory Shortage % |
| 12 | Delivery Zone Performance | tableEx | Values: Delivery_Zone, Values: Total Orders, Values: On-Time Delivery %, Values: Average Delivery Hours |
| 13 | Orders by Shift | clusteredColumnChart | Category: Shift, Y: Total Orders |
| 14 | Average Picking Time by Shift (min) | clusteredColumnChart | Category: Shift, Y: Average Picking Time |
| 15 | Average Packing Time by Shift (min) | clusteredColumnChart | Category: Shift, Y: Average Packing Time |

Text boxes (header, header note, reading guide) are not listed.
