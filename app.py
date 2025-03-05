import streamlit as st
from function import(match_dict,matches,
                     create_timestring,
                     get_event_dict,
                     create_plot,
                     shot_freeze_frame,country_colors)
from visual import (get_starting_xi,
                    plot_team_formation,
                    heat_map,
                    plot_pass_network,
                    pass_flow,
                    joint_shot_plot)
from streamlit_extras.badges import badge
from mplsoccer import Pitch, FontManager, Sbopen
from statsbombpy import sb
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
import plotly.express as px
plt.rcParams['font.family'] = 'Meiryo'

team_country_map = {
        "France": "フランス",
        "England": "イングランド",
        "Portugal": "ポルトガル",
        "Germany": "ドイツ",
        "Spain": "スペイン",
        "Italy": "イタリア",
        "Netherlands": "オランダ",
        "Belgium": "ベルギー",
        "Croatia": "クロアチア",
        "Switzerland": "スイス",
        "Poland": "ポーランド",
        "Denmark": "デンマーク",
        "Slovakia": "スロバキア",
        "Slovenia": "スロベニア",
        "Serbia": "セルビア",
        "Hungary": "ハンガリー",
        "Scotland": "スコットランド",
        "Austria": "オーストリア",
        "Czech Republic": "チェコ",
        "Turkey": "トルコ",
        "Ukraine": "ウクライナ",
        "Romania": "ルーマニア",
        "Georgia": "ジョージア",
        "Albania": "アルバニア",
    }

st.header("サッカーデータサイエンス可視化アプリ")

# 
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 ホーム", "🏆大会データ" , "📊 可視化比較",
                                        "🔍 タイムスタンプ分析", "🎮ゲームの応用(展望)"])
with tab1:
    st.title("🏠")
    st.markdown("""
    このアプリは、StatsBombの2024年ヨーロッパカップ（EURO 2024）のデータを基に、試合分析や可視化を行うことができるWebアプリです。  
    試合の統計情報、チームのパフォーマンス、戦術分析など、さまざまな視点からデータを探索できます。

    ### 🔹 主な機能
    - 🏆 **大会データ**：EURO2024の主要統計を確認できます。
    - 📊 **可視化比較**：チームのパフォーマンスを視覚的に比較できます。
    - 🔍 **タイムスタンプ分析**：試合中の特定の時間帯のフォームを発見できます。
    - 📖 **ゲームの応用(展望)**: Football Managerというゲームと連携

    ### 📌 データソース
    このアプリのデータは**StatsBombの公開データセット**を使用しています。  
    データは定期的に更新され、最新の試合結果を反映しています。

    ### 💡 使い方
    タブを選択し、分析したい試合やチームを選んでください。  
    データはインタラクティブなグラフや表で表示されます。
    """)
    st.markdown("""---""")
    st.markdown(
    "*TTCデータサイエンス+AI科卒業研究_リヤドアハマド*"
    )

with tab2:  # 大会まとめ
    # 2024年ヨーロッパ選手権 (EURO 2024) のデータ取得
    matches = sb.matches(competition_id=55, season_id=282)
    st.title("🏆2024Euro 大会統計")
    st.markdown("本大会の主要なデータを表示")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        total_matches = matches.shape[0]
        st.metric(label="試合数", value=f"{total_matches} 試合")
    with col2:
        total_goals = matches['home_score'].sum() + matches['away_score'].sum()
        st.metric(label="総得点", value=f"{total_goals} ゴール")
    with col3:
        avg_goals = round(total_goals / total_matches, 2)
        st.metric(label="1試合平均ゴール", value=f"{avg_goals} ゴール")
    
    
    parser = Sbopen()
    @st.cache_data
    def load_data():
        matches = sb.matches(competition_id=55, season_id=282)
        event_list = []
        for match_id in matches['match_id']:
            events, related, freeze, players = parser.event(match_id)
            event_list.append(events)
        events = pd.concat(event_list, ignore_index=True)
        return matches, events
    matches, events = load_data()
    
    st.header("⚽ 各チームの攻撃データ")
    team_shots = events[events['type_name'] == 'Shot'].groupby('team_name').size()
    team_goals = events[(events['type_name'] == 'Shot') & (events['outcome_name'] == 'Goal')].groupby('team_name').size()
    team_stats = pd.DataFrame({'シュート数': team_shots, 'ゴール数': team_goals}).fillna(0)
    team_stats['得点率'] = (team_stats['ゴール数'] / team_stats['シュート数']).fillna(0)  # 计算进攻效率
    # --- 🎯 选择球队 ---
    selected_team = st.selectbox("🔍 チームを選択してください", ["全体"] + list(team_stats.index))
    # 过滤数据（如果选择了特定球队）
    if selected_team != "全体":
        team_stats = team_stats.loc[[selected_team]]
    # --- 📊 使用 Plotly 绘制交互式图表 ---
    fig = px.bar(
        team_stats.reset_index(),
        x="team_name",
        y=["シュート数", "ゴール数"],
        title="シュート数 vs ゴール数（チーム別）",
        labels={"value": "数", "team_name": "チーム"},
        barmode="group",  # 分组柱状图
        text_auto=True,
    )
    # 显示图表
    st.plotly_chart(fig)
    # --- 🛡️ 守備データ（失点数） ---
    st.header("🛡️ 各チームの守備データ")
    # 各チームの失点数
    defensive_stats = matches.groupby('home_team')['away_score'].sum() + matches.groupby('away_team')['home_score'].sum()
    defensive_stats = defensive_stats.sort_values()
    fig, ax = plt.subplots(figsize=(10, 5))
    defensive_stats.plot(kind='bar', color='red', alpha=0.7, ax=ax)
    ax.set_xlabel("チーム")
    ax.set_ylabel("失点数")
    ax.set_title("チーム別の失点数")
    plt.xticks(rotation=90)
    st.pyplot(fig)
    
    # --- 📈 試合の時間別ゴール数（トレンド） ---
    st.header("📈 試合時間ごとのゴール傾向")
    goals_by_minute = events[events['type_name'] == 'Shot'][['minute']].value_counts().reset_index()
    goals_by_minute.columns = ['minute', 'goal_count']
    goals_by_minute = goals_by_minute.sort_values(by='minute')
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=goals_by_minute, x='minute', y='goal_count', marker="o", ax=ax)
    ax.set_xlabel("時間（分）")
    ax.set_ylabel("ゴール数")
    ax.set_title("ゴールが最も多い時間帯")
    st.pyplot(fig)
    
    
    st.header("🏅 得点ランキング（選手）")
    goal_events = events[(events['type_name'] == 'Shot') & (events['outcome_name'] == 'Goal')]
    top_scorers = (
        goal_events
        .groupby(['player_id', 'player_name', 'team_name'])  # 追加チーム名
        .size()
        .reset_index()
        .rename(columns={0: 'ゴール数'})
        .sort_values(by='ゴール数', ascending=False)
        .head(10)
    )
    top_scorers['国籍'] = top_scorers['team_name'].map(team_country_map)
    top_scorers = top_scorers[['player_name', '国籍', 'ゴール数']]
    st.dataframe(top_scorers, width=600)
    
    st.markdown("---")


with tab3: # 試合可視化比較
    st.header("📊 試合データの可視化")
    st.write("試合ごとのデータをグラフで表示します。")
    # st.sidebar.title("試合を選んでください")
    selected_match = st.selectbox("試合:", match_dict.keys(), index=1,key="match_select_1")
    # mode = st.selectbox("モードを選択:",["時間帯スライダー", "ショットフリーズフレーム","シュート"])
    match_id = match_dict[selected_match]
    home_team = selected_match.split(" vs ")[0]
    away_team = selected_match.split(" vs ")[1]
    competition_stage = matches[matches["match_id"] == match_id].iloc[0][
        "competition_stage"
    ]
    home_score = matches[matches["match_id"] == match_id].iloc[0]["home_score"]
    away_score = matches[matches["match_id"] == match_id].iloc[0]["away_score"]
    st.subheader(f"試合結果: {home_team} {home_score} - {away_score} {away_team}")
    
    hometeam_xi = get_starting_xi(home_team,match_id=match_id)
    awayteam_xi = get_starting_xi(away_team,match_id=match_id)
    # 获取阵型
    hometeam_formation = hometeam_xi["tactics_formation"].iloc[0]
    awayteam_formation = awayteam_xi["tactics_formation"].iloc[0]

    st.subheader(f"{home_team} vs {away_team}")
    col1, col2 = st.columns(2)  # **创建两列并排显示**
    with col1:
        st.subheader(f"🏠 {home_team} ({hometeam_formation})")
        plot_team_formation(home_team, hometeam_formation, hometeam_xi, flip=False)
    with col2:
        st.subheader(f"🛫 {away_team} ({awayteam_formation})")
        plot_team_formation(away_team, awayteam_formation, awayteam_xi, flip=False)
    
    
    st.subheader("シュートの分布")
    joint_shot_plot(match_id=match_id)
    
    st.subheader(f"ヒットマップ")
    col1, col2 = st.columns(2)  # 创建并排两列
    with col1:
        st.subheader(f"🏠 {home_team}")
        heat_map(match_id, home_team)
    with col2:
        st.subheader(f"🛫 {away_team}")
        heat_map(match_id, away_team)
    st.write(
        "このヒートマップは、試合中に特定のチームが相手にプレッシャーをかけたエリアの分布を示しています。\n"
        "- 明るい色ほど、プレッシャーが多く発生していることを意味します。\n"
        "- チームの守備戦術を分析するのに役立ちます。\n\n"
        "例えば：\n"
        "- **ハイプレス（高い位置でのプレッシャー）**：ヒートマップが相手陣内で明るい場合。\n"
        "- **ローラインディフェンス（低い位置での守備）**：ヒートマップが自陣内に集中している場合。\n"
        "- **サイドプレッシング（サイドへの圧力）**：ヒートマップがサイドに明るく表示されている場合。\n\n"
        "この分析を利用することで、コーチングスタッフはチームの守備戦術を評価し、相手に応じた戦術調整を行うことができます。"
    )
    
    
    st.subheader(f"パスネットワーク")
    col1, col2 = st.columns(2)  # 创建并排两列
    with col1:
        st.subheader(f"🏠 {home_team}")
        plot_pass_network(match_id, home_team,away_team)
    with col2:
        st.subheader(f"🛫 {away_team}")
        plot_pass_network(match_id, away_team,home_team)
    st.markdown("""
    ### 🎯 **パスネットワークの分析ポイント**
    #### 🏟 **1. チームのパススタイル**
    - **短いパスが多く、細いラインが密集** → ポゼッション重視
    - **長いパスが多く、太いラインが目立つ** → 速攻・ロングボール戦術

    #### 🔑 **2. キープレイヤーの特定**
    - **⚽ 大きな点の選手** → ボールタッチが多く、攻撃の中心
    - **⚽ パス回数が多い選手** → 司令塔またはビルドアップの要

    #### 📌 **3. 実際のフォーメーションの可視化**
    - **選手の平均ポジション** → 戦術通りか？試合中の変化を分析
    - **サイドバックが高い位置** → 攻撃的布陣（3-4-3, 4-3-3など）
    - **センターフォワードが低い位置** → 偽9番（False 9）

    #### ⚔ **4. チームの攻撃傾向**
    - **右サイドのパスが多い** → 右サイド攻撃重視
    - **中央のパスが多い** → 中央突破戦術
    - **特定エリアのパスが少ない** → 相手のプレス or 戦術的回避
    ---
    """)
    
    
    
    st.subheader(f"パスフロー")
    col1, col2 = st.columns(2)  # 创建并排两列
    with col1:
        st.subheader(f"🏠 {home_team}")
        pass_flow(match_id, home_team)
    with col2:
        st.subheader(f"🛫 {away_team}")
        pass_flow(match_id, away_team)
    st.markdown("""
    ### 🎯 **パスフロー分析のポイント**
    #### ⚽ **1. チームのパス傾向**
    - **濃い色のエリア** → よくパスが行われるエリア（支配率が高いゾーン）。
    - **薄い色のエリア** → あまりパスが行われないエリア（攻撃が少ない or ボールを保持できていない）。
    - **矢印の方向** → チームの主な攻撃方向を示す。
    #### 📌 **2. 攻撃の展開**
    - **中央エリアの色が濃い** → 中央突破を重視した戦術。
    - **サイドが濃く矢印がゴール方向** → ウィングからのクロスやドリブル突破を多用。
    - **左右対称のパス流れ** → 両サイドをバランスよく使う攻撃。
    - **一方のサイドに偏り** → 片側の選手を中心とした攻撃パターン。
    #### 🛡 **3. 守備の弱点を分析**
    - **相手のパスが集中するエリア** → 守備の対応が必要なゾーン。
    - **自陣ゴール前の濃さが異なる** → ゴール前での守備の強弱を示唆。
    ---
    """)

with tab4: #タイムスタンプ
    st.header("🔍 チーム分析")
    st.write("チームの戦略、プレースタイルを分析します。")
    
    st.title("試合を選んでください")
    selected_match = st.selectbox("試合:", match_dict.keys(), index=2,key="match_select_2")
    mode = st.selectbox("モードを選択:",["時間帯スライダー", "ショットフリーズフレーム"])
    match_id = match_dict[selected_match]
    home_team = selected_match.split(" vs ")[0]
    away_team = selected_match.split(" vs ")[1]
    competition_stage = matches[matches["match_id"] == match_id].iloc[0][
        "competition_stage"
    ]
    home_score = matches[matches["match_id"] == match_id].iloc[0]["home_score"]
    away_score = matches[matches["match_id"] == match_id].iloc[0]["away_score"]
    st.subheader(f"試合結果: {home_team} {home_score} - {away_score} {away_team}")
    
    
    frame_df = sb.frames(match_id=match_id, fmt="dataframe")
    frame_df = frame_df.rename(columns={"location":"player_location"})
    event_df = sb.events(match_id=match_id)
    event_df["timestring"] = event_df.apply(create_timestring, axis=1)

    df = pd.merge(frame_df, event_df, on="id", how="right")
    df = df.sort_values("timestring")
    
    ##xG
    tab_a ,tab_b = st.tabs(["xG","Goal"])
    with tab_a:
        shots_df = event_df[event_df["type"] == "Shot"].copy()
        shots_df["shot_statsbomb_xg"] = shots_df["shot_statsbomb_xg"].fillna(0).astype(float)
        home_shots = shots_df[shots_df["team"] == home_team].copy()
        away_shots = shots_df[shots_df["team"] == away_team].copy()
        # 提取分钟数
        def extract_minutes(timestring):
            """ 从 'MM:SS' 提取分钟数 """
            minutes, _ = map(int, timestring.split(":"))
            return minutes
        home_shots["minute"] = home_shots["timestring"].apply(extract_minutes)
        away_shots["minute"] = away_shots["timestring"].apply(extract_minutes)
        # 处理重复分钟，按分钟累加 xG
        home_shots = home_shots.groupby("minute")["shot_statsbomb_xg"].sum().cumsum().reset_index()
        away_shots = away_shots.groupby("minute")["shot_statsbomb_xg"].sum().cumsum().reset_index()
        all_shot_minutes = sorted(set(home_shots["minute"]).union(set(away_shots["minute"])))
        home_shots = home_shots.set_index("minute").reindex(all_shot_minutes, method="ffill").reset_index()
        away_shots = away_shots.set_index("minute").reindex(all_shot_minutes, method="ffill").reset_index()
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(home_shots["minute"], home_shots["shot_statsbomb_xg"], marker="o",
                linestyle="-", label=f"{home_team} xG", color="blue")
        ax.plot(away_shots["minute"], away_shots["shot_statsbomb_xg"], marker="o",
                linestyle="-", label=f"{away_team} xG", color="red")
        # 设置 x 轴刻度（每 10 分钟一个刻度）
        ax.set_xticks(np.arange(0, max(all_shot_minutes) + 1, 10))
        ax.set_xlabel("試合時間 (分)")
        ax.set_ylabel("累積xG")
        ax.set_title(f"{home_team} vs {away_team} - xG推移")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
    
    
    with tab_b:
        shot_df= event_df[event_df["type"] == "Shot"].copy()
        goals_df = shot_df[shot_df["shot_outcome"] == "Goal"].copy()
        goals_df["minute"] = goals_df["timestring"].apply(extract_minutes)
        
        if not goals_df.empty:
            goals_df["minute"] = goals_df["timestring"].apply(extract_minutes)
            match_duration = int(max(goals_df["minute"].max(), 90) + 5)  # 取最大进球分钟数 +5
        else:
            match_duration = 95
        unique_teams = goals_df["team"].unique()
        fig, ax = plt.subplots(figsize=(10, 2))
        # ax.hlines(y=0, xmin=-5, xmax=match_duration, color="black", linewidth=2)
        if not goals_df.empty:
            for idx, row in goals_df.iterrows():
                goal_time = row["minute"]
                team = row["team"]
                color = country_colors.get(team, "gray")  # 默认颜色为灰色
                # 交错箭头的 y 位置
                
                ax.annotate(
                    "",  # 取消 "G" 文字，仅显示箭头
                    xy=(goal_time, 0),  # 箭头指向的位置（x 轴上的进球时间）
                    xytext=(goal_time,0.08),  # 箭头的起点（交错放置）
                    ha="left",
                    fontsize=12,
                    color=color,
                    arrowprops=dict(arrowstyle="->", color=color, linewidth=1.5),
                )
        legend_patches = [plt.Line2D([0], [0], color=country_colors[team], lw=4, label=team) for team in unique_teams]
        ax.legend(handles=legend_patches, loc="upper right", fontsize=10, title="チーム", frameon=False)

        ax.set_xticks(np.arange(0, match_duration + 1, 10))
        ax.set_yticks([])  # 隐藏 y 轴
        ax.set_xlim(0, match_duration)  # x 轴范围
        ax.set_xlabel("試合時間 (分)")
        ax.set_title("ゴールタイムライン（得点時間）")
        # 移除 y 轴边框
        ax.spines["left"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False) 
        st.pyplot(fig)
        
        
        
    
    if mode == "時間帯スライダー":
        chosen_timestamp = st.select_slider(
            "時間帯を選んでください",
            options=df[(df["visible_area"].notna()) | (df["type"] == "Shot")][
                "timestring"
            ].unique()
        )
        event_dict = get_event_dict(df=df, chosen_timestamp=chosen_timestamp)
        
        displayed_event = st.selectbox("イベントを選んでください",options=event_dict.keys())
        voronoi = st.checkbox("支配されたスペースを強調表示",)
        st.pyplot(
            create_plot(
                df,
                event_dict,
                chosen_timestamp,
                displayed_event,
                voronoi,
                home_team,
                away_team
            )
        )

    elif mode == "ショットフリーズフレーム":
        tab1, tab2 = st.tabs(["📈 チャート", "📄 シュートの情報"])
        
        
        shot_info = event_df[event_df["shot_outcome"].notna()][
            [
                "player",
                "timestring",
                "shot_outcome",
                "shot_statsbomb_xg",
                "shot_technique",
                "shot_body_part"
            ]
        ]
        shot_info.index = range(1, len(shot_info) +1)
        
        with tab1:
            shot_cols = [
                "player",
                "team",
                "timestring",
                "shot_outcome",
                "shot_freeze_frame",
                "location",
                "shot_end_location"
            ]
            shot_df = event_df[event_df["shot_outcome"].notna()][shot_cols]
            shot_df["tag"] = (
                shot_df["player"]
                + " - "
                + shot_df["timestring"]
                + " ( "
                + shot_df["shot_outcome"]
                + " ) "
            )
            tag = st.selectbox("シュートを選んでください", options=shot_df["tag"].to_list())
            keeper_cone = st.checkbox("ハイライトキーパーコーンビュー")
            
            st.pyplot(shot_freeze_frame(shot_df,tag,home_team,away_team,keeper_cone))
        
        with tab2:
            shot_info.columns = [
                "Player",
                "Timestamp",
                "Shot Outcome",
                "xG",
                "Technique",
                "Body Part"
            ]
            st.dataframe(shot_info)


with tab5:
    st.header("🎮 Football Manager 戦術学習 & 応用")
    st.write("この可視化ツールを活用することで、**実際の試合データを分析し、チームの戦術を学ぶ** ことができます。試合のデータを基に、戦術の特徴やチームのプレースタイルを可視化し、**FM2024の戦術作成や模倣** に応用できます。")
    # 介绍内容
    st.write("")
    st.markdown("""
    ## ⚽ **このツールで戦術を学ぶ**
    
    ---
    #### 🎯 **学べる戦術要素**
    ##### 📌 1. 戦術スタイルの理解
    - **ポゼッション戦術**（短いパスとビルドアップを重視）  
    - **カウンター戦術**（縦に速い攻撃が多い）  
    - **ウィングプレー**（サイドからの攻撃が主体）  
    - **ゲーゲンプレス**（高い位置での積極的なプレス）  
    ##### 📌 2. チームのプレーパターン分析
    - **パスネットワーク** → どの選手がプレーメーカーか？  
    - **パスフロー** → 攻撃の方向性は？  
    - **タイムスタンプ分析** → 試合のどの時間帯で優勢か？  
    ---
    #### 🎮 **FM2024での戦術応用**
    ##### 🔧 **1. 戦術作成**
    リアルな試合データから戦術スタイルを分析し、**自分だけのオリジナル戦術をFM2024で作成** できます。  
    例えば：
    - **短いパスが多く、ポゼッション重視** → FMで **ティキ・タカ戦術** を作る  
    - **ロングボールが多く、カウンター狙い** → FMで **ダイレクトプレー** を設定  
    ##### 🔍 **2. 実際のチーム戦術の再現**
    - データを基に、**実際のチーム（例：マンチェスター・シティやリヴァプール）の戦術を再現** し、FM2024でプレイ可能！分析したデータを元に、フォーメーションや選手の役割をセットアップできます
    ---
    #### 🚀 **今後の拡張予定**
    - 🏆 **プレイヤーデータの追加**（個別選手の詳細分析）
    - 📊 **FMデータの統合**（FMゲームデータと実際の試合データの比較）
    - 🔄 **戦術シミュレーション**（FM戦術の勝率分析）
    ---
    ### 🎮 **さあ、リアルな試合データを学び、FM2024で最強の戦術を作ろう！**
    """)
