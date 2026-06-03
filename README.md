# Zemax 自动化热分析与公差预测 | Automated Zemax Thermal & Tolerance Analysis

> 基于 ZOS-API 与 Scikit-Learn MLP 神经网络的 Cooke 三片镜热-公差耦合建模与毫秒级光斑预测。
> Cooke triplet thermal-tolerance coupled modeling and millisecond-level spot prediction powered by ZOS-API and a Scikit-Learn MLP.

---

## 🌟 核心功能 | Core Features

- 🔌 **ZOS-API 自动化连接 | Automated ZOS-API Connection** — 从 Windows 注册表定位 Zemax 根目录，加载 `ZOSAPI_NetHelper.dll`，校验 API 许可证后建立独立进程连接。
  *Locates Zemax via Windows registry, loads the .NET helper, validates the API license, and spawns a standalone process.*

- 🌡️ **多模式热分析 | Multi-Mode Thermal Analysis** — 支持标准三点（20°C / 50°C / 80°C）以及 0–100°C 全范围 10°C 步长扫描，并自动读取 SCHOTT 等材料库的热数据（TCE、D0、dn/dT）。
  *Supports the canonical 3-point sweep and a full 0–100°C scan in 10°C steps; auto-loads SCHOTT thermal constants (TCE, D0, dn/dT).*

- 🎲 **蒙特卡洛热+公差耦合 | Monte Carlo Thermal + Tolerance Coupling** — 在每片透镜前后自动插入 Coordinate Break 与 Pickup Solve，叠加 12 自由度（D<sub>x</sub>, D<sub>y</sub>, T<sub>x</sub>, T<sub>y</sub> × 3）与温度扰动，1000 次随机仿真。
  *Inserts Coordinate Breaks with Pickup Solves around each element, perturbs 12 DOF (D<sub>x</sub>, D<sub>y</sub>, T<sub>x</sub>, T<sub>y</sub> for 3 lenses) plus temperature, runs 1000 random trials.*

- 🧠 **13 维 MLP 回归 | 13-D MLP Regressor** — Scikit-Learn `MLPRegressor` 结构 `13 → 64 → 64 → 1`，输入标准化后 Adam 训练，毫秒级推理替代 Zemax 光线追迹。
  *Scikit-Learn `MLPRegressor` with architecture `13 → 64 → 64 → 1`, trained with Adam on standardized inputs; inference runs in milliseconds.*

- 📈 **高保真数据集 | High-Fidelity Datasets** — 自动采集 V1（200 组纯温度）与 V2（1000 组热+公差）双版本 CSV，覆盖 −40°C ~ 85°C 工业温区。
  *Auto-harvests two CSV datasets: V1 (200 temperature-only samples) and V2 (1000 thermal+tolerance samples), covering −40°C to 85°C industrial range.*

- 🧪 **闭环验证 | Closed-Loop Verification** — 支持将数据集中特定工况回写为 `.zmx` 文件，可在 Zemax 中手动打开对比 AI 预测值与真实光线追迹结果。
  *Reproduces any dataset case as a `.zmx` lens file so engineers can open it in Zemax and compare AI prediction against ground-truth ray tracing.*

---

## 📂 项目结构 | Project Structure

```
Zemax-Temp-Tolerance/
├── 01_System_Connection.py          # [基础] ZOS-API 连接测试 / Connectivity check
├── 02_Thermal_Analysis_3Point.py    # [仿真] 3 点热分析 (20/50/80°C) / 3-point thermal analysis
├── 03_Thermal_Analysis_Sweep_Full.py# [仿真] 0-100°C 全范围扫描 / Full 0-100°C sweep
├── 04_Debug_Material_Catalog.py     # [工具] 材料库热数据校验 / Material catalog verification
├── 05_Data_Harvest_Random.py        # [数据] 随机 200 组温度数据 (V1) / V1 dataset
├── 06_Model_Training_Linear.py      # [AI] 多项式回归 (V1) / Polynomial regression
├── 07_Model_Prediction.py           # [AI] V1 模型推理 / V1 inference
├── 08_Monte_Carlo_Tolerance.py      # [仿真] 1000 组蒙特卡洛 (V2) / 1000-run Monte Carlo
├── 09_Model_Training_Sklearn_MLP.py # [AI] MLP 神经网络训练 / MLP training
├── 10_Generate_Verification_ZMX.py  # [工具] 验证用例 ZMX 导出 / Verification .zmx export
├── models/                          # [资源] 透镜、训练集、模型权重
│   ├── Cooke_Triplet_Base.zmx       # 基础镜头 / base lens
│   ├── dataset_v1.csv               # 200 组纯温度数据 / 200-sample temperature dataset
│   ├── dataset_v2_tolerance.csv     # 1000 组 热+公差 数据 / 1000-sample thermal+tolerance dataset
│   ├── optical_mlp_sklearn.pkl      # 训练好的 MLP 模型 / trained MLP
│   └── input_scaler.pkl             # 输入标准化器 / input StandardScaler
├── images/                          # [资源] 训练曲线与散点图 / Plots and figures
└── README.md                        # 本文件 / this file
```

---

## 🛠 环境要求 | Requirements

| 项目 / Item | 要求 / Requirement |
|---|---|
| 操作系统 / OS | Windows 10 / 11（ZOS-API 仅支持 Windows） |
| Zemax OpticStudio | Professional 或 Premium 版本（需启用 API 许可） |
| Python | 3.7+ （推荐 Anaconda） |
| 关键依赖 / Key deps | `pythonnet` `pandas` `numpy` `scikit-learn` `matplotlib` `joblib` |
| 镜头基准 / Lens | 自带 `Cooke_Triplet_Base.zmx`（40° 视场） |

安装依赖 / Install dependencies:

```bash
pip install pythonnet pandas numpy scikit-learn matplotlib joblib
```

---

## 🚀 快速开始 | Quick Start

三步跑通从仿真到 AI 预测的完整链路。  
*Three steps from simulation to AI prediction.*

### Step 1 · 准备 Zemax | Prepare Zemax
打开 Zemax OpticStudio 并保持交互模式（不要用独占模式）。  
*Launch Zemax OpticStudio in Interactive (non-exclusive) mode.*

### Step 2 · 跑 1000 组蒙特卡洛 | Run 1000 Monte Carlo Trials
```bash
python 08_Monte_Carlo_Tolerance.py
# 输出 models/dataset_v2_tolerance.csv (Temp + 12 DOF + RMS_Spot)
```
*This populates `dataset_v2_tolerance.csv` with 1000 rows: 1 temperature + 12 tolerance DOF + RMS spot radius.*

### Step 3 · 训练 MLP 神经网络 | Train the MLP
```bash
python 09_Model_Training_Sklearn_MLP.py
# 输出 R² / MSE, 保存 optical_mlp_sklearn.pkl + input_scaler.pkl
```
*Prints R² and MSE, dumps the trained model and scaler to `models/`.*

> 💡 想验证 AI 是否靠谱？运行 `10_Generate_Verification_ZMX.py` 会在 `models/Verification_Case_2.zmx` 写出一个可手动打开的镜头文件。  
> *To sanity-check the model, run `10_Generate_Verification_ZMX.py` — it writes `models/Verification_Case_2.zmx` that you can open in Zemax.*

---

## 📊 关键成果 | Key Results

| 指标 / Metric | 数值 / Value | 含义 / Meaning |
|---|---|---|
| 数据集规模 / Dataset size | **1000 组 / runs** | V2 蒙特卡洛热+公差仿真 / V2 Monte Carlo |
| 输入维度 / Input dim | **13** | 1 温度 + 3 透镜 × 4 公差 / 1 temp + 3 lenses × 4 DOF |
| MLP 结构 / MLP arch | **13 → 64 → 64 → 1** | 两层隐藏层 ReLU / two hidden ReLU layers |
| R² Score（测试集 / test set） | **0.989** | 方差解释率 / variance explained |
| MSE（测试集 / test set） | **2.53** µm² | 均方误差 / mean squared error |
| 推理耗时 / Inference | **毫秒级 / ms-level** | 替代 Zemax 光线追迹 / replaces ray tracing |
| 温区 / Range | **−40°C ~ 85°C** | 工业级 / industrial-grade |

> 对比基线：纯温度 1 维多项式回归（R² ≈ 0.9）已不足以刻画多自由度耦合效应，MLP 把 12 个公差维度也压进了 0.989 R² 的同一网络。  
> *Pure-temperature 1-D polynomial regression (R² ≈ 0.9) under-fits the multi-DOF coupling; the MLP lifts 12 extra tolerance dimensions into the same 0.989 R² surface.*

---

## 📚 引用 | Citation

如果本项目对你的研究或工程有帮助，请引用：  
*If this project helps your research or engineering work, please cite:*

```bibtex
@software{zemax_temp_tolerance_2026,
  author    = {EvoPhysics},
  title     = {{Zemax-Temp-Tolerance}: Automated Thermal and Tolerance Analysis
               of Cooke Triplet via {ZOS-API} and {Scikit-Learn} {MLP}},
  year      = {2026},
  version   = {1.0.0},
  url       = {https://github.com/EvoPhysics/Zemax-Temp-Tolerance},
  note      = {Cooke triplet; 1000-run Monte Carlo; R\textsuperscript{2}=0.989; MSE=2.53}
}
```

---

## 📝 License

本项目基于 **MIT License** 开源 — 详见 `LICENSE` 文件（如未随附请在根目录创建）。  
*Released under the **MIT License** — see `LICENSE` (create it at the repo root if not present).*

---

<p align="center">
  <sub>Built with care by the EvoPhysics team · 用心做光学 · 2026</sub>
</p>
