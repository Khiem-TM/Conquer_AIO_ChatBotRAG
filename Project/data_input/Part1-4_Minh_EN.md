# Research and Implementation of Data Visualization using Python

## 1. Introduction: The Importance of Data Visualization

In modern data analysis, visualization is not merely presenting numbers as images, but an essential process to transform raw information into useful knowledge. As Cole Nussbaumer Knaflic stated in *Storytelling With Data: A Data Visualization Guide for Business Professionals*:

> "Data visualization is the intersection of science and art. It's not just about creating pretty charts, but about understanding context, choosing the right display, and eliminating clutter to focus on the core message."

Ignoring the visualization step and relying solely on aggregate statistical indicators can lead to serious errors in identifying the nature of phenomena and making biased decisions.

### 1.1. Empirical Analysis through Anscombe's Quartet

To demonstrate the importance of observing data visually, statistician Francis Anscombe constructed four datasets (denoted as I, II, III, IV). Although these datasets have completely different data point structures, they possess nearly identical descriptive statistical characteristics.

#### Raw Data and Descriptive Statistics
Before observing through charts, reviewing raw data and statistical indicators is the first step in the analysis process. The table below details the $(x, y)$ coordinate pairs of the four datasets:

| No. | Set I (x) | Set I (y) | Set II (x) | Set II (y) | Set III (x) | Set III (y) | Set IV (x) | Set IV (y) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 10.0 | 8.04 | 10.0 | 9.14 | 10.0 | 7.46 | 8.0 | 6.58 |
| 2 | 8.0 | 6.95 | 8.0 | 8.14 | 8.0 | 6.77 | 8.0 | 5.76 |
| 3 | 13.0 | 7.58 | 13.0 | 8.74 | 13.0 | 12.74 | 8.0 | 7.71 |
| 4 | 9.0 | 8.81 | 9.0 | 8.77 | 9.0 | 7.11 | 8.0 | 8.84 |
| 5 | 11.0 | 8.33 | 11.0 | 9.26 | 11.0 | 7.81 | 8.0 | 8.47 |
| 6 | 14.0 | 9.96 | 14.0 | 8.10 | 14.0 | 8.84 | 8.0 | 7.04 |
| 7 | 6.0 | 7.24 | 6.0 | 6.13 | 6.0 | 6.08 | 8.0 | 5.25 |
| 8 | 4.0 | 4.26 | 4.0 | 3.10 | 4.0 | 5.39 | 19.0 | 12.50 |
| 9 | 12.0 | 10.84 | 12.0 | 9.13 | 12.0 | 8.15 | 8.0 | 5.56 |
| 10 | 7.0 | 4.82 | 7.0 | 7.26 | 7.0 | 6.42 | 8.0 | 7.91 |
| 11 | 5.0 | 5.68 | 5.0 | 4.74 | 5.0 | 5.73 | 8.0 | 6.89 |

Basic statistical indicators calculated for all four datasets show similarity up to the second decimal place:

| Statistical Indicator | Value |
| :--- | :--- |
| Number of Observations ($n$) | 11 |
| Mean of variable $x$ ($\bar{x}$) | 9.0 |
| Mean of variable $y$ ($\bar{y}$) | 7.50 |
| Variance of variable $x$ ($s^2_x$) | 11.0 |
| Variance of variable $y$ ($s^2_y$) | 4.12 |
| Pearson Correlation Coefficient ($r$) | 0.816 |
| Linear Regression Equation | $y = 3.00 + 0.500x$ |

#### Visualization Results
However, when plotting scatter plots combined with regression lines, the fundamental differences between the datasets are clearly revealed:

* **Dataset I:** Follows a linear model with a certain standard deviation around the regression line. This is an ideal case for simple regression algorithms.
* **Dataset II:** Data shows a clear non-linear relationship (parabolic). Applying a linear model here is inappropriate and leads to large prediction errors.
* **Dataset III:** A perfect linear relationship exists but is skewed by an outlier far from the main axis, significantly altering the slope of the regression line.
* **Dataset IV:** Shows an unusual data structure where $x$ values are constant (except for one), meaning the regression model does not correctly reflect the actual trend of most data.

The conclusion from this experiment confirms that: Data visualization is a mandatory step to verify statistical assumptions before proceeding with in-depth analysis.

### 1.2. Python Library Ecosystem: Matplotlib and Seaborn

In the Python programming environment, visualization implementation is primarily supported by two central libraries:

* **Matplotlib:** Acts as the foundational (low-level) library, providing APIs to adjust detailed chart structures, from coordinate axes to complex geometric properties.
* **Seaborn:** A high-level library built on Matplotlib. It is optimized for statistical analysis, directly supports Pandas DataFrame structures, and automates graphic aesthetics, making the workflow more efficient.

## 5. Conclusion and Optimization Principles

### 5.1. Choosing the Right Chart Type
Choosing the wrong chart type can lead to misunderstandings about the scale or relationship of the data.
* **Limit Pie Charts:** In professional analysis, pie charts are often restricted, especially when the number of categories exceeds 3-5 groups. Human visual ability to perceive differences in angular area is poorer than comparing lengths (bar charts).
* **Recommendation:** Use Horizontal Bar Charts as an alternative when there are many categories or long category names, ensuring readability and accurate comparison.

### 5.2. Principle of Minimalism and Removing Noise (Chartjunk)
Based on Edward Tufte's theory, the performance of a chart is measured by the "Data-Ink ratio".
* **Eliminate Chartjunk:** Remove overly dark gridlines, unnecessary 3D shadow effects, or cluttered borders.
* **Focus on Core Information:** Keeping the chart clean helps viewers immediately focus on important trends or outliers.

### 5.3. Strategy for Using Colors and Palettes
Colors in Seaborn and Matplotlib are not just aesthetic but functional:
* **Use Color Palettes:** Choose palettes suitable for the nature of the data:
    * *Qualitative palettes:* Used for categorical data without order.
    * *Sequential palettes:* Used for data with continuous variation (low to high).
    * *Diverging palettes:* Used to emphasize differences from a central point (e.g., negative and positive growth).

### 5.4. Summary
Data visualization with Seaborn and Matplotlib is not just about executing source code, but a thinking process to choose the most honest method of expression for the nature of the data. Adhering to the principles of simplicity and accuracy will help analysts convert complex datasets into information with high practical value.
