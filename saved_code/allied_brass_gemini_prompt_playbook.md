# Allied Brass — Gemini Prompt Playbook (Comprehensive 3-Layer Edition)

This playbook is the "Source of Truth" for Allied Brass account analysis. It is designed to navigate the 85k SKU catalog by connecting **Attributes**, **Parents**, and **Business Units**.

---

## 🧠 The 3-Layer Interconnectivity Logic
1.  **Layer 1 (The Vibe):** Group by **Color/Finish** to find brand-wide outlier demand.
2.  **Layer 2 (The Design):** Group by **Item Group ID** to find the winning parent vehicles.
3.  **Layer 3 (The Business):** Group by **Custom Label 0** to allocate capital at the BU level.

---

## 🚀 The Comprehensive Analysis Prompts

### 1) The "Attribute Alpha" Deep Dive
**Goal:** Identify which finish should be scaled across ALL categories.
```text
For customer 6253381786, last 30 days, analyze every variant by its 'color' attribute. 
Show Revenue, ROAS, and Spend for the top 5 finishes. 
Identify the finish with the highest ROAS that has > $500 in spend. 
Label this as 'The Scale Material'.
```

### 2) The "Parent-Finish Profitability" Matrix
**Goal:** Prevent 'Hero' finishes from subsidizing 'Zombie' designs.
```text
Select the 'Matte Black' finish. 
Show a table of all Parent SKUs (item_group_id) that contain this finish. 
Compare the ROAS of Matte Black variants against the total average ROAS of each Parent. 
Flag any Parent where the Matte Black variant is the ONLY converter.
```

### 3) Business Unit (BU) Capital Reallocation
**Goal:** Shift budget from low-efficiency BUs to high-efficiency ones.
```text
Group the entire account by 'custom_label_0' (Business Unit). 
Compare the top 5 BUs by Spend against the top 5 BUs by ROAS. 
Identify 'Inefficient Anchors' (High Spend, < 2.5 ROAS) and 'Efficient Outliers' (Low Spend, > 6.0 ROAS).
Recommend a 20% budget shift from Anchors to Outliers.
```

### 4) The "Zombie SKU" Pruning Audit (Layered)
**Goal:** Prune waste without killing variant coverage.
```text
Identify SKUs with:
- Spend > $100
- Conversions = 0
- Custom Label 3 DOES NOT contain 'zombie'
Filter this by 'product_type' to see which department has the most hidden waste.
```

---

## 🛠 Structural Mapping Tools (Code-Based)

- `saved_code/analyze_attributes.py`: Generates the Attribute Alpha report.
- `saved_code/analyze_parent_finish.py`: Generates the Parent-Finish Matrix.
- `saved_code/finalize_rollup.py`: Performs the macro BU/Product Type rollup.

---
_Playbook Version 4.0 - Hierarchical Interconnectivity. Update: Dec 30, 2025._