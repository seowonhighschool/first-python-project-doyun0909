import tkinter as tk
from tkinter import ttk
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns

# 한글 폰트 설정 (Windows 기본 맑은 고딕)
plt.rc('font', family='Malgun Gothic')
plt.rc('axes', unicode_minus=False)
sns.set_theme(style="whitegrid", font="Malgun Gothic")

# 추진제 물성 데이터
propellants = {
    'Liquid Methane (CH4)': {
        'boiling_point': 111.6, 'latent_heat': 510.0, 'density': 422.6, 
        'maint_score': 85.0, 'density_score': 100.0
    },
    'Liquid Hydrogen (LH2)': {
        'boiling_point': 20.28, 'latent_heat': 446.0, 'density': 70.8, 
        'maint_score': 40.0, 'density_score': 16.8
    }
}

# 마우스 오버 전용 호버 툴팁 클래스
class HoverTooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#2c3e50", foreground="#ffffff", relief='solid', borderwidth=1,
                         font=("맑은 고딕", 9, "normal"), padx=8, pady=6)
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()

# 각 지표별 툴팁 설명
TOOLTIPS = {
    'thick': "단열재 두께 (mm)\n- 탱크로의 열유입량(Fourier's Law)을 결정하는 핵심 변수입니다.\n- 두께가 증가할수록 BOG 손실은 감소하나 구조 질량이 증가합니다.",
    'time': "발사 대기 시간 (Hours)\n- 충전 완료 후 발사 전까지 발사대에서 대기하는 시간입니다.\n- 시간이 누적될수록 증발 가스(BOG) 총 손실량이 비례하여 증가합니다.",
    'w_bog': "BOG 손실률 가중치 (Weight)\n- 전체 평가 모델에서 '증발 손실 방어 성능'이 차지하는 상대적 중요도입니다.",
    'w_maint': "정비 및 운용성 가중치 (Weight)\n- 재사용 정비 주기, 그을음(Coking) 발생 여부, 극저온 취급 난이도의 중요도입니다.",
    'w_dens': "연료 밀도 효율 가중치 (Weight)\n- 추진제 밀도에 따른 탱크 탑재체적 및 구조 질량 소형화 효과의 중요도입니다."
}

class ProfessionalSimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("극저온 추진제 BOG 및 가중치 기반 재사용 적합성(RS) 평가 시뮬레이터")
        self.root.geometry("1150x750")
        self.root.configure(bg="#2c3e50")
        
        # 메인 타이틀
        title_label = tk.Label(root, text="🚀 Cryogenic Propellant BOG & Weighted Reusability Score Simulator", 
                               font=("맑은 고딕", 13, "bold"), fg="white", bg="#2c3e50", pady=10)
        title_label.pack(fill="x")
        
        main_container = tk.Frame(root, bg="#ecf0f1")
        main_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # [좌측 프레임] 조건 및 가중치 조절
        left_frame = tk.Frame(main_container, bg="white", padx=12, pady=12)
        left_frame.pack(side="left", fill="y", padx=5, pady=5)
        
        # 1. 미션 파라미터
        env_group = tk.LabelFrame(left_frame, text=" 1. 미션 파라미터 설정 ", font=("맑은 고딕", 10, "bold"), bg="white", padx=10, pady=8)
        env_group.pack(fill="x", pady=(0, 10))
        
        # 단열재 두께 라벨 + 회색 물음표 아이콘
        row1 = tk.Frame(env_group, bg="white")
        row1.pack(anchor="w", fill="x")
        tk.Label(row1, text="단열재 두께 (mm)", bg="white", font=("맑은 고딕", 9, "bold")).pack(side="left")
        help1 = tk.Label(row1, text="❓", fg="#95a5a6", bg="white", font=("맑은 고딕", 8), cursor="hand2")
        help1.pack(side="left", padx=(4, 0))
        HoverTooltip(help1, TOOLTIPS['thick'])

        self.thick_slider = tk.Scale(env_group, from_=10, to=200, orient="horizontal", bg="white", length=210, command=self.on_change)
        self.thick_slider.set(50)
        self.thick_slider.pack(pady=(0, 8))

        # 발사 대기 시간 라벨 + 회색 물음표 아이콘
        row2 = tk.Frame(env_group, bg="white")
        row2.pack(anchor="w", fill="x")
        tk.Label(row2, text="발사 대기 시간 (Hours)", bg="white", font=("맑은 고딕", 9, "bold")).pack(side="left")
        help2 = tk.Label(row2, text="❓", fg="#95a5a6", bg="white", font=("맑은 고딕", 8), cursor="hand2")
        help2.pack(side="left", padx=(4, 0))
        HoverTooltip(help2, TOOLTIPS['time'])

        self.time_slider = tk.Scale(env_group, from_=1, to=72, orient="horizontal", bg="white", length=210, command=self.on_change)
        self.time_slider.set(24)
        self.time_slider.pack()

        # 2. 평가 항목 가중치
        weight_group = tk.LabelFrame(left_frame, text=" 2. 평가지표 가중치 (Weight) ", font=("맑은 고딕", 10, "bold"), bg="white", padx=10, pady=8)
        weight_group.pack(fill="x")

        # BOG 가중치 라벨 + 회색 물음표 아이콘
        row3 = tk.Frame(weight_group, bg="white")
        row3.pack(anchor="w", fill="x")
        tk.Label(row3, text="BOG 손실률 가중치 (%)", bg="white", font=("맑은 고딕", 9, "bold")).pack(side="left")
        help3 = tk.Label(row3, text="❓", fg="#95a5a6", bg="white", font=("맑은 고딕", 8), cursor="hand2")
        help3.pack(side="left", padx=(4, 0))
        HoverTooltip(help3, TOOLTIPS['w_bog'])

        self.w_bog_slider = tk.Scale(weight_group, from_=0, to=100, orient="horizontal", bg="white", length=210, command=self.on_change)
        self.w_bog_slider.set(50)
        self.w_bog_slider.pack(pady=(0, 8))

        # 정비/운용 가중치 라벨 + 회색 물음표 아이콘
        row4 = tk.Frame(weight_group, bg="white")
        row4.pack(anchor="w", fill="x")
        tk.Label(row4, text="정비/운용성 가중치 (%)", bg="white", font=("맑은 고딕", 9, "bold")).pack(side="left")
        help4 = tk.Label(row4, text="❓", fg="#95a5a6", bg="white", font=("맑은 고딕", 8), cursor="hand2")
        help4.pack(side="left", padx=(4, 0))
        HoverTooltip(help4, TOOLTIPS['w_maint'])

        self.w_maint_slider = tk.Scale(weight_group, from_=0, to=100, orient="horizontal", bg="white", length=210, command=self.on_change)
        self.w_maint_slider.set(30)
        self.w_maint_slider.pack(pady=(0, 8))

        # 연료 밀도 가중치 라벨 + 회색 물음표 아이콘
        row5 = tk.Frame(weight_group, bg="white")
        row5.pack(anchor="w", fill="x")
        tk.Label(row5, text="연료 밀도 효율 가중치 (%)", bg="white", font=("맑은 고딕", 9, "bold")).pack(side="left")
        help5 = tk.Label(row5, text="❓", fg="#95a5a6", bg="white", font=("맑은 고딕", 8), cursor="hand2")
        help5.pack(side="left", padx=(4, 0))
        HoverTooltip(help5, TOOLTIPS['w_dens'])

        self.w_dens_slider = tk.Scale(weight_group, from_=0, to=100, orient="horizontal", bg="white", length=210, command=self.on_change)
        self.w_dens_slider.set(20)
        self.w_dens_slider.pack()

        self.w_total_lbl = tk.Label(weight_group, text="가중치 합계: 100%", fg="#2980b9", bg="white", font=("맑은 고딕", 9, "bold"))
        self.w_total_lbl.pack(pady=8)

        # [우측 프레임] 결과 표 & 그래프
        right_frame = tk.Frame(main_container, bg="white")
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        self.table_frame = tk.Frame(right_frame, bg="white")
        self.table_frame.pack(fill="x", padx=5, pady=5)
        
        self.graph_frame = tk.Frame(right_frame, bg="white")
        self.graph_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(7, 3.5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.update_simulation()

    def on_change(self, val):
        self.update_simulation()

    def update_simulation(self):
        thick_mm = float(self.thick_slider.get())
        hours = float(self.time_slider.get())
        
        w_bog = float(self.w_bog_slider.get())
        w_maint = float(self.w_maint_slider.get())
        w_dens = float(self.w_dens_slider.get())
        
        total_w = w_bog + w_maint + w_dens
        self.w_total_lbl.config(text=f"가중치 합계: {total_w:.0f}%")
        
        norm_w_bog = w_bog / total_w if total_w > 0 else 0.33
        norm_w_maint = w_maint / total_w if total_w > 0 else 0.33
        norm_w_dens = w_dens / total_w if total_w > 0 else 0.33
        
        area, k, temp_k = 100.0, 0.0001, 298.15
        thick_m = thick_mm / 1000.0
        
        data = []
        for name, p in propellants.items():
            heat = (k * area * (temp_k - p['boiling_point'])) / thick_m
            total_heat_kj = (heat * hours * 3600) / 1000.0
            initial_mass = 75.0 * p['density']
            bog_mass = total_heat_kj / p['latent_heat']
            loss_rate = min((bog_mass / initial_mass) * 100, 100.0)
            
            s_bog = max(0.0, 100.0 - loss_rate)
            s_maint = p['maint_score']
            s_dens = p['density_score']
            
            final_rs = (s_bog * norm_w_bog) + (s_maint * norm_w_maint) + (s_dens * norm_w_dens)
            status = "🟢 PASS" if loss_rate < 5.0 else "🔴 FAIL"
            
            data.append({
                'Fuel': name,
                'Loss Rate (%)': loss_rate,
                'BOG Score': s_bog,
                'Maint Score': s_maint,
                'Dens Score': s_dens,
                'RS Score': final_rs,
                'Status': status
            })
            
        df = pd.DataFrame(data)

        # 표 업데이트
        for widget in self.table_frame.winfo_children():
            widget.destroy()
            
        columns = ('추진제 (Propellant)', 'BOG 손실률', '손실방어 점수', '정비/운용 점수', '밀도효율 점수', '최종 RS 지수', '미션 판정')
        tree = ttk.Treeview(self.table_frame, columns=columns, show='headings', height=3)
        tree.pack(fill="x")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=110, anchor="center")
            
        for index, row in df.iterrows():
            tree.insert('', tk.END, values=(
                row['Fuel'], 
                f"{row['Loss Rate (%)']:.2f}%", 
                f"{row['BOG Score']:.1f} pt",
                f"{row['Maint Score']:.1f} pt",
                f"{row['Dens Score']:.1f} pt",
                f"{row['RS Score']:.1f} pt",
                row['Status']
            ))

        # 그래프 업데이트
        self.ax1.clear()
        self.ax2.clear()
        
        sns.barplot(x='Fuel', y='Loss Rate (%)', data=df, palette=['#1abc9c', '#e74c3c'], ax=self.ax1)
        self.ax1.set_title('BOG Loss Rate (%) [Lower is Better]', fontsize=10, fontweight='bold')
        self.ax1.axhline(5.0, color='red', linestyle='--', linewidth=1, label='Launch Limit (5%)')
        self.ax1.legend(loc='upper left', fontsize=8)
        
        sns.barplot(x='Fuel', y='RS Score', data=df, palette=['#1abc9c', '#e74c3c'], ax=self.ax2)
        self.ax2.set_title('Reusability Score (RS) [Higher is Better]', fontsize=10, fontweight='bold')
        self.ax2.set_ylim(0, 100)
        
        for p in self.ax2.patches:
            height = p.get_height()
            if height > 0:
                self.ax2.annotate(f"{height:.1f} pt", (p.get_x() + p.get_width() / 2., height),
                                  ha='center', va='bottom', fontsize=8, fontweight='bold')

        self.fig.tight_layout()
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = ProfessionalSimulatorApp(root)
    root.mainloop()