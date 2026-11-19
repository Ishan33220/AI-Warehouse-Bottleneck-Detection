# Dashboard Explained and Viva Guide

Simple business English. Numbers are from `warehouse_orders.csv` (synthetic data, 2,000 orders).

## 1. What each page is for

| Page | Question it answers |
|---|---|
| 1. Warehouse Overview | "How is the warehouse doing overall?" |
| 2. Bottleneck Analysis | "Which stage is causing the delays, and why?" |
| 3. Inventory and Workforce Efficiency | "Do we have the stock and the people to cope?" |

## 2. Why we selected each KPI

| KPI | Why a manager cares | What problem it exposes |
|---|---|---|
| Total Orders | Shows the workload | Sudden surges that overload the warehouse |
| Completed Orders | Orders actually delivered | Gap between orders taken and orders fulfilled |
| Delayed Orders | Orders that broke the delivery promise | Direct customer-service risk |
| On-Time Delivery % | The standard service-level measure (83.1%) | About 1 in 6 delivered orders is late |
| Average Picking / Packing / Dispatch Time | Time inside each warehouse department | Which department is slow |
| Average Delivery Hours | Courier time (36.0 hours) | Delays outside the warehouse's control |
| Inventory Shortage % | Orders that hit an out-of-stock item (8.2%) | Lost sales, waiting time, cancellations |
| Total Operational Cost | Money spent fulfilling orders | Cost impact of delays and shortages |

## 3. What each visual means and how a manager uses it

**Page 1**
- **Daily Order Trend (teal = orders, red = delayed orders):** shows when pressure builds. Use it to plan extra staff before known busy periods. Our festive week jumps well above normal days.
- **Orders by Status:** delivered, cancelled, in transit. A growing cancelled slice signals a problem (often stock-outs).
- **Orders by Shift:** where the workload sits during the day. Use it to match staff to demand.

**Page 2**
- **Delays by Operational Stage:** the tallest bar is the biggest problem. The warehouse bottleneck bar turns red automatically (here: Packing). The courier bar (Delivery) is grey because the warehouse cannot directly control it.
- **Biggest Warehouse Bottleneck card:** names the stage that the data says needs attention first.
- **Top 8 Delay Reasons:** moves from "where" to "why". Packing station congestion is the largest reason.
- **Average Picking / Packing / Dispatch Time:** speed of each department.
- **Delay Rate by Shift and by Delivery Zone:** whether the problem is tied to a time of day or to a region.

**Page 3**
- **Inventory Status and Shortage by Category:** which products run out most (Electronics and Toys & Games). Use it to set safety stock before sale periods.
- **Orders per Employee, Orders by Shift, Average Picking/Packing Time by Shift:** is manpower balanced? Evening shift carries far more orders per person than night shift. Tip for the demo: click a shift in the Shift slicer and watch the Orders per Employee card change (Morning 110.0, Evening 139.6, Night 40.8; all shifts together 99.6).
- **Delivery Zone Performance:** which regions get late deliveries, to review courier partners.

## 4. Reading it as a manager (5 steps)
1. Check the KPI cards (is on-time % acceptable?).
2. Go to page 2 and read the red bar (where are the delays?).
3. Read the delay reasons (why?).
4. Use the date slicer to test busy days against normal days.
5. Go to page 3 (stock and people) and decide: more packing capacity, rebalanced shifts, higher safety stock, courier review.

**Remember:** the data is synthetic and the packing queue in busy periods was built into our data generator. The dashboard shows that our method finds a bottleneck. It does not prove anything about a real warehouse.

## 5. Who explains what in the viva (about 60 to 75 seconds each)

### Student 1: Data and Business Research Analyst, explains the data and Page 1
**Say:** "Our data is a synthetic set of 2,000 orders for September and October 2026, cleaned in Python. Page 1 gives the overall picture: 2,000 orders, 1,941 delivered, 328 delayed, 83.1% on time. The trend line shows a surge in the festive week."
- *Why synthetic data?* Real company data is confidential. Synthetic data lets us control and document every assumption.
- *Why are some cells blank?* Cancelled and in-transit orders never completed those stages. Blank means "did not happen", not zero.
- *What does the date slicer do?* It filters every chart to the chosen dates, so we can compare busy and normal days.

### Student 2: Business Intelligence Analyst, explains KPIs and DAX
**Say:** "Each card is a DAX measure. On-time % is on-time orders divided by on-time plus delayed orders. We leave out cancelled and in-transit orders because we cannot judge them yet."
- *What is DAX?* The formula language of Power BI. A measure recalculates for whatever the user filters.
- *Why divide with DIVIDE and not /?* DIVIDE returns blank instead of an error when the denominator is zero.
- *Why is the average picking time not affected by cancelled orders?* AVERAGE ignores blank cells.

### Student 3: Generative AI Developer, explains Page 2 and how it feeds the AI
**Say:** "Page 2 shows Packing causing 123 of 328 delays (37.5%), and 75% of all delays are inside the warehouse. These exact numbers are what we give to the AI so it explains verified facts instead of inventing them."
- *How does the dashboard find the biggest bottleneck?* A measure ranks the warehouse stages by delayed orders and returns the top one. We exclude Delivery because it is the courier's stage.
- *Is Packing the bottleneck in real warehouses?* Not necessarily. Our data was built with that cause. We only show the method works.
- *Why look at the median as well as the average?* A few very long waits pull the average up. The pattern is bursts, not constant slowness.

### Student 4: Automation and Integration Analyst, explains Page 3, slicers and integration
**Say:** "Page 3 covers stock and manpower: 8.2% of orders hit an out-of-stock item and the evening shift handles far more orders per person than the night shift. All slicers are synced across pages. The project is stored as a Power BI Project (PBIP) in GitHub, and n8n and Python read the same CSV, so every number agrees."
- *What is cross-filtering?* Clicking one chart filters the others on the page.
- *Is Power BI connected to n8n?* No. Both read the same CSV. A direct link is a future enhancement.
- *What is a PBIP?* A Power BI project saved as readable files, so it works well with GitHub.

### Questions for all four
- *What is the single most important insight?* The packing stage causes the most delays inside the warehouse, mainly in busy periods.
- *What would you do first as the manager?* Add flexible packing capacity for peak days and rebalance shifts, then measure again.
- *Can you promise cost savings?* No. We would need a simulation or a pilot to support any number.
