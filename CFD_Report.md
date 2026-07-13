# F1 Front Wing Wake Comparison: Outwash vs. Inwash Design
**A CFD Study on Pre-2026 vs. 2026 Technical Regulations**

---

## 1. Problem Framing & Aerodynamic Context

F1's technical regulations undergo a major overhaul in 2026. One of the primary goals is to improve overtaking by reducing the aerodynamic wake ("dirty air") left behind a leading car. 

### The Pre-2026 "Outwash" Philosophy
In the regulations leading up to 2026, teams optimized front wings to generate **outwash**. Outwash uses curved wing elements and angled endplates to push the highly turbulent wake of the front wheels outward, away from the car body. While this maximizes the aerodynamic efficiency of the generating car by keeping dirty air away from its floor and sidepods, it creates a very wide, turbulent wake that propagates far downstream. A following car attempting to corner behind it experiences a severe loss of downforce (up to 30–40%), making close racing extremely difficult.

### The 2026 "Inwash" Philosophy
The 2026 regulations mandate simpler front wings with endplates angled inward to promote **inwash**. Rather than pushing the wheel wake outboard, the air is directed inward toward the car centerline. The goal is to draw the wheel wake into the low-pressure region behind the car and under the rear wing, where it can be thrown high into the air, leaving a cleaner path for following cars.

This project quantifies the difference in wake characteristics and aerodynamic coefficients between these two philosophies using 3D RANS CFD.

---

## 2. Numerical Methodology

A simplified 3D half-car front wing and front wheel assembly was modeled to focus purely on the wing-wheel interaction.

### Geometry
*   **Wing**: Inverted cambered airfoil profile (NACA 4412) rotated at an $8^\circ$ angle of attack. Chord length $C = 0.25\text{ m}$, span $S = 0.25\text{ m}$. Ground clearance is $0.03\text{ m}$ (12% of chord).
*   **Outwash Endplate (Geometry A)**: 5 mm thick plate angled outward at $7.6^\circ$ ($y$ shifts from $0.25\text{ m}$ to $0.29\text{ m}$).
*   **Inwash Endplate (Geometry B)**: 5 mm thick plate angled inward at $7.6^\circ$ ($y$ shifts from $0.25\text{ m}$ to $0.21\text{ m}$).
*   **Wheel**: 3D cylinder representing a stationary tire (diameter $D = 0.30\text{ m}$, width $W = 0.15\text{ m}$) centered at $x = 0.45\text{ m}$ ($0.20\text{ m}$ behind the wing trailing edge), offset outboard at $y = 0.355\text{ m}$.

### Computational Domain
The domain was sized according to standard external aerodynamics guidelines:
*   **Inlet**: $1.25\text{ m}$ upstream of the wing leading edge ($5 \times \text{chord}$).
*   **Outlet**: $3.0\text{ m}$ downstream of the wheel trailing edge ($12 \times \text{chord}$).
*   **Domain Width**: $1.5\text{ m}$ (symmetry plane at $y = 0.0\text{ m}$).
*   **Domain Height**: $1.2\text{ m}$.
*   **Blockage Ratio**: $\approx 3.6\%$, well below the recommended $5\%$ limit.

```
                  ================== SKY (Slip) ==================
                  |                                              |
                  |                                              |
    Inlet (30m/s) ->         Wing     Wheel     ---> Wake        -> Outlet (p=0)
                  |          [==]      ( )                       |
                  ================= GROUND (Moving) ==============
```

### Boundary Conditions
*   **Inlet**: Uniform velocity $U = 30\text{ m/s}$ (approx. $108\text{ km/h}$). Turbulence intensity $I = 1\%$, length scale $L = 0.0175\text{ m}$ ($k = 0.135\text{ m}^2/\text{s}^2$, $\omega = 38.3\text{ s}^{-1}$).
*   **Outlet**: Fixed static pressure $p = 0\text{ Pa}$.
*   **Symmetry Plane ($y=0$)**: Symmetry boundary condition.
*   **Side & Sky**: Slip walls.
*   **Ground**: Moving wall with translation velocity $U_g = (30, 0, 0)\text{ m/s}$ to simulate a rolling road.
*   **Wing, Endplate, Wheel**: No-slip walls.

### Solver & Turbulence Modeling
*   **Solver**: Steady-state RANS using `simpleFoam` (SIMPLEC algorithm).
*   **Turbulence Model**: $k$-$\omega$ SST (Shear Stress Transport) model, which is the industry standard for aerodynamic flows with adverse pressure gradients and separation.
*   **Wall Treatment**: Wall functions (`kqRWallFunction`, `omegaWallFunction`, `nutkWallFunction`) with target $y^+$ in the log-law region ($30 < y^+ < 150$).

---

## 3. Mesh Independence Study

An automated grid convergence study was conducted using three refinement levels (Coarse, Medium, Fine). The background mesh resolution was refined by a ratio of $r = 1.5$ per dimension, and surface/region refinement levels in `snappyHexMesh` were adjusted accordingly.

### Mesh Statistics
*   **Coarse**: $\approx 54,000$ cells
*   **Medium**: $\approx 142,000$ cells
*   **Fine**: $\approx 385,000$ cells

### Aerodynamic Coefficients Convergence
Force coefficients $C_d$ (drag) and $C_l$ (lift) are calculated using the wing chord and span reference area $A_{ref} = 0.0625\text{ m}^2$ and reference velocity $U_{inf} = 30\text{ m/s}$.

| Design | Mesh Level | Cell Count | Drag Coeff ($C_d$) | Lift Coeff ($C_l$) | $\Delta C_d$ (%) | $\Delta C_l$ (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Outwash** | Coarse | 53,840 | 0.7450 | -0.5620 | — | — |
| **Outwash** | Medium | 141,920 | 0.7230 | -0.5840 | -2.95% | +3.91% |
| **Outwash** | Fine | 384,750 | 0.7180 | -0.5910 | -0.69% | +1.20% |
| **Inwash** | Coarse | 54,120 | 0.7980 | -0.5050 | — | — |
| **Inwash** | Medium | 142,280 | 0.7760 | -0.5280 | -2.76% | +4.55% |
| **Inwash** | Fine | 385,410 | 0.7710 | -0.5340 | -0.64% | +1.14% |

*Note: Negative $C_l$ represents downforce.*

### Convergence Analysis
Both cases show excellent asymptotic convergence. The change in coefficients from Medium to Fine is below $1\%$ for drag and close to $1.2\%$ for lift. This indicates that the Fine mesh is sufficiently independent of the grid resolution for engineering comparison.

---

## 4. Wake Comparison Results (Fine Mesh)

The comparison of aerodynamic coefficients and wake characteristics reveals the fundamental trade-offs between the two designs.

### Aerodynamic Performance Comparison
1.  **Downforce ($C_l$)**: The Outwash wing generates **$10.7\%$ more downforce** ($C_l = -0.5910$) than the Inwash wing ($C_l = -0.5340$). This is because the outwash endplate directs flow outward, reducing the pressure block effect of the front tire and allowing the wing suction side to perform more efficiently near the tip.
2.  **Drag ($C_d$)**: The Outwash wing assembly has **$7.4\%$ lower drag** ($C_d = 0.7180$) than the Inwash assembly ($C_d = 0.7710$). The outwash endplate successfully routes the high-speed air around the outboard side of the tire face. In contrast, the inwash endplate directs air inward, squeezing it into the gap between the tire and the centerline. This creates a high-pressure stagnation zone in front of the tire, increasing pressure drag.

### Wake Characteristics & Streamlines
The post-processed streamlines and velocity deficit slices highlight why the regulations changed:

*   **Wake Deflection (Top-Down Streamlines)**:
    *   *Outwash case*: Streamlines passing the endplate are deflected outward (positive $y$ direction). This pushes the tire's wake further outboard, creating a wide "dirty air" envelope that expands as it moves downstream.
    *   *Inwash case*: Streamlines are drawn inward (negative $y$ direction) toward the centerline. The high-energy flow is steered into the space behind the wing and inboard of the tire.
*   **Wake Width & Velocity Deficit ($1 - U_x/U_{inf}$)**:
    *   Slices at $x = 0.90\text{ m}$ (1.0 wheel diameter behind the tire) show that the **Outwash wake is wider** and shifted outboard. A following car would have to steer significantly wide of the corner apex to avoid this wake.
    *   The **Inwash wake is narrower** spanwise. The highly turbulent wheel wake is pulled inboard, which aligns it to interact with the floor and diffuser flow. On a full car, this allows the low-pressure wake to be sucked under the chassis and thrown high over the following car by the rear wing and diffuser.

---

## 5. Study Limitations & Future Extensions

While this portfolio project successfully quantifies the core physics of outwash vs. inwash designs, it contains several simplifying assumptions:

1.  **Non-Rotating Wheel**: The wheel was modeled as a static cylinder. In a real car, the rotation of the wheel pulls flow over the top of the tire, creating a strong down-wash and separating the wake earlier.
    *   *Improvement (Stretch Goal)*: Use Multi-Reference Frame (MRF) or sliding meshes to model wheel rotation ($U_{rot} = \omega \times r$).
2.  **Simplified Geometry**: The wing consists of a single element with a flat endplate. Real F1 front wings have 3–4 elements with highly complex flap profiles and endplate channels.
    *   *Improvement*: Integrate a multi-element wing profile with slot-lips.
3.  **Steady RANS Solver**: Steady-state `simpleFoam` models turbulence statistically. The F1 wake is highly transient, characterized by vortex shedding and turbulent eddy propagation.
    *   *Improvement*: Run transient DDES (Delayed Detached Eddy Simulation) or LES (Large Eddy Simulation) to resolve transient wake dynamics.
4.  **No Downstream Car**: The wake was measured in isolation.
    *   *Improvement (Stretch Goal)*: Set up a two-car following scenario to directly measure the drag and lift loss on a second car trailing at $0.5\text{ s}$, $1.0\text{ s}$, and $1.5\text{ s}$ intervals.
