import streamlit as st
from mplsoccer import VerticalPitch, Sbopen
import matplotlib.pyplot as plt
import matplotlib as mpl
from statsbombpy import sb
from matplotlib.colors import to_rgba
import numpy as np
import seaborn as sns
from scipy.ndimage import gaussian_filter
from mplsoccer import Pitch, VerticalPitch, FontManager, Sbopen
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patheffects as path_effects
import pandas as pd

parser = Sbopen()

matches = sb.matches(competition_id=55, season_id=282)
match_dict = {
    f"{home} vs {away}": match_id
    for match_id, home, away in zip(matches["match_id"], matches["home_team"], matches["away_team"])
}
country_colors = {
    "Poland": "#ffffff", "Denmark": "#C60C30", "Portugal": "#006400",
    "Germany": "#000000", "France": "#0055A4", "Netherlands": "#E77E02",
    "Belgium": "#FFD700", "Spain": "#C60C30", "Croatia": "#FF0000",
    "England": "#002366", "Serbia": "#DC143C", "Switzerland": "#FF0000",
    "Scotland": "#006cb7", "Hungary": "#008d55", "Albania": "#ed1b24",
    "Italy": "#009247", "Slovenia": "#005aab", "Austria": "#ed1b24",
    "Slovakia": "#005aab", "Romania": "#ffde00", "Ukraine": "#005aab",
    "Turkey": "#ed1b24", "Georgia": "#fffffc", "Czech Republic": "#005aab",
}


# ✅
def get_starting_xi(team_name,match_id):
    parser = Sbopen()
    event, related, freeze, tactics = parser.event(match_id=match_id)
    starting_xi_event = event.loc[(event["type_name"] == "Starting XI") & 
                                  (event["team_name"] == team_name), ["id", "tactics_formation"]]
    starting_xi = tactics.merge(starting_xi_event, on="id")
    return starting_xi

# ✅ 
def plot_team_formation(team_name, formation, starting_xi, flip=False):
    pitch = VerticalPitch(goal_type="box")
    fig, ax = pitch.draw(figsize=(6, 8.72))
    # 获取球队颜色（默认灰
    team_color = country_colors.get(team_name, "#808080")
    # 绘制球员
    pitch.formation(formation, positions=starting_xi.position_id, kind='text',
                    text=starting_xi.player_name.str.replace(' ', '\n'),
                    va='center', ha='center', fontsize=16, ax=ax, flip=flip)
    # 绘制球员站位（散点）
    mpl.rcParams['hatch.linewidth'] = 3
    mpl.rcParams['hatch.color'] = '#a50044'
    pitch.formation(formation, positions=starting_xi.position_id, kind='scatter',
                    c=team_color, linewidth=3, s=500, xoffset=-8, ax=ax, flip=flip)
    # 标题
    ax.set_title(f"{team_name} ({formation})", fontsize=14, color=team_color, fontweight="bold")
    st.pyplot(fig)  # ✅ Streamlit 显示图像

# ✅
def heat_map(match_id,team_name):
    events, related, freeze, players = parser.event(match_id=match_id)
    mask_pressure = (events.team_name == team_name) & (events.type_name == "Pressure")
    df_pressure = events.loc[mask_pressure, ['x', 'y']]
    mask_pressure = (events.team_name == team_name) & (events.type_name == "Pass")
    df_pass = events.loc[mask_pressure, ["x", "y", "end_x", "end_y"]]
    robotto_regular = FontManager()
    # path effects
    path_eff = [path_effects.Stroke(linewidth=1.5, foreground='black'),
                path_effects.Normal()]
    # see the custom colormaps example for more ideas on setting colormaps
    pearl_earring_cmap = LinearSegmentedColormap.from_list("Pearl Earring - 10 colors",
                                                        ['#15242e', '#4393c4'], N=10)
    pitch = Pitch(pitch_type='statsbomb', line_zorder=2,
              pitch_color='#22312b', line_color='#efefef')
    
    fig, axs = pitch.grid(endnote_height=0.03, endnote_space=0,
                      # leave some space for the colorbar
                      grid_width=0.88, left=0.025,
                      title_height=0.06, title_space=0,
                      # Turn off the endnote/title axis. I usually do this after
                      # I am happy with the chart layout and text placement
                      axis=False,
                        grid_height=0.86)
    fig.set_facecolor('#22312b')
    # plot heatmap
    bin_statistic = pitch.bin_statistic(df_pressure.x, df_pressure.y, statistic='count', bins=(25, 25))
    bin_statistic['statistic'] = gaussian_filter(bin_statistic['statistic'], 1)
    pcm = pitch.heatmap(bin_statistic, ax=axs['pitch'], cmap='hot', edgecolors='#22312b')
    # add cbar
    ax_cbar = fig.add_axes((0.915, 0.093, 0.03, 0.786))
    cbar = plt.colorbar(pcm, cax=ax_cbar)
    cbar.outline.set_edgecolor('#efefef')
    cbar.ax.yaxis.set_tick_params(color='#efefef')
    plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#efefef')
    for label in cbar.ax.get_yticklabels():
        label.set_fontproperties(robotto_regular.prop)
        label.set_fontsize(15)
    
    # endnote and title
    ax_title = axs['title'].text(0.5, 0.5, f'Pressure applied by {team_name}', color='white',
                                va='center', ha='center', path_effects=path_eff,
                                fontproperties=robotto_regular.prop, fontsize=30)

    st.pyplot(fig)
    plt.close(fig)

# ✅
def plot_pass_network(match_id, team_name,opponenet):
    """ 绘制球队的传球网络图 """
    # 解析事件数据
    events, related, freeze, players = parser.event(match_id=match_id)
    TEAM = team_name
    OPPONENT = opponenet
    events.loc[events.tactics_formation.notnull(), 'tactics_id'] = events.loc[events.tactics_formation.notnull(), 'id']
    events[['tactics_id', 'tactics_formation']] = events.groupby('team_name')[['tactics_id', 'tactics_formation']].ffill()
    formation_dict = {1: 'GK', 2: 'RB', 3: 'RCB', 4: 'CB', 5: 'LCB', 6: 'LB', 7: 'RWB',
                  8: 'LWB', 9: 'RDM', 10: 'CDM', 11: 'LDM', 12: 'RM', 13: 'RCM',
                  14: 'CM', 15: 'LCM', 16: 'LM', 17: 'RW', 18: 'RAM', 19: 'CAM',
                  20: 'LAM', 21: 'LW', 22: 'RCF', 23: 'ST', 24: 'LCF', 25: 'SS'}
    players['position_abbreviation'] = players.position_id.map(formation_dict)
    
    sub = events.loc[events.type_name == 'Substitution',['tactics_id', 'player_id', 'substitution_replacement_id','substitution_replacement_name']]
    players_sub = players.merge(sub.rename({'tactics_id': 'id'}, axis='columns'),
                                on=['id', 'player_id'], how='inner', validate='1:1')
    players_sub = (players_sub[['id', 'substitution_replacement_id', 'position_abbreviation']]
                .rename({'substitution_replacement_id': 'player_id'}, axis='columns'))
    players = pd.concat([players, players_sub])
    players.rename({'id': 'tactics_id'}, axis='columns', inplace=True)
    players = players[['tactics_id', 'player_id', 'position_abbreviation']]
    # add on the position the player was playing in the formation to the events dataframe
    events = events.merge(players, on=['tactics_id', 'player_id'], how='left', validate='m:1')
    # add on the position the receipient was playing in the formation to the events dataframe
    events = events.merge(players.rename({'player_id': 'pass_recipient_id'},
                                        axis='columns'), on=['tactics_id', 'pass_recipient_id'],
                        how='left', validate='m:1', suffixes=['', '_receipt'])
    formation_dict = events.groupby('team_name').tactics_formation.unique().to_dict()
    FORMATION = formation_dict[TEAM][0]
    pass_cols = ['id', 'position_abbreviation', 'position_abbreviation_receipt']
    passes_formation = events.loc[(events.team_name == TEAM) & (events.type_name == 'Pass') &
                                (events.tactics_formation == FORMATION) &
                                (events.position_abbreviation_receipt.notnull()), pass_cols].copy()
    location_cols = ['position_abbreviation', 'x', 'y']
    location_formation = events.loc[(events.team_name == TEAM) &
                                    (events.type_name.isin(['Pass', 'Ball Receipt'])) &
                                    (events.tactics_formation == FORMATION), location_cols].copy()
    # average locations
    average_locs_and_count = (location_formation.groupby('position_abbreviation')
                            .agg({'x': ['mean'], 'y': ['mean', 'count']}))
    average_locs_and_count.columns = ['x', 'y', 'count']
    # calculate the number of passes between each position (using min/ max so we get passes both ways)
    passes_formation['pos_max'] = (passes_formation[['position_abbreviation',
                                                    'position_abbreviation_receipt']]
                                .max(axis='columns'))
    passes_formation['pos_min'] = (passes_formation[['position_abbreviation',
                                                    'position_abbreviation_receipt']]
                                .min(axis='columns'))
    passes_between = passes_formation.groupby(['pos_min', 'pos_max']).id.count().reset_index()
    passes_between.rename({'id': 'pass_count'}, axis='columns', inplace=True)
    # add on the location of each player so we have the start and end positions of the lines
    passes_between = passes_between.merge(average_locs_and_count, left_on='pos_min', right_index=True)
    passes_between = passes_between.merge(average_locs_and_count, left_on='pos_max', right_index=True,
                                        suffixes=['', '_end'])
    MAX_LINE_WIDTH = 18
    MAX_MARKER_SIZE = 3000
    passes_between['width'] = (passes_between.pass_count / passes_between.pass_count.max() *
                            MAX_LINE_WIDTH)
    average_locs_and_count['marker_size'] = (average_locs_and_count['count']
                                            / average_locs_and_count['count'].max() * MAX_MARKER_SIZE)
    MIN_TRANSPARENCY = 0.3
    color = np.array(to_rgba('white'))
    color = np.tile(color, (len(passes_between), 1))
    c_transparency = passes_between.pass_count / passes_between.pass_count.max()
    c_transparency = (c_transparency * (1 - MIN_TRANSPARENCY)) + MIN_TRANSPARENCY
    color[:, 3] = c_transparency
    URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/oswald/Oswald%5Bwght%5D.ttf"
    oswald_regular = FontManager(URL)
    pitch = Pitch(
    pitch_type="statsbomb", pitch_color="white", line_color="black", linewidth=1,)
    fig, axs = pitch.grid(
        figheight=10,
        title_height=0.08,
        endnote_space=0,
        # Turn off the endnote/title axis. I usually do this after
        # I am happy with the chart layout and text placement
        axis=False,
        title_space=0,
        grid_height=0.82,
        endnote_height=0.01,
    )
    fig.set_facecolor("white")
    pass_lines = pitch.lines(
        passes_between.x,
        passes_between.y,
        passes_between.x_end,
        passes_between.y_end,
        lw=passes_between.width,
        color="#BF616A",
        zorder=1,
        ax=axs["pitch"],
    )
    pass_nodes = pitch.scatter(
        average_locs_and_count.x,
        average_locs_and_count.y,
        s=average_locs_and_count.marker_size,
        color="#BF616A",
        edgecolors="black",
        linewidth=0.5,
        alpha=1,
        ax=axs["pitch"],
    )
    pass_nodes_internal = pitch.scatter(
        average_locs_and_count.x,
        average_locs_and_count.y,
        s=average_locs_and_count.marker_size / 2,
        color="white",
        edgecolors="black",
        linewidth=0.5,
        alpha=1,
        ax=axs["pitch"],
    )
    for index, row in average_locs_and_count.iterrows():
        text = pitch.annotate(
            row.name,
            xy=(row.x, row.y),
            c="black",
            va="center",
            ha="center",
            size=15,
            weight="bold",
            ax=axs["pitch"],
            fontproperties=oswald_regular.prop,
        )
        text.set_path_effects([path_effects.withStroke(linewidth=1, foreground="white")])
    axs["endnote"].text(
        1,
        1,
        "@Tokyo_TTC_dsAI_riyat",
        color="black",
        va="center",
        ha="right",
        fontsize=15,
        fontproperties=oswald_regular.prop,
    )
    TITLE_TEXT = f"{TEAM}, {FORMATION} formation"
    axs["title"].text(
        0.5,
        0.7,
        TITLE_TEXT,
        color="black",
        va="center",
        ha="center",
        fontproperties=oswald_regular.prop,
        fontsize=30,
    )
    axs["title"].text(
        0.5,
        0.15,
        OPPONENT,
        color="black",
        va="center",
        ha="center",
        fontproperties=oswald_regular.prop,
        fontsize=18,
    )    
    
    st.pyplot(fig)
    plt.close(fig)

# ✅
def pass_flow(match_id, team_name):
    events, related, freeze, players = parser.event(match_id=match_id)
    mask_team1 = (events.type_name == 'Pass') & (events.team_name == team_name)
    
    df_pass = events.loc[mask_team1, ['x', 'y', 'end_x', 'end_y', 'outcome_name']]
    mask_complete = df_pass.outcome_name.isnull()
    pitch = Pitch(pitch_type='statsbomb',  line_zorder=2, line_color='#c7d5cc', pitch_color='#22312b')
    bins = (6, 4)   
    fig, ax = pitch.draw(figsize=(16, 11), constrained_layout=True, tight_layout=False)
    fig.set_facecolor('#22312b')
    # plot the heatmap - darker colors = more passes originating from that square
    bs_heatmap = pitch.bin_statistic(df_pass.x, df_pass.y, statistic='count', bins=bins)
    hm = pitch.heatmap(bs_heatmap, ax=ax, cmap='Blues')
    # plot the pass flow map with a single color ('black') and length of the arrow (5)
    fm = pitch.flow(df_pass.x, df_pass.y, df_pass.end_x, df_pass.end_y,
                    color='black', arrow_type='same',
                    arrow_length=5, bins=bins, ax=ax)
    ax_title = ax.set_title(f'{team_name} pass flow map', fontsize=30, pad=-20)
    st.pyplot(fig)
    fig, ax = pitch.draw(figsize=(16, 11), constrained_layout=True, tight_layout=False)
    fig.set_facecolor('#22312b')
    # plot the heatmap - darker colors = more passes originating from that square
    bs_heatmap = pitch.bin_statistic(df_pass.x, df_pass.y, statistic='count', bins=bins)
    hm = pitch.heatmap(bs_heatmap, ax=ax, cmap='Greens')
    # plot the pass flow map with a single color and the
    # arrow length equal to the average distance in the cell
    fm = pitch.flow(df_pass.x, df_pass.y, df_pass.end_x, df_pass.end_y, color='black',
                    arrow_type='average', bins=bins, ax=ax)
    ax_title = ax.set_title(f'{team_name} pass flow map ', fontsize=30, pad=-20)
    st.pyplot(fig)
    plt.close(fig)

def joint_shot_plot(match_id):
    parser = Sbopen()
    df, related, freeze, tactics = parser.event(match_id=match_id)
    pitch = Pitch(pad_top=0.05, pad_right=0.05, pad_bottom=0.05, pad_left=0.05, line_zorder=2)
    
    # subset the shots
    df_shots = df[df.type_name == 'Shot'].copy()
    
    # subset the shots for each team
    team1, team2 = df_shots.team_name.unique()
    df_team1 = df_shots[df_shots.team_name == team1].copy()
    df_team2 = df_shots[df_shots.team_name == team2].copy()
    
    # Adjust team1 coordinates to align left-to-right attacking direction
    df_team1['x'] = pitch.dim.right - df_team1.x
    
    fig, axs = pitch.jointgrid(figheight=10, left=None, bottom=0.075, grid_height=0.8,
                               axis=False, title_height=0, endnote_height=0)
    
    bs1 = pitch.bin_statistic(df_team1.x, df_team1.y, bins=(18, 12))
    bs2 = pitch.bin_statistic(df_team2.x, df_team2.y, bins=(18, 12))
    
    # Normalize across both teams
    vmax = max(bs2['statistic'].max(), bs1['statistic'].max())
    vmin = min(bs2['statistic'].min(), bs1['statistic'].min())
    
    # Remove zero-shot bins
    bs1['statistic'][bs1['statistic'] == 0] = np.nan
    bs2['statistic'][bs2['statistic'] == 0] = np.nan
    
    # Plot heatmaps
    pitch.heatmap(bs1, ax=axs['pitch'], cmap='Reds', vmin=vmin, vmax=vmax, edgecolor='#f9f9f9')
    pitch.heatmap(bs2, ax=axs['pitch'], cmap='Blues', vmin=vmin, vmax=vmax, edgecolor='#f9f9f9')
    
    # Histograms with KDE plot
    sns.histplot(y=df_team1.y, ax=axs['left'], color='red', linewidth=1, kde=True)
    sns.histplot(x=df_team1.x, ax=axs['top'], color='red', linewidth=1, kde=True)
    sns.histplot(x=df_team2.x, ax=axs['top'], color='blue', linewidth=1, kde=True)
    sns.histplot(y=df_team2.y, ax=axs['right'], color='blue', linewidth=1, kde=True)
    
    # Team names on the pitch
    axs['pitch'].text(x=15, y=70, s=team1, color='red', ha='center', va='center', fontsize=30)
    axs['pitch'].text(x=105, y=70, s=team2, color='blue', ha='center', va='center', fontsize=30)
    
    st.pyplot(fig)
    plt.close(fig)












