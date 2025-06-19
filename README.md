
# 🚦 PATHPLUS MLight & SUMO Traffic Simulation

## 📌 About The Project

This project demonstrates how to build a traffic network using **SUMO (Simulation of Urban Mobility)**, simulate vehicle movements using **OpenStreetMap (OSM)** data, and implement a **Traffic Light System (TLS)** algorithm for smart signal control.

It includes:
- Building road networks from real-world maps  
- Generating random vehicle trips  
- Visualizing and simulating traffic  
- Running a Python-based TLS algorithm for signal optimization

---

## 🛠️ Built With

- [SUMO GUI](https://sumo.dlr.de/docs/Downloads.php)  
- [NETEDIT](https://sumo.dlr.de/docs/Netedit/index.html)  
- Python 3.x and libraries like:
  - `pandas`, `seaborn`, `matplotlib`, `numpy`, `sklearn`, `traci`

---

## 🚀 Getting Started

### ⚙️ Prerequisites

- Python 3.x
- SUMO installed and added to system PATH
- Working internet connection to download OSM data

---

## 🧰 Installation

### 1. Install SUMO & NETEDIT

- **SUMO GUI**: [https://sumo.dlr.de/docs/Downloads.php](https://sumo.dlr.de/docs/Downloads.php)  
- **NETEDIT**: [https://sumo.dlr.de/docs/Netedit/index.html](https://sumo.dlr.de/docs/Netedit/index.html)

---

## 💻 Usage

### Step-by-Step: Build and Simulate Network

#### 1. Export Map from OpenStreetMap
- Visit [https://www.openstreetmap.org](https://www.openstreetmap.org)
- Select your desired region
- Export it as `map.osm`

#### 2. Copy Typemap
Copy `osmNetconvert.typ.xml` from: C:\Program Files (x86)\Eclipse\Sumo\data\typemap to your working folder

#### 3. Convert OSM to SUMO Network
```bash
netconvert -osm-files map.osm -o test.net.xml -t osmNetconvert.typ.xml
```
#### 4. Import Polygons (Optional)

-   Visit [Polygon Import Guide](https://sumo.dlr.de/wiki/Networks/Import/OpenStreetMap)
    
-   Copy polygon type code and save it as `typemap.xml`
    

#### 5. Convert Polygon Data

```bash
`polyconvert --net-file test.net.xml --osm-files map.osm --type-file typemap.xml -o map.poly.xml`
```
#### 6. Generate Random Trips

-   Copy `randomTrips.py` from: `C:\Program Files  (x86)\Eclipse\Sumo\tools`to your working folder.
- Then run: 
```bash
python randomTrips.py -n test.net.xml -r map.rou.xml`
```
#### 7. Create SUMO Config File (`map.sumo.cfg`)

```bash
<configuration> 
<input> 
<net-file  value="test.net.xml"/> 
<route-files  value="map.rou.xml"/> 
<additional-files  value="map.poly.xml"/> 
</input> 
</configuration>`
```
#### 8. Run Simulation in SUMO GUI

-   Open **SUMO GUI**
    
-   Load `map.sumo.cfg`
    
-   Click **Run Simulation**


## 🔁 TLS Algorithm Execution

1. Extract Script Folder

 2. Open `xlmstype.py` in VSCode or any editor

 3. Create Virtual Environment
 ```bash
python -m venv venv
venv\Scripts\activate
 ```
 4. Install Required Packages
 ```bash
`pip install pandas seaborn matplotlib scikit-learn numpy  
 ```

> Note:  
> `traci` is included with SUMO  
> `os`, `time`, `collections` are built-in modules

5. Run TLS Script

 ```bash
`python xlmstype.py` 
 ```
 
#### Output Directory (Set in script)
 ```bash
`OUTPUT_DIR = "C:/Users/anura/OneDrive/Desktop/PLUS PATH/output"  print(f"Output files saved to {OUTPUT_DIR}")` 
 ```

----------

## 🗺️ Roadmap

-   SUMO GUI & NETEDIT setup
    
-   Import map and generate network
    
-   Create and simulate trips
    
-   Implement TLS script
    
-   Add real-time traffic adjustment logic
    
-   Visual performance dashboard (future work)
    

----------

## 🤝 Contributing

Contributions are welcome!  
To contribute:

1.  Fork the repo
    
2.  Create a new branch 
    
3.  Commit your changes
    
4.  Push to your branch
    
5.  Open a Pull Request
    

----------

## 📄 License

This project is for educational/research use.  
Refer to SUMO License for SUMO’s licensing terms.

----------

## 📬 Contact

**Author:** Anurag  
📧 Email: anufyianurag@gmail.com

## 🙏 Acknowledgments

-   [SUMO Documentation](https://sumo.dlr.de/docs/)
    
-   [OpenStreetMap](https://www.openstreetmap.org)
    
-   SUMO & TraCI contributors
    
-   Stack Overflow & GitHub Community
