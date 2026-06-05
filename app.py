import tkinter as tk
from tkinter import ttk
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns

# 스타일 설정
sns.set_theme(style="whitegrid")

# 1. 시뮬레이션 핵심 연산 함수
propellants = {
    'Liquid Methane (CH4)': {'boiling_point': 111.6, 'latent_heat': 510.0, 'density': 422.6, 'reusability': 8.5},
    'Liquid Hydrogen (LH2)': {'boiling_point': 20.28, 'latent_heat': 446.0, 'density': 70.8, 'reusability': 4.0}
}

def calculate_data(thickness_mm, hours):
    area = 100.0  # 탱크 표면적 (m2)
    k = 0.0001    # 단열재 성능
    thick_m = thickness_mm / 1000.0
    
    results = []
    for name, p in propellants.items():
        heat = (k * area * (300.0 - p['boiling_point'])) / thick_m
        total_heat_kj = (heat * hours * 3600) / 1000.0
        initial_mass = 75.0 * p['density']
        bog_mass = total_heat_kj / p['latent_heat']
        loss_rate = min((bog_mass / initial_mass) * 100, 100.0)
        rs_score = p['reusability'] * 5 + (100 - loss_rate) * 0.5
        
        results.append({
            'Fuel': name,
            'Initial Mass (kg)': f"{initial_mass:,.1f}",
            'BOG Loss (kg)': f"{bog_mass:,.1f}",
            'Loss Rate (%)': f"{loss_rate:.2f}%",
            'Reusability Score': f"{rs_score:.1f} pt"
        })
    return results

# 2. 메인 GUI 앱 클래스 설정
class SimulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("극저온 추진제 BOG 및 재사용성(RS) 시뮬레이터")
        self.root.geometry("1100x700")
        self.root.configure(bg="#f5f6fa")
        
        # 상단 제목 프레임
        title_frame = tk.Frame(root, bg="#2c3e50", height=60)
        title_frame.pack(fill="x")
        title_label = tk.Label(title_frame, text="Cryogenic Propellant Simulator for Reusable Rockets", 
                               font=("Arial", 16, "bold"), fg="white", bg="#2c3e50")
        title_label.pack(pady=15)
        
        # 입력 레이아웃 프레임
        input_frame = tk.LabelFrame(root, text=" 미션 프로파일 변수 설정 (Mission Profile Elements) ", font=("Arial", 11, "bold"), bg="white", padx=20, pady=15)
        input_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(input_frame, text="단열재 두께 (Insulation Thickness, mm):", bg="white", font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.thick_entry = tk.Entry(input_frame, font=("Arial", 10), width=10)
        self.thick_entry.insert(0, "50.0")
        self.thick_entry.grid(row=0, column=1, padx=10, pady=5)
        
        tk.Label(input_frame, text="운용/대기 시간 (Mission Duration, Hours):", bg="white", font=("Arial", 10)).grid(row=0, column=2, sticky="w", pady=5)
        self.time_entry = tk.Entry(input_frame, font=("Arial", 10), width=10)
        self.time_entry.insert(0, "24.0")
        self.time_entry.grid(row=0, column=3, padx=10, pady=5)
        
        # 실행 버튼
        run_btn = tk.Button(input_frame, text="시뮬레이션 실행 (Run)", command=self.update_simulation, 
                            bg="#3498db", fg="white", font=("Arial", 10, "bold"), padx=15, pady=3)
        run_btn.grid(row=0, column=4, padx=30)
        
        # 하단 결과 배치 (왼쪽: 표 / 오른쪽: 그래프)
        content_frame = tk.Frame(root, bg="#f5f6fa")
        content_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        # 왼쪽 표 프레임
        self.table_frame = tk.LabelFrame(content_frame, text=" 수치 데이터 (Simulation Matrix) ", font=("Arial", 11, "bold"), bg="white", padx=10, pady=10)
        self.table_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # 오른쪽 그래프 프레임
        self.graph_frame = tk.LabelFrame(content_frame, text=" 시각화 데이터 분석 (Graphical Analysis) ", font=("Arial", 11, "bold"), bg="white", padx=10, pady=10)
        self.graph_frame.pack(side="right", fill="both", expand=True)
        
        # 최초 1회 실행
        self.update_simulation()

    def update_simulation(self):
        # 1. 입력값 읽기
        try:
            thick = float(self.thick_entry.get())
            hours = float(self.time_entry.get())
        except ValueError:
            return # 잘못된 입력 시 반응 없음
            
        data = calculate_data(thick, hours)
        
        # 2. 표 업데이트
        for widget in self.table_frame.winfo_children():
            widget.destroy()
            
        columns = ('Fuel', 'Initial Mass', 'BOG Loss', 'Loss Rate', 'RS Score')
        tree = ttk.Treeview(self.table_frame, columns=columns, show='headings', height=4)
        tree.pack(fill="both", expand=True)
        
        # 표 헤더 설정
        tree.heading('Fuel', text='추진제 (Fuel)')
        tree.heading('Initial Mass', text='초기 질량 (kg)')
        tree.heading('BOG Loss', text='증발 손실 (kg)')
        tree.heading('Loss Rate', text='손실률 (%)')
        tree.heading('RS Score', text='재사용 지수 (RS)')
        
        tree.column('Fuel', width=130, anchor="center")
        tree.column('Initial Mass', width=100, anchor="center")
        tree.column('BOG Loss', width=100, anchor="center")
        tree.column('Loss Rate', width=90, anchor="center")
        tree.column('RS Score', width=110, anchor="center")
        
        for row in data:
            tree.insert('', tk.END, values=(row['Fuel'], row['Initial Mass (kg)'], row['BOG Loss (kg)'], row['Loss Rate (%)'], row['Reusability Score']))
            
        # 3. 그래프 업데이트
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
            
        df = pd.DataFrame(data)
        # 문자열 포맷팅 해제 후 숫자로 변환 (그래프용)
        df['Loss Rate (%)'] = df['Loss Rate (%)'].str.replace('%', '').astype(float)
        df['Reusability Score'] = df['Reusability Score'].str.replace(' pt', '').astype(float)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 3.5))
        fig.patch.set_facecolor('white')
        
        sns.barplot(x='Fuel', y='Loss Rate (%)', data=df, palette=['#16a085', '#c0392b'], ax=ax1)
        ax1.set_title('BOG Loss Rate (%)', fontsize=9, fontweight='bold')
        ax1.set_ylabel('')
        ax1.set_xlabel('')
        
        sns.barplot(x='Fuel', y='Reusability Score', data=df, palette=['#16a085', '#c0392b'], ax=ax2)
        ax2.set_title('Reusability Score (RS)', fontsize=9, fontweight='bold')
        ax2.set_ylabel('')
        ax2.set_xlabel('')
        ax2.set_ylim(0, 100)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = SimulatorApp(root)
    root.mainloop()