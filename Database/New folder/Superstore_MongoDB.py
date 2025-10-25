import pandas as pd
from pymongo import MongoClient
from io import StringIO

# ----------------------------
# Step 1: Connect to MongoDB
# ----------------------------
try:
    client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
    client.server_info()  # Test connection
    print("✅ MongoDB Connected Successfully!\n")
except Exception as e:
    print("❌ Error connecting to MongoDB:", e)
    exit()

# ----------------------------
# Step 2: Set Database and Collection
# ----------------------------
db = client['SuperstoreDB']          # Database (auto-created if not exists)
orders_collection = db['Orders']     # Collection (auto-created if not exists)

# Optional: Clear previous data to avoid duplicates
orders_collection.drop()

# ----------------------------
# Step 3: Load CSV into MongoDB (latin1 decoding to handle special chars)
# ----------------------------
with open('superstore.csv', 'rb') as f:
    content = f.read().decode('latin1')  # decode with latin1 to avoid UnicodeDecodeError
    df = pd.read_csv(StringIO(content))

orders_collection.insert_many(df.to_dict('records'))
print("1) CSV Data inserted successfully into Orders collection.\n")

# ----------------------------
# 4) Retrieve all documents
# ----------------------------
print("2) Sample documents in Orders collection:")
for order in orders_collection.find().limit(5):
    print(order)
print("...\n")

# ----------------------------
# 5) Count total documents
# ----------------------------
count = orders_collection.count_documents({})
print(f"3) Total number of documents: {count}\n")

# ----------------------------
# 6) Fetch orders from 'West' region
# ----------------------------
print("4) Orders from West region (sample 5):")
for order in orders_collection.find({"Region": "West"}).limit(5):
    print(order)
print("...\n")

# ----------------------------
# 7) Orders where Sales > 500
# ----------------------------
print("5) Orders with Sales > 500 (sample 5):")
for order in orders_collection.find({"Sales": {"$gt": 500}}).limit(5):
    print(order)
print("...\n")

# ----------------------------
# 8) Top 3 orders with highest Profit
# ----------------------------
print("6) Top 3 orders with highest Profit:")
for order in orders_collection.find().sort("Profit", -1).limit(3):
    print(order)
print("\n")

# ----------------------------
# 9) Update Ship Mode 'First Class' to 'Premium Class'
# ----------------------------
result = orders_collection.update_many(
    {"Ship Mode": "First Class"},
    {"$set": {"Ship Mode": "Premium Class"}}
)
print(f"7) Updated {result.modified_count} documents: Ship Mode changed to 'Premium Class'.\n")

# ----------------------------
# 10) Delete orders where Sales < 50
# ----------------------------
result = orders_collection.delete_many({"Sales": {"$lt": 50}})
print(f"8) Deleted {result.deleted_count} documents where Sales < 50.\n")

# ----------------------------
# 11) Total sales per region (aggregation)
# ----------------------------
print("9) Total sales per region:")
pipeline = [
    {"$group": {"_id": "$Region", "TotalSales": {"$sum": "$Sales"}}}
]
for record in orders_collection.aggregate(pipeline):
    print(record)
print("\n")

# ----------------------------
# 12) Distinct Ship Modes
# ----------------------------
ship_modes = orders_collection.distinct("Ship Mode")
print(f"10) Distinct Ship Modes: {ship_modes}\n")

# ----------------------------
# 13) Count number of orders per Category
# ----------------------------
print("11) Number of orders per Category:")
pipeline = [
    {"$group": {"_id": "$Category", "OrderCount": {"$sum": 1}}}
]
for record in orders_collection.aggregate(pipeline):
    print(record)
print("\n")

print("🎉 All practical tasks completed successfully!")








"""
Output: - 
(myenv) D:\PW Skills Assignments\Database\MongoDB>python Superstore_MongoDB.py
✅ MongoDB Connected Successfully!

1) CSV Data inserted successfully into Orders collection.

2) Sample documents in Orders collection:
{'_id': ObjectId('68fc95844a687946d45bb34f'), 'Row ID': 1, 'Order ID': 'CA-2016-152156', 'Order Date': '11/8/2016', 'Ship Date': '11/11/2016', 'Ship Mode': 'Second Class', 'Customer ID': 'CG-12520', 'Customer Name': 'Claire Gute', 'Segment': 'Consumer', 'Country': 'United States', 'City': 'Henderson', 'State': 'Kentucky', 'Postal Code': 42420, 'Region': 'South', 'Product ID': 'FUR-BO-10001798', 'Category': 'Furniture', 'Sub-Category': 'Bookcases', 'Product Name': 'Bush Somerset Collection Bookcase', 'Sales': 261.96, 'Quantity': 2, 'Discount': 0.0, 'Profit': 41.9136}
{'_id': ObjectId('68fc95844a687946d45bb350'), 'Row ID': 2, 'Order ID': 'CA-2016-152156', 'Order Date': '11/8/2016', 'Ship Date': '11/11/2016', 'Ship Mode': 'Second Class', 'Customer ID': 'CG-12520', 'Customer Name': 'Claire Gute', 'Segment': 'Consumer', 'Country': 'United States', 'City': 'Henderson', 'State': 'Kentucky', 'Postal Code': 42420, 'Region': 'South', 'Product ID': 'FUR-CH-10000454', 'Category': 'Furniture', 'Sub-Category': 'Chairs', 'Product Name': 'Hon Deluxe Fabric Upholstered Stacking Chairs, Rounded Back', 'Sales': 731.94, 'Quantity': 3, 'Discount': 0.0, 'Profit': 219.582}
{'_id': ObjectId('68fc95844a687946d45bb351'), 'Row ID': 3, 'Order ID': 'CA-2016-138688', 'Order Date': '6/12/2016', 'Ship Date': '6/16/2016', 'Ship Mode': 'Second Class', 'Customer ID': 'DV-13045', 'Customer Name': 'Darrin Van Huff', 'Segment': 'Corporate', 'Country': 'United States', 'City': 'Los Angeles', 'State': 'California', 'Postal Code': 90036, 'Region': 'West', 'Product ID': 'OFF-LA-10000240', 'Category': 'Office Supplies', 'Sub-Category': 'Labels', 'Product Name': 'Self-Adhesive Address Labels for Typewriters by Universal', 'Sales': 14.62, 'Quantity': 2, 'Discount': 0.0, 'Profit': 6.8714}
{'_id': ObjectId('68fc95844a687946d45bb352'), 'Row ID': 4, 'Order ID': 'US-2015-108966', 'Order Date': '10/11/2015', 'Ship Date': '10/18/2015', 'Ship Mode': 'Standard Class', 'Customer ID': 'SO-20335', 'Customer Name': "Sean O'Donnell", 'Segment': 'Consumer', 'Country': 'United States', 'City': 'Fort Lauderdale', 'State': 'Florida', 'Postal Code': 33311, 'Region': 'South', 'Product ID': 'FUR-TA-10000577', 'Category': 'Furniture', 'Sub-Category': 'Tables', 'Product Name': 'Bretford CR4500 Series Slim Rectangular Table', 'Sales': 957.5775, 'Quantity': 5, 'Discount': 0.45, 'Profit': -383.031}
{'_id': ObjectId('68fc95844a687946d45bb353'), 'Row ID': 5, 'Order ID': 'US-2015-108966', 'Order Date': '10/11/2015', 'Ship Date': '10/18/2015', 'Ship Mode': 'Standard Class', 'Customer ID': 'SO-20335', 'Customer Name': "Sean O'Donnell", 'Segment': 'Consumer', 'Country': 'United States', 'City': 'Fort Lauderdale', 'State': 'Florida', 'Postal Code': 33311, 'Region': 'South', 'Product ID': 'OFF-ST-10000760', 'Category': 'Office Supplies', 'Sub-Category': 'Storage', 'Product Name': "Eldon Fold 'N Roll Cart System", 'Sales': 22.368, 'Quantity': 2, 'Discount': 0.2, 'Profit': 2.5164}
...

3) Total number of documents: 9994

4) Orders from West region (sample 5):
{'_id': ObjectId('68fc95844a687946d45bb351'), 'Row ID': 3, 'Order ID': 'CA-2016-138688', 'Order Date': '6/12/2016', 'Ship Date': '6/16/2016', 'Ship Mode': 'Second Class', 'Customer ID': 'DV-13045', 'Customer Name': 'Darrin Van Huff', 'Segment': 'Corporate', 'Country': 'United States', 'City': 'Los Angeles', 'State': 'California', 'Postal Code': 90036, 'Region': 'West', 'Product ID': 'OFF-LA-10000240', 'Category': 'Office Supplies', 'Sub-Category': 'Labels', 'Product Name': 'Self-Adhesive Address Labels for Typewriters by Universal', 'Sales': 14.62, 'Quantity': 2, 'Discount': 0.0, 'Profit': 6.8714}
{'_id': ObjectId('68fc95844a687946d45bb354'), 'Row ID': 6, 'Order ID': 'CA-2014-115812', 'Order Date': '6/9/2014', 'Ship Date': '6/14/2014', 'Ship Mode': 'Standard Class', 'Customer ID': 'BH-11710', 'Customer Name': 'Brosina Hoffman', 'Segment': 'Consumer', 'Country': 'United States', 'City': 'Los Angeles', 'State': 'California', 'Postal Code': 90032, 'Region': 'West', 'Product ID': 'FUR-FU-10001487', 'Category': 'Furniture', 'Sub-Category': 'Furnishings', 'Product Name': 'Eldon Expressions Wood and Plastic Desk Accessories, Cherry Wood', 'Sales': 48.86, 'Quantity': 7, 'Discount': 0.0, 'Profit': 14.1694}
{'_id': ObjectId('68fc95844a687946d45bb355'), 'Row ID': 7, 'Order ID': 'CA-2014-115812', 'Order Date': '6/9/2014', 'Ship Date': '6/14/2014', 'Ship Mode': 'Standard Class', 'Customer ID': 'BH-11710', 'Customer Name': 'Brosina Hoffman', 'Segment': 'Consumer', 'Country': 'United States', 'City': 'Los Angeles', 'State': 'California', 'Postal Code': 90032, 'Region': 'West', 'Product ID': 'OFF-AR-10002833', 'Category': 'Office Supplies', 'Sub-Category': 'Art', 'Product Name': 'Newell 322', 'Sales': 7.28, 'Quantity': 4, 'Discount': 0.0, 'Profit': 1.9656}
{'_id': ObjectId('68fc95844a687946d45bb356'), 'Row ID': 8, 'Order ID': 'CA-2014-115812', 'Order Date': '6/9/2014', 'Ship Date': '6/14/2014', 'Ship Mode': 'Standard Class', 'Customer ID': 'BH-11710', 'Customer Name': 'Brosina Hoffman', 'Segment': 'Consumer', 'Country': 'United States', 'City': 'Los Angeles', 'State': 'California', 'Postal Code': 90032, 'Region': 'West', 'Product ID': 'TEC-PH-10002275', 'Category': 'Technology', 'Sub-Category': 'Phones', 'Product Name': 'Mitel 5320 IP Phone VoIP phone', 'Sales': 907.152, 'Quantity': 6, 'Discount': 0.2, 'Profit': 90.7152}
{'_id': ObjectId('68fc95844a687946d45bb357'), 'Row ID': 9, 'Order ID': 'CA-2014-115812', 'Order Date': '6/9/2014', 'Ship Date': '6/14/2014', 'Ship Mode': 'Standard Class', 'Customer ID': 'BH-11710', 'Customer Name': 'Brosina Hoffman', 'Segment': 'Consumer', 'Country': 'United States', 'City': 'Los Angeles', 'State': 'California', 'Postal Code': 90032, 'Region': 'West', 'Product ID': 'OFF-BI-10003910', 'Category': 'Office Supplies', 'Sub-Category': 'Binders', 'Product Name': 'DXL Angle-View Binders with Locking Rings by Samsill', 'Sales': 18.504, 'Quantity': 3, 'Discount': 0.2, 'Profit': 5.7825}
...

5) Orders with Sales > 500 (sample 5):
{'_id': ObjectId('68fc95844a687946d45bb350'), 'Row ID': 2, 'Order ID': 'CA-2016-152156', 'Order Date': '11/8/2016', 'Ship Date': '11/11/2016', 'Ship Mode': 'Second Class', 'Customer ID': 'CG-12520', 'Customer Name': 'Claire Gute', 'Segment': 'Consumer', 'Country': 'United States', 'City': 'Henderson', 'State': 'Kentucky', 'Postal Code': 42420, 'Region': 'South', 'Product ID': 'FUR-CH-10000454', 'Category': 'Furniture', 'Sub-Category': 'Chairs', 'Product Name': 'Hon Deluxe Fabric Upholstered Stacking Chairs, Rounded Back', 'Sales': 731.94, 'Quantity': 3, 'Discount': 0.0, 'Profit': 219.582}
{'_id': ObjectId('68fc95844a687946d45bb352'), 'Row ID': 4, 'Order ID': 'US-2015-108966', 'Order Date': '10/11/2015', 'Ship Date': '10/18/2015', 'Ship Mode': 'Standard Class', 'Customer ID': 'SO-20335', 'Customer Name': "Sean O'Donnell", 'Segment': 'Consumer', 'Country': 'United States', 'City': 'Fort Lauderdale', 'State': 'Florida', 'Postal Code': 33311, 'Region': 'South', 'Product ID': 'FUR-TA-10000577', 'Category': 'Furniture', 'Sub-Category': 'Tables', 'Product Name': 'Bretford CR4500 Series Slim Rectangular Table', 'Sales': 957.5775, 'Quantity': 5, 'Discount': 0.45, 'Profit': -383.031}
{'_id': ObjectId('68fc95844a687946d45bb356'), 'Row ID': 8, 'Order ID': 'CA-2014-115812', 'Order Date': '6/9/2014', 'Ship Date': '6/14/2014', 'Ship Mode': 'Standard Class', 'Customer ID': 'BH-11710', 'Customer Name': 'Brosina Hoffman', 'Segment': 'Consumer', 'Country': 'United States', 'City': 'Los Angeles', 'State': 'California', 'Postal Code': 90032, 'Region': 'West', 'Product ID': 'TEC-PH-10002275', 'Category': 'Technology', 'Sub-Category': 'Phones', 'Product Name': 'Mitel 5320 IP Phone VoIP phone', 'Sales': 907.152, 'Quantity': 6, 'Discount': 0.2, 'Profit': 90.7152}
{'_id': ObjectId('68fc95844a687946d45bb359'), 'Row ID': 11, 'Order ID': 'CA-2014-115812', 'Order Date': '6/9/2014', 'Ship Date': '6/14/2014', 'Ship Mode': 'Standard Class', 'Customer ID': 'BH-11710', 'Customer Name': 'Brosina Hoffman', 'Segment': 'Consumer', 'Country': 'United States', 'City': 'Los Angeles', 'State': 'California', 'Postal Code': 90032, 'Region': 'West', 'Product ID': 'FUR-TA-10001539', 'Category': 'Furniture', 'Sub-Category': 'Tables', 'Product Name': 'Chromcraft Rectangular Conference Tables', 'Sales': 1706.184, 'Quantity': 9, 'Discount': 0.2, 'Profit': 85.3092}
{'_id': ObjectId('68fc95844a687946d45bb35a'), 'Row ID': 12, 'Order ID': 'CA-2014-115812', 'Order Date': '6/9/2014', 'Ship Date': '6/14/2014', 'Ship Mode': 'Standard Class', 'Customer ID': 'BH-11710', 'Customer Name': 'Brosina Hoffman', 'Segment': 'Consumer', 'Country': 'United States', 'City': 'Los Angeles', 'State': 'California', 'Postal Code': 90032, 'Region': 'West', 'Product ID': 'TEC-PH-10002033', 'Category': 'Technology', 'Sub-Category': 'Phones', 'Product Name': 'Konftel 250 Conference\xa0phone\xa0- Charcoal black', 'Sales': 911.424, 'Quantity': 4, 'Discount': 0.2, 'Profit': 68.3568}
...

6) Top 3 orders with highest Profit:
{'_id': ObjectId('68fc95844a687946d45bcdf9'), 'Row ID': 6827, 'Order ID': 'CA-2016-118689', 'Order Date': '10/2/2016', 'Ship Date': '10/9/2016', 'Ship Mode': 'Standard Class', 'Customer ID': 'TC-20980', 'Customer Name': 'Tamara Chand', 'Segment': 'Corporate', 'Country': 'United States', 'City': 'Lafayette', 'State': 'Indiana', 'Postal Code': 47905, 'Region': 'Central', 'Product ID': 'TEC-CO-10004722', 'Category': 'Technology', 'Sub-Category': 'Copiers', 'Product Name': 'Canon imageCLASS 2200 Advanced Copier', 'Sales': 17499.95, 'Quantity': 5, 'Discount': 0.0, 'Profit': 8399.976}
{'_id': ObjectId('68fc95844a687946d45bd328'), 'Row ID': 8154, 'Order ID': 'CA-2017-140151', 'Order Date': '3/23/2017', 'Ship Date': '3/25/2017', 'Ship Mode': 'First Class', 'Customer ID': 'RB-19360', 'Customer Name': 'Raymond Buch', 'Segment': 'Consumer', 'Country': 'United States', 'City': 'Seattle', 'State': 'Washington', 'Postal Code': 98115, 'Region': 'West', 'Product ID': 'TEC-CO-10004722', 'Category': 'Technology', 'Sub-Category': 'Copiers', 'Product Name': 'Canon imageCLASS 2200 Advanced Copier', 'Sales': 13999.96, 'Quantity': 4, 'Discount': 0.0, 'Profit': 6719.9808}
{'_id': ObjectId('68fc95844a687946d45bc3ad'), 'Row ID': 4191, 'Order ID': 'CA-2017-166709', 'Order Date': '11/17/2017', 'Ship Date': '11/22/2017', 'Ship Mode': 'Standard Class', 'Customer ID': 'HL-15040', 'Customer Name': 'Hunter Lopez', 'Segment': 'Consumer', 'Country': 'United States', 'City': 'Newark', 'State': 'Delaware', 'Postal Code': 19711, 'Region': 'East', 'Product ID': 'TEC-CO-10004722', 'Category': 'Technology', 'Sub-Category': 'Copiers', 'Product Name': 'Canon imageCLASS 2200 Advanced Copier', 'Sales': 10499.97, 'Quantity': 3, 'Discount': 0.0, 'Profit': 5039.9856}


7) Updated 1538 documents: Ship Mode changed to 'Premium Class'.

8) Deleted 4849 documents where Sales < 50.

9) Total sales per region:
{'_id': 'Central', 'TotalSales': 479611.8458}
{'_id': 'South', 'TotalSales': 376023.312}
{'_id': 'West', 'TotalSales': 694686.6195}
{'_id': 'East', 'TotalSales': 651137.705}


10) Distinct Ship Modes: ['Premium Class', 'Same Day', 'Second Class', 'Standard Class']

11) Number of orders per Category:
{'_id': 'Technology', 'OrderCount': 1496}
{'_id': 'Furniture', 'OrderCount': 1573}
{'_id': 'Office Supplies', 'OrderCount': 2076}


🎉 All practical tasks completed successfully!
"""