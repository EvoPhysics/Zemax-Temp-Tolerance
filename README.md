# 基于 Python ZOS-API 的 Zemax 自动化热分析与 AI 预测

本项目展示了如何结合 **Zemax OpticStudio API (ZOS-API)** 与 **Python** 进行自动化的光学系统热分析与公差分析。我们不仅实现了自动化的数据采集，还利用机器学习（MLP 神经网络）建立了高精度的光斑预测模型，实现了“虚拟 Zemax”的毫秒级推理。

## 🌟 核心功能

1.  **自动化连接**：自动连接到正在运行的 Zemax OpticStudio 实例。
2.  **热分析扫描**：
    *   支持标准的 3 点热分析（20°C, 50°C, 80°C）。
    *   支持自定义范围（如 0°C - 100°C）的全自动温度扫描。
3.  **蒙特卡洛公差分析 (Monte Carlo Tolerance)**：
    *   **热+公差耦合**：模拟真实的物理环境，同时考虑**温度变化**与**装配公差**（透镜的偏心 Decenter 与倾斜 Tilt）。
    *   **自动化建模**：脚本自动在透镜前后插入 Coordinate Break 表面，并设置 Pickup Solve。
    *   **自动对焦**：模拟实际装调过程，每次扰动后自动执行 Quick Focus。
4.  **数据采集 (The Harvest)**：批量生成随机工况，自动运行仿真并采集 RMS 光斑半径数据。
5.  **AI 建模与预测**：
    *   **MLP 神经网络**：使用 Scikit-Learn 搭建多层感知机（13 -> 64 -> 64 -> 1）。
    *   **高精度**：在“热+公差”复杂工况下，模型 R2 Score 达到 **0.989**，MSE 仅为 **2.53**。

## 📂 项目结构

```
.
├── 01_System_Connection.py          # [基础] 测试 ZOS-API 连接
├── 02_Thermal_Analysis_3Point.py    # [仿真] 标准 3 点热分析
├── 03_Thermal_Analysis_Sweep_Full.py# [仿真] 0-100°C 全范围迭代扫描
├── 04_Debug_Material_Catalog.py     # [工具] 验证内部材料库热数据读取
├── 05_Data_Harvest_Random.py        # [数据] 批量采集 200 组随机温度数据 (V1)
├── 06_Model_Training_Linear.py      # [AI] 训练多项式回归模型 (V1)
├── 07_Model_Prediction.py           # [AI] V1 模型预测脚本
├── 08_Monte_Carlo_Tolerance.py      # [仿真] 蒙特卡洛公差分析 (生成 dataset_v2)
├── 09_Model_Training_Sklearn_MLP.py # [AI] 训练 MLP 神经网络拟合复杂公差数据
├── 10_Generate_Verification_ZMX.py  # [工具] 生成特定工况的 ZMX 文件以供人工验证
├── models/                          # [资源] 透镜文件、数据集与模型权重
│   ├── Cooke_Triplet_Base.zmx       # 基础镜头文件
│   ├── dataset_v2_tolerance.csv     # 1000组 热+公差 仿真数据
│   ├── optical_mlp_sklearn.pkl      # 训练好的神经网络模型
│   └── input_scaler.pkl             # 输入数据标准化器
├── images/                          # [资源] 结果图表
└── README.md                        # 项目说明文档
```

## 🛠️ 环境要求

*   **Zemax OpticStudio**: Professional 或 Premium 版本（需支持 API）。
*   **Python**: 3.7+ (推荐使用 Anaconda)
*   **依赖库**:
    ```bash
    pip install pythonnet pandas numpy scikit-learn matplotlib
    ```

## 🚀 快速开始

### 1. 准备工作
打开 Zemax OpticStudio 并确保处于交互模式（Interactive Mode）。

### 2. 运行蒙特卡洛仿真
```bash
# 运行 1000 次蒙特卡洛分析 (热+公差)
# 自动生成 dataset_v2_tolerance.csv
python 08_Monte_Carlo_Tolerance.py
```

### 3. 训练 AI 模型
```bash
# 训练 MLP 神经网络
# 输出 R2 Score 并保存模型至 models/
python 09_Model_Training_Sklearn_MLP.py
```

### 4. 验证结果
```bash
# 生成特定工况的 ZMX 文件 (Verification_Case_2.zmx)
# 你可以在 Zemax 中打开此文件，对比 AI 预测值与 Zemax 真实仿真值
python 10_Generate_Verification_ZMX.py
```

## 📊 关键成果

*   **复杂物理场模拟**：成功实现了 Python 对 Zemax 坐标断点（Coordinate Break）和求解类型（Solve Type）的深度控制，模拟了真实的装配误差。
*   **AI 替代仿真**：对于包含 13 个自由度（温度 + 12个公差变量）的复杂系统，神经网络模型（R2=0.989）可以替代耗时的光线追迹，实现毫秒级性能评估。

## 📝 许可证

MIT License
