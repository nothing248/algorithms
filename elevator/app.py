import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random
import time
import numpy as np

# --- 页面配置 ---
st.set_page_config(
    page_title="外卖骑手算法进化史 - 交互演示 Demo", 
    layout="wide", 
    page_icon="🚴"
)

# ==========================================
# --- 自定义 CSS 样式（不使用 f-string 避免花括号冲突） ---
# ==========================================
CSS_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', 'Outfit', sans-serif;
    }
    
    .main-title {
        background: linear-gradient(135deg, #ff4e50, #f9d423);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 0.2rem;
        text-align: center;
    }
    
    .subtitle-text {
        color: #a0aec0;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    .section-title {
        font-weight: 700;
        font-size: 1.5rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
        border-left: 5px solid #ff4e50;
        padding-left: 10px;
    }

    .card-container {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        margin-bottom: 20px;
    }
    
    .rider-card {
        flex: 1 1 300px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .rider-card:hover {
        transform: translateY(-5px);
        border-color: rgba(255, 255, 255, 0.15);
        box-shadow: 0 8px 25px rgba(0,0,0,0.25);
    }
    
    .card-title {
        font-size: 1.25rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }
    
    .academic-tag {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-family: monospace;
        color: #e2e8f0;
    }
    
    .card-desc {
        font-size: 0.9rem;
        color: #cbd5e0;
        line-height: 1.5;
    }
    
    /* 侧边边框颜色定义 */
    .border-fcfs { border-left: 6px solid #3b82f6; }
    .border-sstf { border-left: 6px solid #fbbf24; }
    .border-scan { border-left: 6px solid #a78bfa; }
    .border-look { border-left: 6px solid #f97316; }
    .border-cscan { border-left: 6px solid #10b981; }
    
    /* 对比矩阵面板 */
    .metric-box {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #ff4e50;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #718096;
        margin-top: 5px;
    }
</style>
"""
st.markdown(CSS_STYLE, unsafe_allow_html=True)

# ==========================================
# --- Google Analytics 4 (GA4) 集成 ---
# ==========================================
try:
    from streamlit_gtag import st_gtag
    # 使用 streamlit-google-analytics-tag 第三方库进行 GA4 上报
    st_gtag(
        id="G-1P3NZM3830",
        event_name="page_view",
        params={
            "page_title": "外卖骑手算法进化史交互 Demo",
            "page_path": "/"
        }
    )
except ImportError:
    pass

# ==========================================
# --- 核心算法实现 (Segment Based Tracking) ---
# ==========================================

def alg_fcfs(start_pos, requests):
    """先来先服务 (FCFS) - 小明"""
    segments = []
    current = start_pos
    for req in requests:
        dist = abs(req - current)
        segments.append({
            "start": current,
            "end": req,
            "distance": dist,
            "type": "deliver",
            "dest_order": req
        })
        current = req
    return segments

def alg_sstf(start_pos, requests):
    """最短寻道时间优先 (SSTF) - 小刚"""
    segments = []
    current = start_pos
    remaining = requests.copy()
    
    while remaining:
        closest = min(remaining, key=lambda x: abs(x - current))
        dist = abs(closest - current)
        segments.append({
            "start": current,
            "end": closest,
            "distance": dist,
            "type": "deliver",
            "dest_order": closest
        })
        current = closest
        remaining.remove(closest)
        
    return segments

def alg_scan(start_pos, requests, direction="left", street_end=100):
    """电梯算法 (SCAN) - 撞墙老张"""
    segments = []
    if not requests:
        return segments
        
    left_reqs = sorted([r for r in requests if r < start_pos], reverse=True)
    right_reqs = sorted([r for r in requests if r >= start_pos])
    
    current = start_pos
    
    if direction == "left":
        # 1. 向左服务左侧订单
        for req in left_reqs:
            segments.append({
                "start": current, "end": req, "distance": abs(req - current),
                "type": "deliver", "dest_order": req
            })
            current = req
        
        # 2. 走到左边界 0 撞墙
        last_left = left_reqs[-1] if left_reqs else start_pos
        segments.append({
            "start": current, "end": 0, "distance": abs(0 - current),
            "type": "empty", "dest_order": None
        })
        current = 0
        
        # 3. 折返向右
        if right_reqs:
            # 拆分空载：0 -> last_left 是因为撞墙退回来的无效路程，last_left -> right_reqs[0] 是有效送单路程
            segments.append({
                "start": current, "end": last_left, "distance": abs(last_left - current),
                "type": "empty", "dest_order": None
            })
            current = last_left
            
            segments.append({
                "start": current, "end": right_reqs[0], "distance": abs(right_reqs[0] - current),
                "type": "deliver", "dest_order": right_reqs[0]
            })
            current = right_reqs[0]
            
            # 依次完成右侧剩余订单
            for req in right_reqs[1:]:
                segments.append({
                    "start": current, "end": req, "distance": abs(req - current),
                    "type": "deliver", "dest_order": req
                })
                current = req
    else:
        # 1. 向右服务右侧订单
        for req in right_reqs:
            segments.append({
                "start": current, "end": req, "distance": abs(req - current),
                "type": "deliver", "dest_order": req
            })
            current = req
            
        # 2. 走到右边界 street_end 撞墙
        last_right = right_reqs[-1] if right_reqs else start_pos
        segments.append({
            "start": current, "end": street_end, "distance": abs(street_end - current),
            "type": "empty", "dest_order": None
        })
        current = street_end
        
        # 3. 折返向左
        if left_reqs:
            # 拆分空载：street_end -> last_right 是撞墙空载，last_right -> left_reqs[0] 是有效送餐
            segments.append({
                "start": current, "end": last_right, "distance": abs(last_right - current),
                "type": "empty", "dest_order": None
            })
            current = last_right
            
            segments.append({
                "start": current, "end": left_reqs[0], "distance": abs(left_reqs[0] - current),
                "type": "deliver", "dest_order": left_reqs[0]
            })
            current = left_reqs[0]
            
            # 依次完成左侧剩余订单
            for req in left_reqs[1:]:
                segments.append({
                    "start": current, "end": req, "distance": abs(req - current),
                    "type": "deliver", "dest_order": req
                })
                current = req
                
    return segments

def alg_look(start_pos, requests, direction="left"):
    """看着办算法 (LOOK) - 智慧老张"""
    segments = []
    if not requests:
        return segments
        
    left_reqs = sorted([r for r in requests if r < start_pos], reverse=True)
    right_reqs = sorted([r for r in requests if r >= start_pos])
    
    current = start_pos
    
    if direction == "left":
        # 顺路把左边的送完，在最左侧订单处直接掉头，不去0号
        for req in left_reqs:
            segments.append({
                "start": current, "end": req, "distance": abs(req - current),
                "type": "deliver", "dest_order": req
            })
            current = req
        for req in right_reqs:
            segments.append({
                "start": current, "end": req, "distance": abs(req - current),
                "type": "deliver", "dest_order": req
            })
            current = req
    else:
        # 顺路把右边的送完，在最右侧订单处掉头，不去100号
        for req in right_reqs:
            segments.append({
                "start": current, "end": req, "distance": abs(req - current),
                "type": "deliver", "dest_order": req
            })
            current = req
        for req in left_reqs:
            segments.append({
                "start": current, "end": req, "distance": abs(req - current),
                "type": "deliver", "dest_order": req
            })
            current = req
            
    return segments

def alg_c_scan(start_pos, requests, street_end=100):
    """循环扫描 (C-SCAN) - 单行道撞墙老张"""
    segments = []
    if not requests:
        return segments
        
    right_reqs = sorted([r for r in requests if r >= start_pos])
    left_reqs = sorted([r for r in requests if r < start_pos])
    
    current = start_pos
    
    # 1. 向大数方向服务右侧订单
    for req in right_reqs:
        segments.append({
            "start": current, "end": req, "distance": abs(req - current),
            "type": "deliver", "dest_order": req
        })
        current = req
        
    # 2. 走到大数边界 100 撞墙
    last_right = right_reqs[-1] if right_reqs else start_pos
    segments.append({
        "start": current, "end": street_end, "distance": abs(street_end - current),
        "type": "empty", "dest_order": None
    })
    current = street_end
    
    # 3. 快速“闪现”到小数边界 0
    segments.append({
        "start": current, "end": 0, "distance": street_end, 
        "type": "reset", "dest_order": None
    })
    current = 0
    
    # 4. 从 0 跑到左侧第一个订单（空载）
    if left_reqs:
        segments.append({
            "start": current, "end": left_reqs[0], "distance": abs(left_reqs[0] - current),
            "type": "empty", "dest_order": left_reqs[0]
        })
        current = left_reqs[0]
        
        # 5. 服务剩下的左侧订单
        for req in left_reqs[1:]:
            segments.append({
                "start": current, "end": req, "distance": abs(req - current),
                "type": "deliver", "dest_order": req
            })
            current = req
            
    return segments

def alg_c_look(start_pos, requests):
    """循环看着办 (C-LOOK) - 单行道智慧老张"""
    segments = []
    if not requests:
        return segments
        
    right_reqs = sorted([r for r in requests if r >= start_pos])
    left_reqs = sorted([r for r in requests if r < start_pos])
    
    current = start_pos
    
    # 1. 向右服务右侧订单
    for req in right_reqs:
        segments.append({
            "start": current, "end": req, "distance": abs(req - current),
            "type": "deliver", "dest_order": req
        })
        current = req
        
    # 2. 从最右侧的订单（或起点）直接“闪现”到最左侧第一个订单
    if left_reqs:
        dest_left = left_reqs[0]
        segments.append({
            "start": current, "end": dest_left, "distance": abs(current - dest_left),
            "type": "reset", "dest_order": dest_left
        })
        current = dest_left
        
        # 3. 服务剩余的左侧订单
        for req in left_reqs[1:]:
            segments.append({
                "start": current, "end": req, "distance": abs(req - current),
                "type": "deliver", "dest_order": req
            })
            current = req
            
    return segments

# ==========================================
# --- 统一算法性能评估评估 ---
# ==========================================
def evaluate_algorithm(segments, requests):
    if not segments:
        return {
            "total_dist": 0, "deliver_dist": 0, "empty_dist": 0, "reset_dist": 0,
            "avg_wait": 0, "max_wait": 0, "std_wait": 0
        }
        
    total_dist = sum(s["distance"] for s in segments)
    deliver_dist = sum(s["distance"] for s in segments if s["type"] == "deliver")
    empty_dist = sum(s["distance"] for s in segments if s["type"] == "empty")
    reset_dist = sum(s["distance"] for s in segments if s["type"] == "reset")
    
    # 计算每个订单的等待时间（即到达该订单时骑手所行驶的累积路程）
    waiting_distances = {}
    cum_dist = 0
    for s in segments:
        cum_dist += s["distance"]
        dest = s.get("dest_order")
        if dest is not None and dest in requests and dest not in waiting_distances:
            waiting_distances[dest] = cum_dist
            
    for r in requests:
        if r not in waiting_distances:
            waiting_distances[r] = cum_dist
            
    wait_list = [waiting_distances[r] for r in requests]
    avg_wait = sum(wait_list) / len(wait_list) if wait_list else 0
    max_wait = max(wait_list) if wait_list else 0
    std_wait = np.std(wait_list) if wait_list else 0
    
    return {
        "total_dist": round(total_dist, 1),
        "deliver_dist": round(deliver_dist, 1),
        "empty_dist": round(empty_dist, 1),
        "reset_dist": round(reset_dist, 1),
        "avg_wait": round(avg_wait, 1),
        "max_wait": round(max_wait, 1),
        "std_wait": round(std_wait, 1)
    }

# ==========================================
# --- 动画仿真帧生成 ---
# ==========================================
def generate_animation_frames(start_pos, segments, requests):
    frames = []
    delivered = set()
    accum_dist = 0
    
    # 初始第 0 帧
    frames.append({
        "pos": start_pos,
        "delivered": set(),
        "log_msg": f"🚴 骑手在 {start_pos} 号位置待命，准备出发派送...",
        "accum_dist": 0,
        "direction": "idle",
        "plot_path": [start_pos]
    })
    
    plot_path = [start_pos]
    
    for seg in segments:
        start = seg["start"]
        end = seg["end"]
        dist = seg["distance"]
        seg_type = seg["type"]
        dest = seg["dest_order"]
        
        direction = "right" if end > start else "left" if end < start else "idle"
        
        if seg_type == "deliver":
            status_text = f"前往 {dest}号 商铺送餐..."
        elif seg_type == "empty":
            if end in (0, 100):
                status_text = f"空车前往边界墙 {end}号..."
            else:
                status_text = f"折返跑中，前往 {dest}号 途中..."
        elif seg_type == "reset":
            status_text = f"⚠️ 快速闪现复位到 {end}号 街头/商铺..."
            
        if seg_type == "reset":
            # 闪现：直接瞬移
            accum_dist += dist
            plot_path.append(end)
            if dest is not None and dest in requests:
                delivered.add(dest)
            frames.append({
                "pos": end,
                "delivered": delivered.copy(),
                "log_msg": f"⚡ 闪现完成！已快速复位到 {end}号位置。",
                "accum_dist": round(accum_dist, 1),
                "direction": "idle",
                "plot_path": plot_path.copy()
            })
        else:
            diff = end - start
            step_size = 4.0 # 动画每帧跨越的商铺数，值越小移动越平滑，但也越慢
            num_steps = max(1, int(abs(diff) / step_size))
            actual_step = diff / num_steps
            
            for i in range(1, num_steps + 1):
                curr_pos = start + actual_step * i
                if i == num_steps:
                    curr_pos = end # 最后一帧精确对齐
                    
                step_dist = abs(actual_step) if i < num_steps else abs(end - (start + actual_step * (i-1)))
                accum_dist += step_dist
                
                temp_plot_path = plot_path.copy()
                if curr_pos == end:
                    plot_path.append(end)
                    temp_plot_path = plot_path.copy()
                else:
                    temp_plot_path.append(curr_pos)
                    
                if curr_pos == end and dest is not None and dest in requests:
                    delivered.add(dest)
                    msg = f"🎉 成功送达 {dest}号 商铺！订单派送成功！"
                elif curr_pos == end and seg_type == "empty" and end in (0, 100):
                    msg = f"🧱 撞到 {end}号 边界墙！骑手准备优雅调头..."
                else:
                    msg = status_text
                    
                frames.append({
                    "pos": round(curr_pos, 1),
                    "delivered": delivered.copy(),
                    "log_msg": msg,
                    "accum_dist": round(accum_dist, 1),
                    "direction": direction,
                    "plot_path": temp_plot_path
                })
                
    return frames

# ==========================================
# --- 动态 HTML 街道渲染 ---
# ==========================================
def generate_street_html(current_pos, requests, delivered_requests, direction=None):
    bike_left = 5 + current_pos * 0.9
    
    markers = ""
    for req in requests:
        is_delivered = req in delivered_requests
        color = "#10b981" if is_delivered else "#ef4444"
        shadow = "0 0 10px #10b981" if is_delivered else "0 0 10px #ef4444"
        text_color = "#e2e8f0"
        left_pct = 5 + req * 0.9
        
        markers += f"""<div style="position: absolute; left: {left_pct}%; top: 38px; transform: translateX(-50%); display: flex; flex-direction: column; align-items: center;"><div style="width: 14px; height: 14px; border-radius: 50%; background-color: {color}; box-shadow: {shadow}; z-index: 10; border: 2px solid #111827;"></div><span style="font-size: 0.75rem; font-weight: 700; color: {text_color}; margin-top: 5px; font-family: 'Outfit';">{req}号</span></div>"""
        
    direction_arrow = "➡️" if direction == "right" else "⬅️" if direction == "left" else "⏸️"
    
    html_content = f"""<div style="background: linear-gradient(135deg, #1f2937, #111827); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 25px 20px; position: relative; height: 140px; margin-top: 10px; margin-bottom: 20px; overflow: hidden; box-shadow: inset 0 2px 10px rgba(0,0,0,0.6);"><span style="position: absolute; left: 1.2%; top: 40px; font-size: 0.75rem; color: #9ca3af; font-weight: 800; font-family: 'Outfit';">街头(0)</span><span style="position: absolute; right: 1.2%; top: 40px; font-size: 0.75rem; color: #9ca3af; font-weight: 800; font-family: 'Outfit';">街尾(100)</span><div style="position: absolute; top: 43px; left: 5%; right: 5%; height: 6px; background: linear-gradient(to right, #4b5563, #374151, #4b5563); border-radius: 3px; z-index: 1; border-top: 1px solid rgba(255,255,255,0.05);"></div>{markers}<div style="position: absolute; left: {bike_left}%; top: 12px; transform: translateX(-50%); transition: left 0.15s ease-out; z-index: 20; display: flex; flex-direction: column; align-items: center;"><div style="background-color: #3b82f6; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 800; margin-bottom: 2px; white-space: nowrap; box-shadow: 0 4px 6px rgba(0,0,0,0.3); font-family: 'Outfit'; border: 1px solid rgba(255,255,255,0.2);">骑手: {current_pos} {direction_arrow}</div><span style="font-size: 2.2rem; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.5)); line-height: 1; cursor: pointer;">🚴</span></div></div>"""
    return html_content

# ==========================================
# --- 页面标题与导语 ---
# ==========================================
st.markdown('<h1 class="main-title">🚴 外卖骑手算法进化史</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-text">—— 磁盘调度与物理电梯算法可交互科普演示平台</p>', unsafe_allow_html=True)

# ==========================================
# --- 侧边栏控制台 ---
# ==========================================
with st.sidebar:
    st.header("🎛️ 站长调度中心")
    st.markdown("---")
    
    st.subheader("1. 配置外卖街状态")
    
    input_mode = st.radio("订单输入模式", ("随机生成", "手动输入序列"), index=0)
    
    if input_mode == "随机生成":
        total_requests = st.slider("美食街订单数", min_value=3, max_value=20, value=8, step=1)
        st.caption("拖动滑块生成随机商铺订单。")
    else:
        custom_seq = st.text_input("输入商铺编号序列 (逗号隔开，范围0-100)", value="20, 85, 40, 10, 75, 95, 30, 65")
        st.caption("示例：`20, 85, 40, 10, 75, 95, 30, 65`")
        
    current_bike_pos = st.slider("骑手初始位置", min_value=0, max_value=100, value=50, step=1)
    
    # 随机生成按钮
    if st.button("🆕 刷新 / 生成新订单", type="secondary"):
        if input_mode == "随机生成":
            potential_requests = list(range(5, 96)) # 避开最极端边缘，留点撞墙空间
            if current_bike_pos in potential_requests:
                potential_requests.remove(current_bike_pos)
            st.session_state['requests'] = sorted(random.sample(potential_requests, total_requests))
        else:
            try:
                parsed = [int(x.strip()) for x in custom_seq.split(",") if x.strip().isdigit()]
                parsed = [x for x in parsed if 0 <= x <= 100]
                if not parsed:
                    parsed = [20, 85, 40, 10, 75, 95, 30, 65]
                st.session_state['requests'] = parsed
            except Exception:
                st.session_state['requests'] = [20, 85, 40, 10, 75, 95, 30, 65]
        st.session_state['anim_triggered'] = False

    # 默认值初始化
    if 'requests' not in st.session_state:
        st.session_state['requests'] = [20, 85, 40, 10, 75, 95, 30, 65]
        
    st.markdown("---")
    
    st.subheader("2. 设定骑手方向")
    start_direction = st.radio(
        "SCAN 与 LOOK 初始方向", 
        ("left", "right"), 
        index=0, 
        help="此方向仅对 SCAN (老司机老张) 和 LOOK (智慧老张) 起效"
    )
    
    st.markdown("---")
    st.subheader("3. 设定动画速度")
    anim_speed_delay = st.slider(
        "每帧刷新间隔 (秒)",
        min_value=0.02,
        max_value=0.50,
        value=0.08,
        step=0.02,
        help="数值越小，骑手移动越快；数值越大，移动越慢，适合仔细观察细节。"
    )
    
    st.markdown("---")
    st.markdown("📋 **当前美食街订单**：")
    st.code(str(st.session_state['requests']))
    st.markdown(f"📍 **骑手初始位置**：`{current_bike_pos}` 号店铺")

# ==========================================
# --- 主界面选项卡划分 ---
# ==========================================
tab_story, tab_arena, tab_anim = st.tabs([
    "📖 骑手进化故事", 
    "📊 算法擂台大比拼", 
    "🚴 实时派送动画模拟"
])

# ------------------------------------------
# --- Tab 1: 📖 骑手进化故事 ---
# ------------------------------------------
with tab_story:
    st.markdown('<div class="section-title">骑手档案与算法对照手册</div>', unsafe_allow_html=True)
    st.markdown("""
    在计算机底层的机械硬盘里，**磁头**为了在不同磁道间读取数据必须来回移动（**寻道**）。
    如果我们将硬盘磁道看作**“美食一条街”**，把磁头看作**“外卖骑手”**，而数据读取请求就是**“外卖订单”**。
    跟随下面 5 位骑手的进化史，你将轻松秒懂 5 种最经典的磁盘调度与电梯调度算法！
    """)
    
    # 彻底解决 Markdown 渲染在有空行/缩进时把 HTML 误解析为代码块的 Bug，使所有 HTML 行完全顶格且去掉内部换行空行
    story_html = """<div class="card-container"><div class="rider-card border-fcfs"><div class="card-title"><span>小明 🚴</span><span class="academic-tag">FCFS / 先来先服务</span></div><div class="card-desc"><strong>座右铭：</strong> 谁先下单，我就先送谁家！绝不插队！<br><strong>骑手现状：</strong> 微信步数轻松突破五万步，累得直吐舌头，结果外卖还经常迟到，差评满天飞。<br><strong>算法硬核：</strong> 绝对公平，但极其低效。若订单交替出现于街道两端，磁头会疯狂进行无意义的折返，严重浪费寻道时间。</div></div><div class="rider-card border-sstf"><div class="card-title"><span>小刚 🛵</span><span class="academic-tag">SSTF / 最短寻道时间优先</span></div><div class="card-desc"><strong>座右铭：</strong> 谁离我最近，我就先去谁家！节省体力第一！<br><strong>骑手现状：</strong> 送单确实极快。但街尾 80号 顾客从中午等到天黑，眼睁睁看着小刚在 40-50号 之间反复转悠，就是不往远处挪一步。<br><strong>算法硬核：</strong> 追求局部最短距离。会带来致命的<strong>“饥饿现象（Starvation）”</strong>。只要中心区域不断产生新请求，边缘请求就会被无限期拖延。</div></div><div class="rider-card border-scan"><div class="card-title"><span>老张 (初级版) 🛗</span><span class="academic-tag">SCAN / 扫描算法（电梯算法）</span></div><div class="card-desc"><strong>座右铭：</strong> 一条道走到黑，撞到最尽头的墙壁才准调头！<br><strong>骑手现状：</strong> 规矩铁律，顺路就接。虽然偶尔有微小延迟，但归根结底绝不会让任何一个顾客永远收不到外卖，全局公平有序。<br><strong>算法硬核：</strong> 完美的物理电梯模拟。在当前方向上扫描至最边缘，解决饥饿问题，平衡了公平与效率。但会存在空跑到 0 或 100 边界的<strong>无效跑路</strong>。</div></div><div class="rider-card border-look"><div class="card-title"><span>老张 (智慧版) 👁️</span><span class="academic-tag">LOOK / 看着办算法</span></div><div class="card-desc"><strong>座右铭：</strong> 顺路送，但抬头看路，前面没有单我就就地折返！<br><strong>骑手现状：</strong> 在老张的基础上学会了摸鱼与智能判断，不再傻乎乎去撞街道边缘的墙壁，体能消耗大幅减少。<br><strong>算法硬核：</strong> 磁盘调度的经典改进。若当前行进方向的前方已无等待读写的磁道请求，磁头立即改变运行方向，避开无效的边缘空扫。</div></div><div class="rider-card border-cscan"><div class="card-title"><span>老张 (循环版) 🔄</span><span class="academic-tag">C-SCAN & C-LOOK / 循环扫描</span></div><div class="card-desc"><strong>座右铭：</strong> 只在从左往右时送货！到头后直接闭眼‘闪现’跑回起点！<br><strong>骑手现状：</strong> 街道被改成单行道。虽然多跑了回程闪现的路，但所有顾客发现，无论在何处下单，外卖**平均等待时间**都是一模一样的！<br><strong>算法硬核：</strong> 循环扫描。忽略回扫耗时（回扫通常极快），它使磁盘任意扇区请求的等待时间方差降到最低，提供了<strong>极致、稳定的公平性</strong>。</div></div></div>"""
    st.markdown(story_html, unsafe_allow_html=True)
    
    st.info("💡 请切换到 **“算法擂台大比拼”** 查看当前配置下各骑手的实测成绩，或在 **“实时派送动画模拟”** 里观看他们的动态跑单动画！")

# ------------------------------------------
# --- Tab 2: 📊 算法擂台大比拼 ---
# ------------------------------------------
with tab_arena:
    st.markdown('<div class="section-title">算法擂台：同台数据大竞技</div>', unsafe_allow_html=True)
    
    requests = st.session_state['requests']
    
    # 并发计算 6 种情况下的派送轨迹与指标
    fcfs_seg = alg_fcfs(current_bike_pos, requests)
    sstf_seg = alg_sstf(current_bike_pos, requests)
    scan_seg = alg_scan(current_bike_pos, requests, direction=start_direction)
    look_seg = alg_look(current_bike_pos, requests, direction=start_direction)
    cscan_seg = alg_c_scan(current_bike_pos, requests)
    clook_seg = alg_c_look(current_bike_pos, requests)
    
    fcfs_res = evaluate_algorithm(fcfs_seg, requests)
    sstf_res = evaluate_algorithm(sstf_seg, requests)
    scan_res = evaluate_algorithm(scan_seg, requests)
    look_res = evaluate_algorithm(look_seg, requests)
    cscan_res = evaluate_algorithm(cscan_seg, requests)
    clook_res = evaluate_algorithm(clook_seg, requests)
    
    # 汇总为 DataFrame
    compare_data = {
        "算法与骑手": [
            "FCFS (直肠子小明)", 
            "SSTF (近路狂魔小刚)", 
            "SCAN (撞墙老张)", 
            "LOOK (智慧老张)", 
            "C-SCAN (循环撞墙老张)", 
            "C-LOOK (循环智慧老张)"
        ],
        "总行驶距离 🚲": [
            fcfs_res["total_dist"], 
            sstf_res["total_dist"], 
            scan_res["total_dist"], 
            look_res["total_dist"], 
            cscan_res["total_dist"], 
            clook_res["total_dist"]
        ],
        "送单行驶距离 📦": [
            fcfs_res["deliver_dist"], 
            sstf_res["deliver_dist"], 
            scan_res["deliver_dist"], 
            look_res["deliver_dist"], 
            cscan_res["deliver_dist"], 
            clook_res["deliver_dist"]
        ],
        "边界空跑距离 🧱": [
            fcfs_res["empty_dist"], 
            sstf_res["empty_dist"], 
            scan_res["empty_dist"], 
            look_res["empty_dist"], 
            cscan_res["empty_dist"], 
            clook_res["empty_dist"]
        ],
        "闪现空回距离 ⚡": [
            fcfs_res["reset_dist"], 
            sstf_res["reset_dist"], 
            scan_res["reset_dist"], 
            look_res["reset_dist"], 
            cscan_res["reset_dist"], 
            clook_res["reset_dist"]
        ],
        "订单平均等待时间 ⏳": [
            fcfs_res["avg_wait"], 
            sstf_res["avg_wait"], 
            scan_res["avg_wait"], 
            look_res["avg_wait"], 
            cscan_res["avg_wait"], 
            clook_res["avg_wait"]
        ],
        "最长订单等待时间 😡": [
            fcfs_res["max_wait"], 
            sstf_res["max_wait"], 
            scan_res["max_wait"], 
            look_res["max_wait"], 
            cscan_res["max_wait"], 
            clook_res["max_wait"]
        ],
        "等待时间波动差 ⚖️": [
            fcfs_res["std_wait"], 
            sstf_res["std_wait"], 
            scan_res["std_wait"], 
            look_res["std_wait"], 
            cscan_res["std_wait"], 
            clook_res["std_wait"]
        ],
        "边缘饥饿风险": [
            "无", 
            "⚠️ 高风险", 
            "无", 
            "无", 
            "无", 
            "无"
        ]
    }
    
    df_compare = pd.DataFrame(compare_data)
    
    # 美化显示表格，使用高亮突出表现最好的
    def highlight_min(s):
        is_min = s == s.min()
        return ['background-color: rgba(16, 185, 129, 0.25); color: #10b981; font-weight: bold' if v else '' for v in is_min]
        
    def highlight_max(s):
        is_max = s == s.max()
        return ['background-color: rgba(239, 68, 68, 0.2); color: #ef4444' if v else '' for v in is_max]
        
    styled_df = df_compare.style\
        .apply(highlight_min, subset=["总行驶距离 🚲", "订单平均等待时间 ⏳", "等待时间波动差 ⚖️"])\
        .apply(highlight_max, subset=["最长订单等待时间 😡"])
        
    st.subheader("📊 综合性能比拼矩阵")
    st.dataframe(styled_df, width='stretch', hide_index=True)
    st.caption("注：绿底代表当前列最优算法，红底代表最长等待时间（体现倒霉客户的等待极限）。")
    
    # 绘图区域：两个图表
    st.subheader("📈 数据可视化直观对比")
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # 图表1：总移动距离与平均等待距离
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=df_compare["算法与骑手"],
            y=df_compare["总行驶距离 🚲"],
            name="总行驶距离 (路程总开销)",
            marker_color="#3b82f6"
        ))
        fig1.add_trace(go.Bar(
            x=df_compare["算法与骑手"],
            y=df_compare["订单平均等待时间 ⏳"],
            name="订单平均等待时间 (响应性)",
            marker_color="#10b981"
        ))
        fig1.update_layout(
            title="总行驶路程 vs 订单平均等待时间 (越低越高效)",
            barmode="group",
            xaxis_tickangle=-15,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=60, b=40),
            height=400
        )
        st.plotly_chart(fig1, width='stretch')
        
    with col_chart2:
        # 图表2：最长等待时间与离散度
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=df_compare["算法与骑手"],
            y=df_compare["最长订单等待时间 😡"],
            name="最长等待时间 (最倒霉客户)",
            marker_color="#f59e0b"
        ))
        fig2.add_trace(go.Scatter(
            x=df_compare["算法与骑手"],
            y=df_compare["等待时间波动差 ⚖️"],
            name="等待时间波动方差 (波动越小越公平)",
            marker=dict(color="#ec4899", size=8),
            line=dict(color="#ec4899", width=3)
        ))
        fig2.update_layout(
            title="最长等待时间 vs 等待时间波动性 (离散度)",
            xaxis_tickangle=-15,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=60, b=40),
            height=400
        )
        st.plotly_chart(fig2, width='stretch')
        
    # 科普深度解读
    with st.expander("🧐 站长深度报告：算法背后的博弈（效率与公平）"):
        st.markdown("""
        通过上面的擂台比拼，我们可以清晰地读懂这 6 种经典磁盘调度算法背后的工程哲学：
        
        1. **小刚 (SSTF) 的“小聪明”与代价**：
           - 在多数随机订单分布下，**SSTF** 的“总行驶距离”都处于极低水平。这就像只送身边的外卖确实省油。
           - 但它的致命盲区在 **最长等待时间** 和 **波动方差**。由于小刚只图近，如果中间不断有人下单，边缘的订单会被活活“饿死”（即饥饿现象）。因此，**它的波动差通常最大，公平性最差**。
           
        2. **老张 (SCAN vs LOOK) 的“撞墙与回头”**：
           - **SCAN (电梯算法)** 强制撞两端边界（0和100），这为所有人提供了服务保障，绝不会有饥饿。但你可以看到，它产生了明显的**边界空跑距离**。
           - **LOOK** 是老张的智慧升级版。由于“抬头看路”，如果前方没单就会立即调头。这让它的**总行驶距离明显小于 SCAN**，而平均等待时间和最大等待时间却几乎保持一致！在工程上，这是一次巨大的优化。
           
        3. **单行道老张 (C-SCAN vs C-LOOK) 的“极致公平”**：
           - 很多人不解：C-SCAN 到头后还要跑 100 距离的“空回闪现”，这不是浪费吗？
           - 看一下**“等待时间波动差（⚖️）”**指标。**C-SCAN/C-LOOK** 的波动差在很多情况下是最平稳的！
           - 在高并发的硬盘请求中，如果只像电梯那样来回扫，刚刚被掠过的磁道想要被再次读取，必须等待磁头“开到头、调头、走回来”，耗时翻倍；而边缘磁道的等待时间也是中间磁道的两倍。
           - **C-SCAN/C-LOOK 规定只单向配送，让磁头对整条街任意商铺的平均等待时间变得完全均等。** 用一次快速的回扫，换取了系统的**极度稳定与可预测性**，这是系统架构设计中对于“绝对公平”的终极追求。
        """)

# ------------------------------------------
# --- Tab 3: 🚴 实时派送动画模拟 ---
# ------------------------------------------
with tab_anim:
    st.markdown('<div class="section-title">派送模拟器：骑手实时送餐演示</div>', unsafe_allow_html=True)
    st.markdown("选择算法，点击开始，你可以亲眼看到骑手 🚴 是如何在这条美食街上奔波的！")
    
    col_ctrl, col_stats = st.columns([1, 2])
    
    with col_ctrl:
        selected_alg = st.selectbox(
            "当前模拟的算法",
            [
                "1. FCFS (先来先服务小明)", 
                "2. SSTF (最短寻道时间小刚)", 
                "3. SCAN (撞墙老司机老张)", 
                "4. LOOK (智慧老司机老张)", 
                "5. C-SCAN (循环撞墙老张)", 
                "6. C-LOOK (循环智慧老张)"
            ],
            index=3 # 默认 LOOK
        )
        
        # 准备对应的算法数据
        requests = st.session_state['requests']
        
        if "1. FCFS" in selected_alg:
            chosen_seg = alg_fcfs(current_bike_pos, requests)
        elif "2. SSTF" in selected_alg:
            chosen_seg = alg_sstf(current_bike_pos, requests)
        elif "3. SCAN" in selected_alg:
            chosen_seg = alg_scan(current_bike_pos, requests, direction=start_direction)
        elif "4. LOOK" in selected_alg:
            chosen_seg = alg_look(current_bike_pos, requests, direction=start_direction)
        elif "5. C-SCAN" in selected_alg:
            chosen_seg = alg_c_scan(current_bike_pos, requests)
        else:
            chosen_seg = alg_c_look(current_bike_pos, requests)
            
        anim_frames = generate_animation_frames(current_bike_pos, chosen_seg, requests)
        total_frames = len(anim_frames)
        
        st.markdown(f"🎬 该算法派送路线共包含 `{len(chosen_seg)}` 个阶段，拆分为 `{total_frames}` 个动画关键帧。")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            run_simulation = st.button("🚀 开始动画模拟", key="start_anim_btn", type="primary")
        with col_btn2:
            stop_simulation = st.button("⏹️ 重置", key="stop_anim_btn")
            
        if stop_simulation:
            st.session_state['anim_triggered'] = False
            
    with col_stats:
        stats_placeholder = st.empty()
        
        eval_res = evaluate_algorithm(chosen_seg, requests)
        stats_placeholder.markdown(f"""<div style="display: flex; gap: 15px; margin-top: 10px;"><div class="metric-box" style="flex: 1;"><div class="metric-value">{eval_res['total_dist']}</div><div class="metric-label">预计总行驶里程</div></div><div class="metric-box" style="flex: 1;"><div class="metric-value">{eval_res['avg_wait']}</div><div class="metric-label">订单平均等待</div></div><div class="metric-box" style="flex: 1;"><div class="metric-value">{eval_res['max_wait']}</div><div class="metric-label">最长客户等待</div></div></div>""", unsafe_allow_html=True)
        
    street_placeholder = st.empty()
    progress_col, log_col = st.columns([1, 2])
    with progress_col:
        progress_placeholder = st.empty()
    with log_col:
        log_placeholder = st.empty()
        
    chart_placeholder = st.empty()
    
    street_placeholder.markdown(
        generate_street_html(current_bike_pos, requests, set()), 
        unsafe_allow_html=True
    )
    
    full_path_positions = [current_bike_pos] + [s["end"] for s in chosen_seg]
    fig_static = go.Figure()
    
    fig_static.add_shape(type="rect", x0=0, y0=0, x1=len(full_path_positions)-1, y1=100, fillcolor="rgba(240,240,240,0.02)", line_width=0)
    fig_static.add_trace(go.Scatter(
        x=list(range(len(full_path_positions))),
        y=full_path_positions,
        mode='lines+markers',
        line=dict(color='#ff4e50', width=3),
        marker=dict(size=8, color='#f9d423', line=dict(width=1, color='#111827')),
        name="完整规划路径",
        hovertemplate='步骤 %{x}: %{y}号商铺'
    ))
    
    for idx in range(1, len(full_path_positions)):
        p_start = full_path_positions[idx-1]
        p_end = full_path_positions[idx]
        is_reset_segment = False
        for s in chosen_seg:
            if s["start"] == p_start and s["end"] == p_end and s["type"] == "reset":
                is_reset_segment = True
                break
        if is_reset_segment:
            fig_static.add_trace(go.Scatter(
                x=[idx-1, idx], y=[p_start, p_end],
                mode='lines',
                line=dict(color='rgba(239, 68, 68, 0.6)', width=2.5, dash='dash'),
                showlegend=False,
                hoverinfo='none'
            ))
            
    fig_static.update_layout(
        title=f"🚴 骑手完整派送路径规划图 (由左至右)",
        xaxis_title="派送步骤 / 折返点",
        yaxis_title="商铺编号 (0-100)",
        yaxis=dict(range=[-5, 105], gridcolor='rgba(255,255,255,0.05)', tickmode='linear', tick0=0, dtick=10),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=50, b=40),
        height=320,
        showlegend=False
    )
    chart_placeholder.plotly_chart(fig_static, width='stretch')
    
    if run_simulation:
        st.session_state['anim_triggered'] = True
        
        for idx, frame in enumerate(anim_frames):
            if not st.session_state.get('anim_triggered', False):
                break
                
            curr_pos = frame["pos"]
            delivered_set = frame["delivered"]
            log_msg = frame["log_msg"]
            accum_dist = frame["accum_dist"]
            direction = frame["direction"]
            plot_path_curr = frame["plot_path"]
            
            street_placeholder.markdown(
                generate_street_html(curr_pos, requests, delivered_set, direction=direction),
                unsafe_allow_html=True
            )
            
            stats_placeholder.markdown(f"""<div style="display: flex; gap: 15px; margin-top: 10px;"><div class="metric-box" style="flex: 1; border-color: rgba(59, 130, 246, 0.3);"><div class="metric-value" style="color: #3b82f6;">{accum_dist} 号</div><div class="metric-label">当前累积行驶</div></div><div class="metric-box" style="flex: 1; border-color: rgba(16, 185, 129, 0.3);"><div class="metric-value" style="color: #10b981;">{len(delivered_set)} / {len(requests)}</div><div class="metric-label">已送达订单数</div></div><div class="metric-box" style="flex: 1; border-color: rgba(245, 158, 11, 0.3);"><div class="metric-value" style="color: #f59e0b;">{round(curr_pos, 1)}</div><div class="metric-label">骑手当前坐标</div></div></div>""", unsafe_allow_html=True)
            
            progress_pct = (idx + 1) / total_frames
            progress_placeholder.progress(progress_pct)
            log_placeholder.markdown(f"📢 **最新广播**：`{log_msg}`")
            
            if idx % 3 == 0 or idx == total_frames - 1:
                fig_dynamic = go.Figure()
                fig_dynamic.add_shape(type="rect", x0=0, y0=0, x1=len(full_path_positions)-1, y1=100, fillcolor="rgba(240,240,240,0.02)", line_width=0)
                
                fig_dynamic.add_trace(go.Scatter(
                    x=list(range(len(plot_path_curr))),
                    y=plot_path_curr,
                    mode='lines+markers',
                    line=dict(color='#ff4e50', width=3),
                    marker=dict(size=8, color='#f9d423', line=dict(width=1, color='#111827')),
                    showlegend=False
                ))
                
                fig_dynamic.add_trace(go.Scatter(
                    x=[len(plot_path_curr) - 1],
                    y=[curr_pos],
                    mode='markers',
                    marker=dict(size=14, color='#3b82f6', symbol='hexagram', line=dict(width=2, color='#ffffff')),
                    showlegend=False
                ))
                
                fig_dynamic.update_layout(
                    title=f"🚴 骑手实时派送轨迹图 (已送达 {len(delivered_set)}/{len(requests)} 处)",
                    xaxis_title="派送步骤 / 折返点",
                    yaxis_title="商铺编号 (0-100)",
                    yaxis=dict(range=[-5, 105], gridcolor='rgba(255,255,255,0.05)', tickmode='linear', tick0=0, dtick=10),
                    xaxis=dict(range=[-0.5, len(full_path_positions)-0.5], gridcolor='rgba(255,255,255,0.05)'),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=40, r=40, t=50, b=40),
                    height=320
                )
                chart_placeholder.plotly_chart(fig_dynamic, width='stretch')
                
            time.sleep(anim_speed_delay)
            
        st.success("🏁 派送任务圆满完成！")
        st.session_state['anim_triggered'] = False