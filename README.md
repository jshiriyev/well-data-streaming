# well-data-streaming – Python Data Structures for Well-Centric Applications

**WellX** is a Python package providing **modular, immutable-ish data structures** for managing well-related information across the entire lifecycle of a well — from **location surveys** and **formation tops** to **drilling records**, **production surveillance**, and **formation evaluation**.

The package is built with:

* **Data integrity first** – strong validation rules
* **Web-app readiness** – efficient, immutable-friendly structures ideal for frameworks like Streamlit
* **Plotly integration** – for interactive visualization
* **Future DB connectivity** – planned integration with well databases
* **MIT License** – free for commercial and academic use

---

## ✨ Key Features

* **Geology-aware structures**:

  * `Survey` – store & transform wellbore trajectory data (MD/TVD, offsets, inclinations, azimuths)
  * `Tops` – manage formation tops with MD-based ordering, color mapping, and interval logic
* **Strict validation**:

  * Positive MD only, unique formation names, sorted data
  * Raises descriptive errors for invalid input
* **Convenience methods**:

  * Convert between MD and TVD
  * Query formation intervals
  * Find which formation contains a given depth
* **Facecolor mapping** for geological visualization
* **Interoperable** with numpy and pandas without forcing dependencies

---

## 📦 Installation

```bash
pip install wellx
```

---

## 🚀 Quick Start

```python
import numpy as np
from wellx import Survey, Tops

# Example 1: Create a well survey and get plan & section views
survey = Survey(
    MD=np.array([0, 500, 1000]),
    TVD=np.array([0, 450, 900]),
    DX=np.array([0, 100, 150]),
    DY=np.array([0, 300, 600]),
    INC=np.array([0, 10, 20]),
    AZI=np.array([0, 45, 90])
)

print(survey.md2tvd([750]))  # interpolate TVD at MD=750

# Example 2: Manage formation tops
tops = Tops(
    formation=["Sand_A", "Shale_B", "Lime_C"],
    depth=[1200.0, 1850.5, 2500.0],
    facecolor={"Sand_A": "yellow", "Shale_B": "gray"}
)

print(tops.get_limit("Sand_A"))  # (1200.0, 1850.5)
print(tops.find_at_md(2000))     # "Shale_B"
```

---

## 📊 Visualizing with Plotly

```python
import plotly.express as px
import pandas as pd

df = pd.DataFrame({
    "MD": survey.MD,
    "TVD": survey.TVD
})

fig = px.line(df, x="MD", y="TVD", title="Wellbore Profile")
fig.show()
```

---

## 📂 Planned Data Structure Coverage

<img src="img/well_data.jpg">

---

## 📅 Roadmap

1. **Core Data Structures** – Survey, Tops, Production Rates
2. **Visualization Tools** – Plotly-based built-ins
3. **Database Connectivity** – optional integration with field data servers
4. **Streamlit App Templates** – deployable dashboards
5. **Export/Import Utilities** – CSV, LAS, JSON, and database connectors

---

## 🤝 Contributing

Contributions are welcome!

* Fork the repo
* Create a branch (`feature/my-feature`)
* Submit a pull request with clear description and tests

---

## 📜 License

MIT License – you are free to use, modify, and distribute this package commercially and academically.
See [LICENSE](LICENSE) for details.

---

## 📬 Contact

**Author:** Javid Shiriyev
📧 Email: [shiriyevcavid@gmail.com](mailto:shiriyevcavid@gmail.com)
🔗 LinkedIn: [linkedin.com/in/jshiriyev](https://www.linkedin.com/in/jshiriyev/)