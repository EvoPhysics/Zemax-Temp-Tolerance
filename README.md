# 基于 Python ZOS-API 的 Zemax 自动化热分析与 AI 预测

本项目展示了如何结合 **Zemax OpticStudio API (ZOS-API)** 与 **Python** 进行自动化的光学系统热分析。我们不仅实现了自动化的数据采集，还利用机器学习（多项式回归）建立了光斑大小随温度变化的预测模型。

## 🌟 核心功能

1.  **自动化连接**：自动连接到正在运行的 Zemax OpticStudio 实例。
2.  **热分析扫描**：
    *   支持标准的 3 点热分析（20°C, 50°C, 80°C）。
    *   支持自定义范围（如 0°C - 100°C）的全自动温度扫描。
3.  **精准仿真**：摒弃简单的评价函数（Merit Function）操作数，采用 `StandardSpot` Analysis 直接调用 Zemax 内核进行光斑分析，确保结果与 GUI 界面完全一致。
4.  **数据采集 (The Harvest)**：批量生成随机温度点，自动运行仿真并采集 RMS 光斑半径数据。
5.  **AI 建模与预测**：基于采集的数据训练多项式回归模型（R2 Score > 0.99），实现对任意温度下光斑大小的毫秒级预测。

## 📂 项目结构

```
.
├── 01_System_Connection.py          # [基础] 测试 ZOS-API 连接
├── 02_Thermal_Analysis_3Point.py    # [仿真] 标准 3 点热分析 (20/50/80°C)
├── 03_Thermal_Analysis_Sweep_Full.py# [仿真] 0-100°C 全范围迭代扫描
├── 04_Debug_Material_Catalog.py     # [工具] 验证内部材料库热数据读取
├── 05_Data_Harvest_Random.py        # [数据] 批量采集 200 组随机温度数据
├── 06_Model_Training_Linear.py      # [AI] 训练多项式回归模型并评估
├── 07_Model_Prediction.py           # [AI] 使用模型预测特定温度 (如 73.5°C) 的结果
├── models/                          # [资源] 透镜文件与数据集
│   ├── Cooke_Triplet_Base.zmx       # 基础柯克三片式镜头文件
│   └── dataset_v1.csv               # 采集到的温度-光斑数据集
├── images/                          # [资源] 结果图表
│   └── model_v1_fit.png             # AI 模型拟合曲线图
└── README.md                        # 项目说明文档
```

## 🛠️ 环境要求

*   **Zemax OpticStudio**: Professional 或 Premium 版本（需支持 API）。
*   **Python**: 3.7+
*   **依赖库**:
    ```bash
    pip install pythonnet pandas numpy scikit-learn matplotlib
    ```

## 🚀 快速开始

### 1. 准备工作
打开 Zemax OpticStudio 并确保处于交互模式（Interactive Mode）。

### 2. 运行仿真与采集
```bash
# 测试连接
python 01_System_Connection.py

# 运行基础热分析
python 02_Thermal_Analysis_3Point.py

# 批量采集数据 (生成 dataset_v1.csv)
python 05_Data_Harvest_Random.py
```

### 3. AI 训练与预测
```bash
# 训练模型 (输出 R2 Score 和拟合曲线)
python 06_Model_Training_Linear.py

# 预测特定温度 (如 73.5°C)
python 07_Model_Prediction.py
```

## 📊 关键成果

*   **仿真精度**：通过迭代更新多重结构（MCE）的方法，解决了 API 调用中的状态更新问题，成功复现了 Zemax GUI 的热分析结果。
*   **模型性能**：针对 Cooke Triplet 镜头的热离焦特性，二阶多项式回归模型达到了 **R2 > 0.995** 的精度，预测误差小于 **0.1 微米**。

## 📝 许可证

MIT License
