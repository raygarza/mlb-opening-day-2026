import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os

# Page config
st.set_page_config(
    page_title="Opening Day 2026",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data
@st.cache_data
def load_data():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base, 'data')
    
    games = pd.read_csv(os.path.join(data_path, 'games_model.csv'))
    arsenal = pd.read_csv(os.path.join(data_path, 'arsenal_summary.csv'))
    lineups = pd.read_csv(os.path.join(data_path, 'lineup_scores.csv'))
    fg = pd.read_csv(os.path.join(data_path, 'fg_stats_2025.csv'))
    
    return games, arsenal, lineups, fg

games, arsenal, lineups, fg = load_data()

# Sidebar
st.sidebar.title("⚾ Opening Day 2026")
st.sidebar.markdown("A deep dive into every Opening Day game — pitchers, lineups, parks, and projections.")

page = st.sidebar.radio(
    "Navigate",
    ["Home", "Run Environment", "Arsenal Fingerprints", "Fade or Ride", "Lineup Quality"]
)

# Home page
if page == "Home":
    st.title("Opening Day 2026")
    st.subheader("Every game. Every starter. Every number that matters.")
    st.markdown("---")
    st.markdown("""
    Baseball is the most data-rich game ever played.
    
    This project models every Opening Day 2026 matchup using real 2025 Statcast data, 
    FanGraphs pitching metrics, projected lineups from MLB.com, and park factors. 
    The goal is not to predict winners. The goal is to understand the run environment 
    each game is walking into before a single pitch is thrown.
    
    Use the sidebar to explore.
    """)
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Opening Day Games", "15")
    col2.metric("Confirmed Starters", "27")
    col3.metric("Pitches Analyzed", "72,802")
    col4.metric("Lineups Modeled", "28")

# Run Environment page
elif page == "Run Environment":
    st.title("Projected Run Environment")
    st.markdown("""
    Every Opening Day game has a run environment. This model combines starter quality (xERA), 
    lineup strength (xwOBA), and park factors to project how many total runs should score 
    in each game. Higher is more offense. Lower is a pitcher's duel.
    """)
    st.markdown("---")

    run_plot = games[['away_team', 'home_team', 'away_starter',
                       'home_starter', 'total_proj_runs', 'park_factor']].dropna().copy()
    run_plot['matchup'] = run_plot['away_team'] + ' @ ' + run_plot['home_team']
    run_plot = run_plot.sort_values('total_proj_runs', ascending=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=run_plot['total_proj_runs'],
        y=run_plot['matchup'],
        mode='markers+text',
        text=run_plot['total_proj_runs'].round(1).astype(str),
        textposition='middle right',
        textfont=dict(size=11),
        marker=dict(
            size=18,
            color=run_plot['total_proj_runs'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title='Total Runs'),
            line=dict(width=1, color='white')
        ),
        hovertemplate='<b>%{y}</b><br>Projected runs: %{x:.2f}<extra></extra>'
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            title='Projected Total Runs',
            gridcolor='#334155',
            range=[5, 15]
        ),
        yaxis=dict(
            gridcolor='#334155',
        ),
        height=600,
        margin=dict(l=250, r=100, t=40, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Game detail table
    st.markdown("### Game by Game Breakdown")
    display = run_plot[['matchup', 'away_starter', 'home_starter', 
                         'park_factor', 'total_proj_runs']].copy()
    display.columns = ['Matchup', 'Away Starter', 'Home Starter', 'Park Factor', 'Proj. Runs']
    display = display.sort_values('Proj. Runs', ascending=False)
    st.dataframe(display, use_container_width=True, hide_index=True)


# Fade or Ride page
elif page == "Fade or Ride":
    st.title("Fade or Ride")
    st.markdown("""
    ERA tells you what happened. xERA tells you what should have happened.
    
    Pitchers above the diagonal line posted ERAs better than their underlying metrics 
    suggest they deserved. They got lucky. **Fade them.** Pitchers below the line 
    were better than their ERA showed. They got unlucky. **Ride them.**
    
    Bubble size = innings pitched. Bigger bubble means more data, more confidence.
    """)
    st.markdown("---")

    fg_plot = fg[['Name', 'ERA', 'xERA', 'IP', 'WAR']].copy()
    fg_plot['gap'] = fg_plot['ERA'] - fg_plot['xERA']
    fg_plot['verdict'] = fg_plot['gap'].apply(
        lambda x: 'Fade (got lucky)' if x < -0.5
        else 'Ride (got unlucky)' if x > 0.5
        else 'True to form'
    )

    colors = {
        'Fade (got lucky)':   '#ef4444',
        'Ride (got unlucky)': '#22c55e',
        'True to form':       '#94a3b8'
    }

    fig = go.Figure()
    min_val, max_val = 1.5, 5.5

    for verdict, group in fg_plot.groupby('verdict'):
        fig.add_trace(go.Scatter(
            x=group['ERA'],
            y=group['xERA'],
            mode='markers+text',
            name=verdict,
            text=group['Name'],
            textposition='top center',
            textfont=dict(size=9, color='white'),
            marker=dict(
                size=group['IP'] / 15,
                color=colors[verdict],
                opacity=0.85,
                line=dict(width=1, color='white')
            ),
            hovertemplate='<b>%{text}</b><br>ERA: %{x}<br>xERA: %{y}<extra></extra>'
        ))

    fig.add_trace(go.Scatter(
        x=[min_val, max_val],
        y=[min_val, max_val],
        mode='lines',
        line=dict(color='#475569', dash='dash', width=1.5),
        showlegend=False,
        hoverinfo='skip'
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            title='ERA (what happened)',
            gridcolor='#334155',
            range=[min_val, max_val]
        ),
        yaxis=dict(
            title='xERA (what should have happened)',
            gridcolor='#334155',
            range=[min_val, max_val]
        ),
        legend=dict(
            bgcolor='rgba(0,0,0,0)',
            bordercolor='#334155',
            borderwidth=1
        ),
        height=650,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Verdict table
    st.markdown("### The Verdicts")
    col1, col2, col3 = st.columns(3)

    fade = fg_plot[fg_plot['verdict'] == 'Fade (got lucky)'][['Name','ERA','xERA','IP']].copy()
    fade['gap'] = (fade['ERA'] - fade['xERA']).abs().round(2)
    fade = fade.sort_values('gap', ascending=False)

    ride = fg_plot[fg_plot['verdict'] == 'Ride (got unlucky)'][['Name','ERA','xERA','IP']].copy()
    ride['gap'] = (ride['ERA'] - ride['xERA']).abs().round(2)
    ride = ride.sort_values('gap', ascending=False)

    true = fg_plot[fg_plot['verdict'] == 'True to form'][['Name','ERA','xERA','IP']].copy()

    with col1:
        st.markdown("#### 🔴 Fade")
        st.dataframe(fade, hide_index=True, use_container_width=True)

    with col2:
        st.markdown("#### 🟢 Ride")
        st.dataframe(ride, hide_index=True, use_container_width=True)

    with col3:
        st.markdown("#### ⚪ True to Form")
        st.dataframe(true, hide_index=True, use_container_width=True)


# Arsenal Fingerprints page
elif page == "Arsenal Fingerprints":
    st.title("Arsenal Fingerprints")
    st.markdown("""
    Every pitcher has a signature. A unique combination of pitch types, velocities, 
    and movement profiles that defines how they attack hitters. This page maps the 
    complete arsenal for every Opening Day starter using 72,802 pitches from the 2025 season.
    
    Select a pitcher to explore their full pitch mix — how hard they throw each pitch, 
    how much it moves, and how often hitters miss it completely.
    """)
    st.markdown("---")

    # Pitcher selector
    pitchers = sorted(arsenal['pitcher_name'].unique())
    selected = st.selectbox("Select a pitcher", pitchers)

    pa = arsenal[arsenal['pitcher_name'] == selected].copy()

    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pitch Types", len(pa))
    
    top_pitch = pa.sort_values('usage_pct', ascending=False).iloc[0]
    col2.metric("Primary Pitch", top_pitch['pitch_name'])
    col3.metric("Primary Velo", f"{top_pitch['avg_velo']:.1f} mph")
    
    nastiest = pa.sort_values('whiff_rate', ascending=False).iloc[0]
    col4.metric("Nastiest Pitch", f"{nastiest['pitch_name']} ({nastiest['whiff_rate']:.1%} whiff)")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    # Whiff rate bar chart
    with col_left:
        st.markdown("#### Whiff Rate by Pitch")
        pa_sorted = pa.sort_values('whiff_rate', ascending=True)
        fig_whiff = go.Figure(go.Bar(
            x=pa_sorted['whiff_rate'],
            y=pa_sorted['pitch_name'],
            orientation='h',
            marker=dict(
                color=pa_sorted['whiff_rate'],
                colorscale='Blues',
                line=dict(width=0.5, color='white')
            ),
            text=pa_sorted['whiff_rate'].apply(lambda x: f"{x:.1%}"),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Whiff Rate: %{x:.1%}<extra></extra>'
        ))
        fig_whiff.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(gridcolor='#334155', tickformat='.0%'),
            yaxis=dict(gridcolor='#334155'),
            height=350,
            margin=dict(l=20, r=60, t=20, b=20)
        )
        st.plotly_chart(fig_whiff, use_container_width=True)

    # Usage pie chart
    with col_right:
        st.markdown("#### Pitch Mix")
        fig_pie = go.Figure(go.Pie(
            labels=pa['pitch_name'],
            values=pa['usage_pct'],
            hole=0.4,
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Usage: %{value:.1f}%<extra></extra>'
        ))
        fig_pie.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Movement scatter for this pitcher
    st.markdown("#### Movement Profile")
    fig_mov = go.Figure()

    pitch_colors_map = px.colors.qualitative.Plotly
    for i, (_, pitch) in enumerate(pa.iterrows()):
        fig_mov.add_trace(go.Scatter(
            x=[pitch['pfx_x_in']],
            y=[pitch['pfx_z_in']],
            mode='markers+text',
            name=pitch['pitch_name'],
            text=[pitch['pitch_name']],
            textposition='top center',
            textfont=dict(size=11, color='white'),
            marker=dict(
                size=pitch['usage_pct'] * 1.5,
                color=pitch_colors_map[i % len(pitch_colors_map)],
                opacity=0.9,
                line=dict(width=1, color='white')
            ),
            hovertemplate=(
                f"<b>{pitch['pitch_name']}</b><br>"
                f"Horizontal: {pitch['pfx_x_in']:.1f} in<br>"
                f"Vertical: {pitch['pfx_z_in']:.1f} in<br>"
                f"Usage: {pitch['usage_pct']:.1f}%<br>"
                f"Velo: {pitch['avg_velo']:.1f} mph<extra></extra>"
            )
        ))

    fig_mov.add_hline(y=0, line_color='#475569', line_width=1)
    fig_mov.add_vline(x=0, line_color='#475569', line_width=1)

    fig_mov.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(title='Horizontal Movement (inches)', gridcolor='#334155'),
        yaxis=dict(title='Vertical Movement (inches)', gridcolor='#334155'),
        height=450,
        showlegend=False
    )
    st.plotly_chart(fig_mov, use_container_width=True)

    # Raw stats table
    st.markdown("#### Full Arsenal Stats")
    display_cols = ['pitch_name', 'usage_pct', 'avg_velo', 'avg_spin', 
                    'whiff_rate', 'pfx_x_in', 'pfx_z_in']
    display = pa[display_cols].copy()
    display.columns = ['Pitch', 'Usage %', 'Avg Velo', 'Avg Spin', 
                       'Whiff Rate', 'H. Move (in)', 'V. Move (in)']
    display['Usage %'] = display['Usage %'].round(1)
    display['Avg Velo'] = display['Avg Velo'].round(1)
    display['Avg Spin'] = display['Avg Spin'].round(0)
    display['Whiff Rate'] = display['Whiff Rate'].apply(lambda x: f"{x:.1%}")
    display['H. Move (in)'] = display['H. Move (in)'].round(1)
    display['V. Move (in)'] = display['V. Move (in)'].round(1)
    display = display.sort_values('Usage %', ascending=False)
    st.dataframe(display, hide_index=True, use_container_width=True)
    

# Lineup Quality page
elif page == "Lineup Quality":
    st.title("Lineup Quality")
    st.markdown("""
    A pitcher does not face a team. He faces nine individuals. This page scores every 
    Opening Day lineup using real 2025 batting data — wOBA, xwOBA, hard hit rate, 
    barrel rate, strikeout rate, and walk rate.
    
    The higher the xwOBA, the more damage this lineup is capable of doing on any given night.
    """)
    st.markdown("---")

    lineup_plot = lineups[['team', 'avg_xwOBA', 'avg_wRC+', 
                            'avg_HardHit%', 'avg_Barrel%', 
                            'avg_K%', 'avg_BB%']].copy()
    lineup_plot = lineup_plot.sort_values('avg_xwOBA', ascending=True)

    nl_teams = [
        'New York Mets', 'Philadelphia Phillies', 'Atlanta Braves', 
        'Miami Marlins', 'Washington Nationals', 'Chicago Cubs', 
        'Milwaukee Brewers', 'Cincinnati Reds', 'Pittsburgh Pirates', 
        'St. Louis Cardinals', 'Los Angeles Dodgers', 'San Diego Padres', 
        'Arizona Diamondbacks', 'Colorado Rockies', 'San Francisco Giants'
    ]
    lineup_plot['color'] = lineup_plot['team'].apply(
        lambda x: '#f97316' if x in nl_teams else '#3b82f6'
    )

    fig = go.Figure(go.Bar(
        x=lineup_plot['avg_xwOBA'],
        y=lineup_plot['team'],
        orientation='h',
        marker=dict(
            color=lineup_plot['color'],
            opacity=0.85,
            line=dict(width=0.5, color='white')
        ),
        hovertemplate='<b>%{y}</b><br>xwOBA: %{x:.3f}<extra></extra>'
    ))

    fig.add_vline(
        x=0.315,
        line_dash='dash',
        line_color='#94a3b8',
        line_width=1.5,
        annotation_text='League Avg (.315)',
        annotation_font=dict(color='white', size=11),
        annotation_position='top right'
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        xaxis=dict(
            title='Average Lineup xwOBA',
            gridcolor='#334155',
            range=[0.22, 0.37]
        ),
        yaxis=dict(
            gridcolor='#334155',
            tickfont=dict(size=11)
        ),
        height=750,
        margin=dict(l=200, r=40, t=40, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)

    # League toggle
    st.markdown("---")
    st.markdown("### Full Lineup Scores")

    league_filter = st.radio("Filter by league", ["All", "AL", "NL"], horizontal=True)

    display = lineup_plot[['team', 'avg_xwOBA', 'avg_wRC+', 
                            'avg_HardHit%', 'avg_Barrel%', 
                            'avg_K%', 'avg_BB%']].copy()
    display.columns = ['Team', 'xwOBA', 'wRC+', 'HardHit%', 'Barrel%', 'K%', 'BB%']
    display = display.sort_values('xwOBA', ascending=False)

    if league_filter == "NL":
        display = display[display['Team'].isin(nl_teams)]
    elif league_filter == "AL":
        display = display[~display['Team'].isin(nl_teams)]

    display['xwOBA'] = display['xwOBA'].round(3)
    display['wRC+'] = display['wRC+'].round(1)
    display['HardHit%'] = display['HardHit%'].round(1)
    display['Barrel%'] = display['Barrel%'].round(1)
    display['K%'] = display['K%'].round(3)
    display['BB%'] = display['BB%'].round(3)

    st.dataframe(display, hide_index=True, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.markdown("Built by Ray Garza | Austin TX")
st.sidebar.markdown("[GitHub](#) | [LinkedIn](#)")